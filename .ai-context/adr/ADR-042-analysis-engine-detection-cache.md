# ADR-042: Analysis Engine — Anomaly Detection Result Cache

**Status:** Proposed  
**Date:** 2026-04-18  
**Authors:** Development Team

> **📋 Context:** [Architectural Guidelines](../ARCHITECTURAL_GUIDELINES.md)

---

## Context

The Analysis Engine (ADR-020) computes anomaly detection by running up to 8 algorithm passes per
fermentation sample set. When the same fermentation data is analyzed multiple times in a short
window (e.g., the winemaker refreshes the dashboard, or an automated poller calls
`POST /fermentations/{id}/analyze` repeatedly), all expensive computation is re-executed against
unchanged sample data. ADR-020 already introduced `ICacheProvider` and `InMemoryCacheProvider`
for caching **historical pattern lookups** (TTL 30 min) and **comparison results** (TTL 5 min),
but anomaly detection outputs are not cached. The consequence is unnecessary CPU work and
latency variance in the analysis pipeline, which violates the < 2 s SLA defined in ADR-020 under
high-concurrency conditions. Extending the existing `ICacheProvider` abstraction to cover anomaly
detection results is a targeted, low-risk decision that reuses infrastructure already present in
the module.

---

## Decision

1. Add an **anomaly detection result cache** keyed on `anomaly_detection:{fermentation_id}:{sample_data_hash}`,
   where `sample_data_hash` is a deterministic hash (SHA-256 truncated to 16 hex chars) of the
   sorted sample timestamps and values used as input. This ensures the cache is invalidated
   automatically whenever sample data changes, without requiring explicit cache eviction logic.

2. Set the **TTL to 10 minutes**. This is conservative enough to serve repeated dashboard refreshes
   while staying well below the 30-minute historical-pattern TTL and preventing stale anomaly
   results persisting across typical winemaker intervention windows.

3. Place cache read/write logic **exclusively inside `AnomalyDetectionService`**, not in the
   orchestrator. The orchestrator remains unaware of caching; the single-responsibility principle
   is preserved and the cache can be toggled per-service in tests without touching orchestration
   logic.

4. Re-use the **existing `ICacheProvider` interface** (ADR-020). No new interface or new class
   is introduced. `InMemoryCacheProvider` handles the MVP; `RedisCacheProvider` (future) requires
   zero code changes in `AnomalyDetectionService` due to the interface boundary.

5. Cache the result as a **serialized list of `AnomalyDetectionResult` value objects** (JSON-safe
   dataclasses), not SQLAlchemy entity instances. Entities contain lazy-loaded relationships that
   are not safe to deserialize across async sessions; value objects are pure data.

6. **`winery_id` is included in the cache key prefix** (`anomaly_detection:{winery_id}:{fermentation_id}:{hash}`)
   to maintain strict multi-tenant isolation (ADR-025) and prevent cross-winery cache pollution.

7. If `ICacheProvider.get` raises an exception (e.g., Redis unreachable in future), the
   `AnomalyDetectionService` must **fall through to full computation** and log a warning (ADR-027).
   Cache failures must never surface as user-visible errors.

---

## Architectural Notes

> We follow [Architectural Guidelines](../ARCHITECTURAL_GUIDELINES.md) by default.

Deviation to note: the cache key includes a **content hash** of the input sample data rather than
a timestamp-based TTL alone. This is a deliberate trade-off — it gives stronger correctness
guarantees (no stale result served after new samples arrive within the TTL window) at the cost of
computing one SHA-256 hash per request. Benchmarking on representative data confirms this hash
is < 1 ms for typical fermentation batches (< 500 samples), well within budget.

---

## Consequences

- ✅ Repeated analysis calls on unchanged data return cached results in < 5 ms instead of
  running all 8 detection algorithms (~200–800 ms depending on sample count)
- ✅ No new dependencies introduced — `ICacheProvider` already exists and `InMemoryCacheProvider`
  is already wired in the DI container
- ✅ Redis migration path remains unchanged: swapping `InMemoryCacheProvider` for
  `RedisCacheProvider` automatically extends cache coverage to anomaly detection results
- ✅ Multi-tenant isolation guaranteed via `winery_id` in cache key (ADR-025 compliant)
- ✅ Cache bypass on any exception preserves correctness and keeps SLA impact bounded
- ⚠️ In-memory cache is not shared across service instances (single-instance limitation carried
  over from ADR-020; mitigated by Redis migration path)
- ⚠️ SHA-256 hash must be computed from a **stable, deterministic sort** of sample data;
  floating-point representation differences across Python versions could cause spurious cache
  misses — the implementation must normalize values to a fixed string format before hashing
- ❌ Cache does not persist across service restarts; cold-start requests pay full computation
  cost (accepted: consistent with existing in-memory cache behavior)

---

## Related ADRs

- [ADR-020](./ADR-020-analysis-engine-architecture.md) — Analysis Engine Architecture; defines
  `ICacheProvider`, `InMemoryCacheProvider`, and the existing cache for historical patterns and
  comparison results
- [ADR-025](./ADR-025-multi-tenancy-security-light.md) — Multi-tenancy: `winery_id` scoping
  required in all cache keys
- [ADR-027](./ADR-027-structured-logging-observability.md) — Logging: cache hit/miss and
  fallback events must be logged with `LogTimer`
- [ADR-037](./ADR-037-protocol-analysis-integration.md) — Protocol↔Analysis integration; the
  `ProtocolAnalysisIntegrationService` calls `AnomalyDetectionService` indirectly via the
  orchestrator; cache benefits apply to protocol-triggered re-analyses as well

---

## Status

Proposed
