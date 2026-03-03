# Analysis Engine ADRs - Implementation Roadmap

**Status**: ✅ ADR-020 fully implemented | 🔄 ADR-037 in progress  
**Related to**: Protocol Engine (ADR-035, ADR-036, ADR-037, ADR-038, ADR-039)

---

## 🎯 Analysis Service ADRs (Sorted by Implementation Order)

### **PRIMARY ADR**

#### **ADR-020: Analysis Engine Architecture & Anomaly Detection Algorithms**
**Status**: ✅ Approved, ✅ **Fully Implemented** (March 1, 2026)  
**File**: `.ai-context/adr/ADR-020-analysis-engine-architecture.md` (1046 lines)

**What it defines**:
- ✅ Domain entities (Analysis, Anomaly, Recommendation, RecommendationTemplate)
- ✅ Value objects (ConfidenceLevel, ComparisonResult, DeviationScore)
- ✅ Enums (AnomalyType x8, SeverityLevel, AnalysisStatus, RecommendationCategory x11)
- ✅ Repository interfaces + implementations
- ✅ **Service layer** (4 services: Orchestrator, Comparison, AnomalyDetection, Recommendation)
- ✅ **API layer** (analysis_router, recommendation_router, schemas, error_handlers, main.py port 8001)
- ✅ **108 unit tests passing**
  
**Key Concepts Defined**:

1. **Anomaly Types** (8 types, priority-ranked):
   - 🔴 Critical (Priority 1): Stuck Fermentation, Temperature Out of Range, Volatile Acidity
   - 🟠 Warning (Priority 2): Density Drop Too Fast, H2S Risk, Temperature Suboptimal
   - 🟡 Info (Priority 3): Unusual Duration, Atypical Pattern

2. **Detection Thresholds** (validated by Susana Rodriguez Vasquez - 20-year winemaker):
   - Stuck fermentation: No density change for 0.5-1 day (threshold: < 1.0 points)
   - Temperature critical: Reds 75-90°F, Whites 53-62°F
   - Volatile acidity: High acetic acid levels (chemical test)
   - Density drop too fast: > 15% in 24 hours
   - H2S risk: Low nitrogen + low temperature
   - Duration unusual: Outside percentile 10-90 vs historical

3. **Confidence Levels**:
   - LOW: < 5 historical samples
   - MEDIUM: 5-15 historical samples
   - HIGH: 15-30 historical samples
   - VERY_HIGH: > 30 historical samples

4. **Severity Levels**:
   - CRITICAL: Vino no vendible (High Volatile Acidity, Stuck Fermentation, etc.)
   - HIGH: Daño severo (Temperature out of range)
   - MEDIUM: Afecta calidad (Density drop too fast, H2S)
   - LOW: Early warning or informational

---

### **SUPPORTING ADRs**

#### **ADR-034: Historical Data Service Refactoring**
**Status**: ✅ Completed  
**File**: `.ai-context/adr/ADR-034-historical-data-service-refactoring.md`

**What it provides**:
- ✅ PatternAnalysisService - extracts patterns from historical fermentations
- ✅ Filters by: varietal, fruit_origin, winery, date range
- ✅ Returns statistical metrics: mean duration, density trajectory, temperature range
- ✅ **BLOCKING DEPENDENCY for Analysis Service** - needed to find similar fermentations

**Key Methods Available**:
```python
async def extract_patterns(
    winery_id: UUID,
    varietal: str,
    fruit_origin: str,
    date_from: datetime,
    date_to: datetime
) -> FermentationPatterns
```

**Returns**:
- Historical samples count
- Similarity score
- Statistical metrics (mean, std dev, percentiles)
- Comparison criteria met

---

#### **ADR-032: Historical Data API Layer**
**Status**: ✅ Completed  
**File**: `.ai-context/adr/ADR-032-historical-data-api-layer.md`

**What it provides**:
- ✅ Endpoint: `GET /api/v1/fermentations/patterns/extract`
- ✅ Query parameters: varietal, fruit_origin, winery_id
- ✅ Returns historical fermentation patterns in JSON
- ✅ **Used by Analysis Service** to get comparison data

**Usage in Analysis Flow**:
```
Fermentation being analyzed
    ↓
Call PatternAnalysisService to get similar historical fermentations
    ↓
Use comparison_result for anomaly detection
    ↓
Boost confidence based on historical_samples_count
```

---

#### **ADR-029: Data Source Field**
**Status**: ✅ Completed  
**File**: `.ai-context/adr/ADR-029-data-source-field.md`

**What it provides**:
- ✅ `data_source` field on fermentation data: SYSTEM / HISTORICAL / MIGRATED
- ✅ Allows filtering: exclude migrated/historical when computing confidence
- ✅ **Used by Analysis Service** for data quality filtering

**Impact on Analysis**:
```
When comparing fermentations:
- SYSTEM fermentations: Full weight in similarity calculation
- HISTORICAL fermentations: Can be included or excluded per policy
- MIGRATED fermentations: May have data quality issues
```

---

#### **ADR-025: Multi-Tenancy & Security**
**Status**: ✅ Completed  
**File**: `.ai-context/adr/ADR-025-multi-tenancy-security.md`

**What it requires**:
- ✅ Strict `winery_id` isolation on all queries
- ✅ Analysis can only compare fermentations within same winery
- ✅ Authenticated user context required

**Impact on Analysis Service**:
```
async def calculate_anomalies(
    fermentation_id: UUID,
    winery_id: UUID  # MUST validate access
) -> List[Anomaly]:
    # Can only query:
    # - Current fermentation (winery_id match)
    # - Historical fermentations (same winery_id only)
```

---

## 📋 Service Layer Structure (NOT YET BUILT)

Based on ADR-020, the Analysis Service layer should have:

```python
# Interfaces (needed)
├── AnalysisOrchestratorServiceInterface
│   └── analyze(fermentation_id, winery_id) -> Analysis
│
├── ComparisonServiceInterface  
│   └── find_similar_fermentations(fermentation_id) -> List[Fermentation]
│
├── AnomalyDetectionServiceInterface
│   └── detect_anomalies(fermentation, similar_fermentations) -> List[Anomaly]
│
├── RecommendationServiceInterface
│   └── generate_recommendations(anomalies) -> List[Recommendation]
│
├── RuleConfigServiceInterface
│   └── get_detection_rules() -> DetectionRules
│
└── CacheProviderInterface (in-memory, future: Redis)
    └── cache(key, value) / get(key) / invalidate(key)


# Implementations (needed)
├── AnalysisOrchestratorService
│   ├── Calls ComparisonService
│   ├── Calls AnomalyDetectionService
│   ├── Calls RecommendationService
│   ├── Persists Analysis + Anomalies + Recommendations
│   └── Returns complete Analysis
│
├── ComparisonService
│   ├── Calls PatternAnalysisService (from ADR-034)
│   ├── Filters by winery_id + varietal
│   └── Returns ranked list of similar fermentations
│
├── AnomalyDetectionService
│   ├── Runs 8 anomaly detection algorithms
│   ├── Each checks one anomaly type
│   ├── Uses thresholds from RuleConfigService
│   └── Returns anomalies with severity levels
│
├── RecommendationService
│   ├── Maps anomalies to recommendation templates
│   ├── Ranks by effectiveness/urgency
│   ├── Loads templates from database
│   └── Returns prioritized recommendations
│
├── RuleConfigService
│   ├── Loads detection rules from YAML
│   ├── Provides thresholds: stuck fermentation, temperature, etc.
│   ├── Supports multi-varietal config (Pinot vs Cabernet different thresholds)
│   └── Can be updated without redeploy (in-memory reload)
│
└── InMemoryCacheProvider
    ├── Caches historical patterns (expires after 1 hour)
    ├── Caches recommendation templates
    └── Future: migrate to Redis without breaking code
```

---

## 🎯 What's NEEDED to Implement Analysis Service

### **Must Have (Blocking)**

1. ✅ **ADR-020** - Domain layer & thresholds - DONE
2. ✅ **ADR-034** - PatternAnalysisService to fetch historical data - DONE
3. ✅ **ADR-025** - Multi-tenancy rules - DONE
4. ❌ **Service Layer** - 4 services to build:
   - AnalysisOrchestratorService (orchestration)
   - ComparisonService (find similar fermentations)
   - AnomalyDetectionService (detect anomalies)
   - RecommendationService (generate recommendations)

### **Nice to Have (Non-Blocking)**

5. 🔄 **ADR-037** - Protocol-Analysis Integration (**In Progress** - started March 1, 2026)
6. ⏳ **ADR-040** - Notifications (can add later)
7. ⏳ **API Endpoints** (can add after service complete)

---

## 📈 Implementation Roadmap

### **Phase 1: Core Service Layer (1-2 weeks)**
```
Week 1:
├─ AnalysisOrchestratorService
│  └─ Orchestrates the analysis workflow
│
├─ ComparisonService
│  └─ Finds similar historical fermentations
│
└─ RuleConfigService
   └─ Loads detection thresholds

Week 2:
├─ AnomalyDetectionService
│  └─ Detects 8 anomaly types
│
├─ RecommendationService
│  └─ Generates recommendations
│
└─ InMemoryCacheProvider
   └─ Caches patterns & templates
```

### **Phase 2: Testing & Persistence (1 week)**
```
├─ 40+ unit tests for each service
├─ Integration tests with real database
├─ Load testing (1000s of fermentations)
└─ AnalysisRepository integration
```

### **Phase 3: Integration (1 week - optional)**
```
├─ 🔄 ADR-037 (Protocol-Analysis integration) ← IN PROGRESS
├─ Add API endpoints
└─ End-to-end testing
```

---

## 🔑 Key Decisions from ADR-020

### **1. Hybrid Detection Algorithm**
```python
# NOT just statistical outliers
# Use BOTH:
# - Statistical: Density outside ±2σ
# - Rule-based: Temperature > 32°C
# - Heuristic: Stuck (no change 24h)
```

### **2. Confidence is Transparent**
```python
# Show to winemaker:
# "Analysis confidence: HIGH (based on 22 similar fermentations)"
# Lower confidence = more cautious recommendations
```

### **3. Minimize False Positives**
```python
# Better to miss something (false negative) 
# than annoy winemaker with false alerts
# But for CRITICAL anomalies, err on side of caution
```

### **4. Human Decisions Always**
```python
# System recommends, winemaker decides
# Example: System says "add nutrients"
#         Winemaker verifies with microscope first
```

### **5. Varietal-Specific Thresholds**
```python
# Pinot Noir temperature: 53-62°F (whites/rosés)
# Cabernet temperature: 75-90°F (reds)
# Rules loaded from YAML, not hardcoded
```

---

## ❓ Summary for Building Analysis Service

**You have**:
- ✅ Domain entities & repositories (ADR-020)
- ✅ Historical data service (ADR-034)
- ✅ Historical data API (ADR-032)
- ✅ Multi-tenancy rules (ADR-025)
- ✅ Detection thresholds validated by expert winemaker

**Fully implemented (2026-03-01)**:
- ✅ Domain entities & repositories (ADR-020)
- ✅ AnalysisOrchestratorService
- ✅ ComparisonService
- ✅ AnomalyDetectionService
- ✅ RecommendationService
- ✅ Historical data service (ADR-034)
- ✅ Historical data API (ADR-032)
- ✅ Multi-tenancy rules (ADR-025)
- ✅ Unit tests (108 tests passing)

**In progress (Phase 4)**:
- 🔄 Protocol-Analysis Integration (ADR-037) ← started March 1, 2026

**Not yet started**:
- Notification system (ADR-040)

---

## 🚀 Next Steps

ADR-037 implementation underway. Building `ProtocolAnalysisIntegrationService` with confidence boost formula:
`adjusted_confidence = base_confidence × (0.5 + compliance_score / 100)`
