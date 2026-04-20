# Analysis Engine Refactor: AnomalyDetectionService

## Context read (per skill hierarchy)

**NIVEL 1 (project-context.md):** Analysis Engine is ✅ COMPLETE — 185 tests passing, 5 services + API layer + ADR-037 implemented. The system has 1,416 total passing tests. `project-context.md` also shows ADR-039/040 Alert Service is the next unfinished work.

**NIVEL 1 (ARCHITECTURAL_GUIDELINES.md):** SRP is mandatory, god objects are explicitly listed as an anti-pattern. Dependency direction must always point inward toward domain. SOLID checklist must pass before submitting.

**NIVEL 1 (collaboration-principles.md):** "No me des siempre la razón." I'm expected to push back, not validate. Noted.

**NIVEL 2 (module-context.md):** The service layer already has 5 separate services:
- `AnalysisOrchestratorService` — pipeline coordinator
- `ComparisonService` — historical baseline comparison
- `AnomalyDetectionService` — threshold-based anomaly detection
- `RecommendationService` — template-driven recommendation generation
- `ProtocolAnalysisIntegrationService` — ADR-037 confidence boost + advisory generation

**NIVEL 4 (actual code):** Read all five services.

---

## Direct answer to the question: "What should we do?"

**Stop. Before proposing a refactor, let's be precise about what problem actually exists — because the premise in the question is partially wrong.**

### What the question claims: `AnomalyDetectionService` is doing anomaly detection AND recommendation generation AND protocol integration all in one class.

### What the code actually shows:

```
anomaly_detection_service.py  — 444 lines — ONLY anomaly detection
recommendation_service.py     — 299 lines — ONLY recommendation generation  
protocol_integration_service.py — 383 lines — ONLY protocol integration
```

**The three responsibilities are already split into three separate classes.** `AnomalyDetectionService` does not touch recommendations or protocol integration. `RecommendationService` doesn't call `ProtocolAnalysisIntegrationService`. These are already separated.

The actual orchestration logic that *coordinates* all three lives in `AnalysisOrchestratorService.execute_analysis()` — and that's architecturally correct. The Orchestrator's job is exactly that: call the sub-services in sequence. That's not a god object; that's the pipeline coordinator.

---

## So is there actually a refactoring problem?

**Yes — but it's not the one described.** After reading the code carefully, here are the real issues:

### Issue 1 — `AnomalyDetectionService` has weak cohesion across its 8 detect_* methods

The 8 methods fall into two distinct groups with different data dependencies:

| Group | Methods | Data required |
|-------|---------|---------------|
| **Real-time physical signals** | `detect_stuck_fermentation`, `detect_temperature_critical`, `detect_temperature_suboptimal`, `detect_density_drop_too_fast`, `detect_hydrogen_sulfide_risk`, `detect_volatile_acidity` | Current readings + thresholds |
| **Historical comparisons** | `detect_unusual_duration`, `detect_atypical_pattern` | Historical baseline data |

These two groups have different reasons to change: the first group changes when winemaker thresholds change, the second group changes when the statistical comparison model changes. That's two reasons to change — a mild SRP violation. Whether this warrants a split depends on how much the historical comparison side will grow (if `ComparisonService` feeds more statistical signals into anomaly detection, the case for splitting strengthens).

**Current verdict:** The class at 444 lines is large but cohesive enough given current scope. Monitor it; split when historical anomaly detection grows.

### Issue 2 — `AnalysisOrchestratorService` has a direct `session.add(advisory)` call that bypasses the repository layer

In `execute_analysis()` at line 179:
```python
for advisory in advisories:
    self.session.add(advisory)  # ← direct ORM in service layer
```

This is an architecture violation. The service layer must not touch SQLAlchemy sessions directly — that belongs in a repository. The `ProtocolAdvisoryRepository` already exists. The Orchestrator should call `advisory_repo.save(advisory)` not `session.add(advisory)`.

**This is the real problem worth fixing.**

### Issue 3 — `ProtocolAnalysisIntegrationService` returns advisory-as-unsaved-entity, pushing persistence responsibility to the caller

The service is designed as "returns entity, caller persists it" (documented in the docstring). This breaks the boundary between domain logic and persistence — advisory generation and advisory persistence should be decoupled via an interface, not via a convention that the caller must remember to call `session.add`.

### Issue 4 — `_calculate_confidence` is a static method on `AnalysisOrchestratorService` but conceptually belongs to `ConfidenceLevel`

The confidence calculation logic at the bottom of `execute_analysis()` (lines 254–319) computes weights and thresholds that are business rules, not orchestration logic. A static method on the Orchestrator is the right call for now, but if confidence calculation grows (ADR-037 adds the protocol boost on top), this should move to a dedicated `ConfidenceCalculationService` or become a factory method on `ConfidenceLevel`.

---

## What you should actually do (prioritized)

### 1. Fix the architecture violation immediately (medium effort, high value)

Move the `session.add(advisory)` calls in `AnalysisOrchestratorService` into `ProtocolAdvisoryRepository`. The repository already exists — just add a `save_many(advisories)` or `save(advisory)` method and inject the repository into the Orchestrator via its interface.

```python
# In AnalysisOrchestratorService.__init__:
def __init__(
    self,
    session: AsyncSession,
    threshold_config: ThresholdConfigService,
    advisory_repo: IProtocolAdvisoryRepository,  # add this
) -> None:
    ...
    self.advisory_repo = advisory_repo

# In execute_analysis(), replace:
for advisory in advisories:
    self.session.add(advisory)  # ← wrong

# With:
await self.advisory_repo.save_many(advisories)  # ← correct
```

**Why this matters:** Right now you can't unit-test the Orchestrator's advisory-persistence path without a real SQLAlchemy session. This is exactly what the skill's TDD workflow requires.

### 2. Do NOT split `AnomalyDetectionService` right now

The question implies this is urgent. It isn't. The class has 8 focused methods, a single constructor, a single `detect_all_anomalies()` entry point, and all methods share `ThresholdConfigService`. There is no coupling to recommendation logic or protocol logic. The existing separation is correct.

Splitting it prematurely into `PhysicalSignalAnomalyDetector` + `HistoricalPatternAnomalyDetector` would add two interfaces, two injectables in the Orchestrator, and two sets of tests — for a problem that doesn't exist today.

**Refactor when:** (a) historical anomaly detection grows to require its own repository queries, or (b) the class exceeds ~600 lines with methods that have different collaborators.

### 3. Consider extracting `ConfidenceCalculationService` when ADR-040 (Alert Service) lands

The confidence formula will be consumed by both the analysis pipeline and the alert service. At that point, duplicating the formula is a bigger risk than the current static method. Extract it then, not now — YAGNI applies until there's a second caller.

### 4. No changes needed to `RecommendationService` or `ProtocolAnalysisIntegrationService`

Both are clean, single-purpose, and appropriately sized. `ProtocolAnalysisIntegrationService` is correctly stateless for Flow 1 (confidence boost) and returns unsaved entities for Flow 2 — the persistence concern is a caller issue (see Issue 2 above), not a service design issue.

---

## Summary

| Finding | Severity | Action |
|---------|----------|--------|
| `AnomalyDetectionService` has 3 mixed concerns | ❌ Premise is wrong | No action — the three concerns are already in 3 classes |
| `session.add(advisory)` in Orchestrator bypasses repository | ⚠️ Architecture violation | Fix: inject `IProtocolAdvisoryRepository`, move persistence there |
| `AnomalyDetectionService` has 2 cohesion groups | ℹ️ Minor SRP concern | Monitor; split only when historical detection grows its own collaborators |
| `_calculate_confidence` on Orchestrator | ℹ️ Anticipatory concern | Extract to `ConfidenceCalculationService` when ADR-040 creates a second caller |
| `RecommendationService`, `ProtocolAnalysisIntegrationService` | ✅ Clean | No changes needed |

The single concrete action with immediate architectural payoff is fixing the `session.add()` call in the Orchestrator. Everything else is either already correct or should wait for a real forcing function.
