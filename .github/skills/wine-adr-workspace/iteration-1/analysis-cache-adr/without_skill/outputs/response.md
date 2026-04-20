# ADR-042: Analysis Engine Caching Layer for Anomaly Detection

**Status:** Proposed  
**Date:** 2026-04-18  
**Authors:** Development Team

> **📋 Context Files:** Para decisiones arquitectónicas, revisar:
> - [Architectural Guidelines](../../../../../../../.ai-context/ARCHITECTURAL_GUIDELINES.md) - Principios de diseño
> - [ADR-020 - Analysis Engine Architecture](../../../../../../../.ai-context/adr/ADR-020-analysis-engine-architecture.md) - Cache interface already defined
> - [ADR-034 - Historical Data Service Refactoring](../../../../../../../.ai-context/adr/ADR-034-historical-data-service-refactoring.md) - PatternAnalysisService (cache consumer)

---

## Context

The Analysis Engine (ADR-020) performs anomaly detection by comparing the current fermentation's samples against historical fermentation patterns retrieved via `PatternAnalysisService`. This operation is expensive: it queries historical data, calculates statistical baselines, and runs a hybrid rule + statistical detection pipeline for every call to `POST /fermentations/{id}/analyze`.

When the same fermentation sample data is submitted multiple times within a short window — e.g. the user refreshes the UI, a polling client re-requests, or event-driven phase 2 triggers duplicate events — the full analysis is recomputed from scratch even though the underlying input (sample set + historical patterns) has not changed. This wastes CPU, database I/O, and inflates response times beyond the < 2 second target.

ADR-020 already specified and partially designed an `ICacheProvider` interface with both `InMemoryCacheProvider` and a placeholder `RedisCacheProvider`. However, that ADR focused on caching *historical pattern queries* (TTL 30 min) and *comparison results* (TTL 5 min). It did not address caching the *full anomaly detection result* for a specific set of sample data, nor define the cache key strategy, invalidation triggers, or observability requirements for that layer.

This ADR formalizes the caching layer specifically for the anomaly detection computation to prevent redundant recomputation on unchanged sample data.

---

## Decision

1. **Cache at the analysis orchestration boundary**: The `AnalysisOrchestratorService` will check the cache before delegating to `ComparisonService` → `AnomalyDetectionService`. A cache hit short-circuits the full pipeline and returns the persisted `Analysis` result directly.

2. **Cache key is derived from fermentation ID + sample fingerprint**: The key encodes `winery_id`, `fermentation_id`, and a deterministic hash of the sample data snapshot (sorted sample IDs + their timestamps). This ensures the cache is invalidated naturally when new samples arrive.
   ```
   analysis:winery_{winery_id}:fermentation_{fermentation_id}:samples_{sha256_of_sorted_sample_ids}
   ```

3. **TTL set to 10 minutes**: Short enough that stale anomaly results do not persist long after new samples arrive; long enough to absorb burst re-analysis requests within a typical UI interaction window.

4. **Use the existing `ICacheProvider` interface (ADR-020)**: No new abstraction is introduced. `InMemoryCacheProvider` is used for the MVP (single-instance). Migration to `RedisCacheProvider` requires only a dependency injection swap.

5. **Cache stores a reference to the persisted `Analysis.id`, not the full object**: The cached value is the integer primary key. On a cache hit, the orchestrator loads the full `Analysis` aggregate from the database via repository. This avoids serializing complex nested objects into the cache and keeps cache entries small.

6. **Cache is invalidated explicitly on new sample ingestion**: Whenever a new `Sample` is added to a fermentation, the `SampleService` (or relevant service in the fermentation module) calls `cache_provider.delete(pattern=f"analysis:winery_{winery_id}:fermentation_{fermentation_id}:*")` via the `clear_pattern` method already defined in `ICacheProvider`.

7. **Cache is bypassed on explicit force-reanalysis**: The `POST /fermentations/{id}/analyze` endpoint accepts an optional query parameter `?force=true` that skips cache lookup and always runs the full pipeline, persisting a new `Analysis` record.

8. **Cache misses are logged at DEBUG level; cache hits at INFO level with analysis ID**: This enables observability without verbose noise in steady state. Cache hit rate will be tracked via structured logging (ADR-027).

---

## Implementation Notes

```
analysis-engine/
└── service_component/
    ├── interfaces/
    │   └── cache_provider_interface.py        # Existing — ICacheProvider (no change)
    └── services/
        ├── analysis_orchestrator_service.py   # MODIFIED — add cache check/set logic
        ├── in_memory_cache_provider.py        # Existing — supports clear_pattern (verify/add)
        └── sample_fingerprint_service.py      # NEW — computes sha256 of sorted sample IDs

fermentation/                                  # (or samples module)
└── service_component/
    └── services/
        └── sample_service.py                  # MODIFIED — call cache invalidation on add
```

**Key responsibilities:**

- **`SampleFingerprintService`**: Takes a `List[Sample]` (or just their IDs + `recorded_at` timestamps), sorts them deterministically, and returns a stable SHA-256 hex digest. This is the variable portion of the cache key.

- **`AnalysisOrchestratorService.run_analysis(fermentation_id, winery_id, force=False)`**:
  1. Load current samples for the fermentation.
  2. Compute fingerprint via `SampleFingerprintService`.
  3. Build cache key.
  4. If `not force`: check `ICacheProvider.get(key)`.
     - **Hit**: load `Analysis` by ID from repository, return immediately.
     - **Miss**: run full pipeline, persist `Analysis`, store `analysis.id` in cache with TTL.
  5. If `force`: skip step 4 lookup, always run pipeline, store new result.

- **`InMemoryCacheProvider.clear_pattern(pattern: str)`**: Must support simple wildcard suffix matching (e.g., `"analysis:winery_1:fermentation_42:*"`). If not already implemented, add this to the existing class.

---

## Architectural Considerations

- **Cache coherence (single-instance only)**: `InMemoryCacheProvider` is process-local. Two running instances will have independent caches. This is acceptable for the MVP (single-instance deployment). When scaling to multi-instance, the injection of `RedisCacheProvider` addresses this automatically per ADR-020.

- **Cache-aside pattern**: Chosen over write-through because analysis is compute-on-demand, not a side effect of writes. The cache is populated lazily on first analysis request.

- **Storing ID vs full object**: Storing the full `Analysis` aggregate (with nested `Anomaly` and `Recommendation` lists) in cache would require JSON serialization with custom encoders and inflate memory usage. Storing the `int` primary key keeps cache entries at ~8 bytes each and avoids deserialization bugs at the cost of one additional DB read on cache hit — acceptable given the read is a simple PK lookup.

- **Pattern invalidation cost**: `clear_pattern` with in-memory cache is O(n) over all keys. For the expected scale (tens to hundreds of fermentations per winery), this is negligible.

---

## Consequences

- ✅ Eliminates redundant anomaly detection computation for repeated requests on unchanged sample data.
- ✅ Reduces database load from `PatternAnalysisService` queries on cache hits.
- ✅ Keeps the `< 2 second` performance target achievable under burst conditions.
- ✅ Zero new abstractions — builds on `ICacheProvider` already defined in ADR-020.
- ✅ `?force=true` escape hatch preserves full pipeline access without cache workarounds.
- ✅ Explicit invalidation on new sample ingestion ensures correctness: stale results are never served after data changes.
- ⚠️ Adds a cross-module coupling: the sample/fermentation module must now call into the cache layer on sample writes. This should be done via an event or a dedicated interface to avoid tight coupling.
- ⚠️ `InMemoryCacheProvider.clear_pattern` may not yet be fully implemented — must be verified and completed before this ADR is implemented.
- ❌ Cache does not survive process restarts (in-memory). After a restart, the first analysis request per fermentation will always miss and run the full pipeline. Acceptable for MVP.

---

## TDD Plan

- **`SampleFingerprintService.compute(samples)`** → same fingerprint for same set regardless of input order
- **`SampleFingerprintService.compute(samples)`** → different fingerprint when a sample is added
- **`AnalysisOrchestratorService.run_analysis` (cache miss)** → calls full pipeline, stores result ID in cache
- **`AnalysisOrchestratorService.run_analysis` (cache hit)** → does NOT call `AnomalyDetectionService`, returns existing Analysis
- **`AnalysisOrchestratorService.run_analysis(force=True)`** → bypasses cache, always runs pipeline
- **`SampleService.add_sample`** → calls `cache_provider.clear_pattern(...)` with correct winery + fermentation scope
- **`InMemoryCacheProvider.clear_pattern`** → removes all keys matching prefix pattern, leaves others intact
- **Cache key format** → includes `winery_id`, `fermentation_id`, and fingerprint (multi-tenancy isolation)

---

## Quick Reference

- Cache key: `analysis:winery_{winery_id}:fermentation_{fermentation_id}:samples_{fingerprint}`
- Fingerprint: SHA-256 of sorted sample IDs + timestamps
- TTL: 10 minutes
- Cache stores: `Analysis.id` (int), not the full object
- Hit path: load Analysis by PK from DB → return
- Invalidation: explicit on new sample added (`clear_pattern`)
- Override: `?force=true` bypasses cache entirely
- Provider: `InMemoryCacheProvider` (MVP) → `RedisCacheProvider` (multi-instance, no logic change)
- Interface: existing `ICacheProvider` from ADR-020 — no new abstraction needed

---

## API Examples

```python
# Orchestrator - simplified cache logic
async def run_analysis(
    self,
    fermentation_id: int,
    winery_id: int,
    force: bool = False,
) -> Analysis:
    samples = await self._fermentation_repo.get_samples(fermentation_id, winery_id)
    fingerprint = self._fingerprint_service.compute(samples)
    cache_key = f"analysis:winery_{winery_id}:fermentation_{fermentation_id}:samples_{fingerprint}"

    if not force:
        cached_id = await self._cache.get(cache_key)
        if cached_id is not None:
            logger.info("analysis_cache_hit", analysis_id=cached_id, fermentation_id=fermentation_id)
            return await self._analysis_repo.get_by_id(cached_id, winery_id)

    logger.debug("analysis_cache_miss", fermentation_id=fermentation_id)
    analysis = await self._run_full_pipeline(fermentation_id, winery_id, samples)
    await self._cache.set(cache_key, analysis.id, ttl_seconds=600)
    return analysis


# Sample service - invalidation on new sample
async def add_sample(self, fermentation_id: int, winery_id: int, data: SampleCreate) -> Sample:
    sample = await self._sample_repo.create(fermentation_id, winery_id, data)
    pattern = f"analysis:winery_{winery_id}:fermentation_{fermentation_id}:*"
    await self._cache.clear_pattern(pattern)
    return sample
```

---

## Acceptance Criteria

- [ ] Repeated calls to `POST /fermentations/{id}/analyze` with unchanged sample data return the same `Analysis` record without re-running detection.
- [ ] Adding a new sample invalidates the cache; the next analysis call runs the full pipeline and returns a new `Analysis` record.
- [ ] `?force=true` always runs the full pipeline and persists a new `Analysis` record, even on a cache hit.
- [ ] Cache keys include `winery_id` — analysis cache from winery A cannot be accessed by winery B.
- [ ] Response time for a cache hit is < 200ms (DB PK lookup only).
- [ ] All existing analysis engine tests continue to pass.
- [ ] New unit tests cover: fingerprint stability, cache hit short-circuit, invalidation on sample add, force bypass.

---

## Status

Proposed
