# ADR Task: Analysis Engine Caching Layer

## Finding: ADR-042 Already Exists

**Before writing a new ADR, the skill requires checking ADR-INDEX.md for existing related ADRs.**

Upon reading the index and the file itself, **ADR-042 already fully covers this decision.**

---

## ADR-042: Analysis Engine — Anomaly Detection Result Cache

**File:** `.ai-context/adr/ADR-042-analysis-engine-detection-cache.md`  
**Status:** Proposed  
**Date:** 2026-04-18  
**Next ADR number if a new one were needed:** ADR-044

---

### Summary of ADR-042

ADR-042 addresses exactly the requested task: adding a caching layer to the analysis engine so anomaly detection is not re-run on unchanged sample data.

**Key decisions already recorded:**

1. **Cache key:** `anomaly_detection:{winery_id}:{fermentation_id}:{sample_data_hash}` — where the hash is SHA-256 (16-hex-char truncation) of sorted sample timestamps + values. Ensures automatic invalidation on data change without explicit eviction.

2. **TTL: 10 minutes** — conservative, serves repeated dashboard refreshes while staying below the 30-min historical-pattern TTL from ADR-020.

3. **Placement: `AnomalyDetectionService` only** — the orchestrator stays unaware of caching; SRP preserved.

4. **Re-uses `ICacheProvider` interface** (ADR-020) — no new abstractions. `InMemoryCacheProvider` for MVP; Redis migration requires zero changes to service code.

5. **Cache payload: serialized `AnomalyDetectionResult` value objects** (JSON-safe dataclasses, not SQLAlchemy entities) — avoids lazy-load session hazards.

6. **`winery_id` in key prefix** — ADR-025 multi-tenant isolation enforced.

7. **Fail-open on cache errors** — exceptions fall through to full computation + ADR-027 warning log. Cache failures never surface to users.

**Consequences recorded:**
- ✅ Repeated calls on unchanged data: < 5 ms vs 200–800 ms
- ✅ No new dependencies
- ✅ Redis migration path intact
- ✅ Multi-tenant isolation guaranteed
- ⚠️ In-memory cache not shared across service instances
- ⚠️ Hash must use stable deterministic sort + fixed string normalization
- ❌ Cache lost on restart (accepted)

**Related ADRs cross-referenced:** ADR-020, ADR-025, ADR-027, ADR-037

---

## Action Taken

No new ADR was created — **duplication is explicitly prohibited by the skill** ("Check if an ADR already covers this decision — link to it instead of duplicating").

The existing ADR-042 is complete and well-formed. The recommended action is:

> **Review ADR-042** (`.ai-context/adr/ADR-042-analysis-engine-detection-cache.md`) and confirm or accept it. Use `wine-backend-dev` skill when ready to implement.

---

## ADR-INDEX.md Status

ADR-042 is already listed in the index:

| ADR | Title | Status | Date | Impact |
|-----|-------|--------|------|--------|
| **ADR-042** | Analysis Engine — Anomaly Detection Result Cache | Proposed | 2026-04-18 | Medium |

No index update required.

---

## Next ADR Number

The last ADR in the index is **ADR-043** (FermentationNote Entity Design, 2026-04-19).  
Next available number: **ADR-044**.
