# Refactoring AnomalyDetectionService — With Skill

## What the context tells me

**project-context.md**: Analysis Engine is ✅ COMPLETE with 185–201 tests passing, full Clean Architecture stack.

**module-context.md**: The service layer already has **5 distinct services**: `AnalysisOrchestratorService`, `ComparisonService`, `AnomalyDetectionService`, `RecommendationService`, and `ProtocolAnalysisIntegrationService`.

---

## Direct answer: stop — the premise is wrong

You said `AnomalyDetectionService` is "doing anomaly detection AND recommendation generation AND protocol integration all in one class." I read the actual file. **That is not what's happening.**

The current `AnomalyDetectionService`:
- Has **one responsibility**: apply threshold rules to raw sensor data and return `Anomaly` objects
- Does **zero recommendation generation** — that lives in `RecommendationService`
- Does **zero protocol integration** — that lives in `ProtocolAnalysisIntegrationService`
- Has **zero imports** of recommendation or protocol concerns

The file is 444 lines but it's doing exactly one thing: 8 anomaly detection algorithms, each as its own method. That's not a SRP violation — that's 8 specialised variants of the same responsibility.

---

## What IS actually worth fixing

### OCP concern (not SRP)

Adding a new anomaly type requires editing the class. If you're actively adding types, extract each detector into a Strategy:

```python
# domain/interfaces/anomaly_detector_interface.py
class IAnomalyDetector(Protocol):
    async def detect(self, thresholds: VarietalThresholds, **context) -> Optional[Anomaly]:
        ...
```

`AnomalyDetectionService` becomes a thin orchestrator injected with the detector list. New anomaly type = new file, no edit to the coordinator.

**My recommendation: don't split unless you have a concrete upcoming requirement.** 444 cohesive lines is not a maintenance problem.

### Two real issues to fix now

1. **3 skipped tests on `detect_volatile_acidity`** — the method exists and looks complete. Either unskip the tests or remove the method. Skipped tests covering implemented code are a lie in your test suite.

2. **`session: AsyncSession` injected but never used** — remove it from the constructor or document why it's there. It inflates test setup complexity for no reason.

---

## Summary

| Concern | Verdict |
|---------|---------|
| SRP violation? | ❌ No — recommendations and protocol are already separate classes |
| Class too large? | ⚠️ Wide but cohesive. Not a problem. |
| OCP violation? | ⚠️ Yes — only matters if actively growing the type list |
| Recommended refactor | Strategy pattern if adding types. No change if stable. |
| Actual things to fix | Unskip 3 `detect_volatile_acidity` tests. Remove unused `session` injection. |
