# Refactoring AnomalyDetectionService: Separating Concerns

## Problem

The `AnomalyDetectionService` is violating the **Single Responsibility Principle (SRP)**. It currently handles three distinct responsibilities:

1. **Anomaly Detection** – identifying abnormal readings/events
2. **Recommendation Generation** – producing actionable suggestions based on anomalies
3. **Protocol Integration** – communicating with external protocols/systems

---

## Recommended Approach: Split into Focused Services

### 1. `AnomalyDetectionService` (keep, but slimmed down)

```python
class AnomalyDetectionService:
    def __init__(self, thresholds: dict):
        self.thresholds = thresholds

    def detect(self, sensor_data: dict) -> list[Anomaly]:
        anomalies = []
        # detection logic here...
        return anomalies
```

### 2. `RecommendationService` (new)

```python
class RecommendationService:
    def generate(self, anomalies: list[Anomaly]) -> list[Recommendation]:
        recommendations = []
        # recommendation logic here...
        return recommendations
```

### 3. `ProtocolIntegrationService` (extracted)

```python
class ProtocolIntegrationService:
    def __init__(self, client):
        self.client = client

    async def publish_anomaly(self, anomaly: Anomaly) -> None:
        await self.client.send(anomaly.to_payload())
```

### 4. Orchestrate with a Pipeline

```python
class AnalysisPipeline:
    def __init__(self, anomaly_service, recommendation_service, protocol_service):
        self.anomaly_service = anomaly_service
        self.recommendation_service = recommendation_service
        self.protocol_service = protocol_service

    async def run(self, sensor_data: dict) -> None:
        anomalies = self.anomaly_service.detect(sensor_data)
        if not anomalies:
            return
        recommendations = self.recommendation_service.generate(anomalies)
        for anomaly in anomalies:
            await self.protocol_service.publish_anomaly(anomaly)
```

---

## Benefits

| Concern | Before | After |
|---|---|---|
| **Testability** | Must mock everything together | Each service tested in isolation |
| **Maintainability** | One large class | Small, focused classes |
| **Extensibility** | Risky to add features | Swap or add one service safely |
