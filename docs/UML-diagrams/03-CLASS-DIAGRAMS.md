# Class Diagrams - Individual Components

> **Overview**: Class diagrams separated by module to maintain clarity and readability. Each component shows its entities, value objects, enums, and repository interfaces.

---

## 1. Fermentation Module - Class Diagram

```mermaid
classDiagram
    %% ====== BASE CLASSES ======
    class BaseEntity {
        int id
        datetime created_at
        datetime updated_at
        datetime deleted_at
    }
    
    %% ====== MAIN ENTITIES ======
    class Fermentation {
        int id
        int fermented_by_user_id
        int winery_id
        int vintage_year
        string yeast_strain
        string vessel_code
        float input_mass_kg
        float initial_sugar_brix
        float initial_density
        string status
        datetime start_date
        datetime imported_at
        bool is_deleted
        get_current_status()
        can_add_sample()
        complete()
    }
    
    class BaseSample {
        int id
        int fermentation_id
        datetime measurement_date
        float value
        string notes
        bool is_deleted
        float calculate_change_rate()
    }
    
    class SugarSample {
        float brix_value
    }
    
    class DensitySample {
        float sg_value
    }
    
    class CelsiusSample {
        float celsius_value
    }
    
    class FermentationNote {
        int id
        int fermentation_id
        int user_id
        string content
        datetime noted_at
    }
    
    class FermentationLotSource {
        int id
        int fermentation_id
        int harvest_lot_id
        float percentage
    }
    
    %% ====== ENUMS ======
    class SampleType {
        <<enumeration>>
        SUGAR
        DENSITY
        TEMP
    }
    
    class FermentationStatus {
        <<enumeration>>
        ACTIVE
        COMPLETED
        STUCK
        PROBLEM
    }
    
    %% ====== REPOSITORY INTERFACES ======
    class IFermentationRepository {
        <<interface>>
        get_by_id(id, winery_id)
        get_all(winery_id)
        create(fermentation, user_id)
        update(id, updates, user_id)
        delete(id, user_id)
    }
    
    class ISampleRepository {
        <<interface>>
        create(sample)
        get_latest(fermentation_id)
        get_all_for_fermentation(fermentation_id)
    }
    
    %% ====== RELATIONSHIPS ======
    BaseEntity <|-- Fermentation
    BaseEntity <|-- BaseSample
    BaseEntity <|-- FermentationNote
    BaseEntity <|-- FermentationLotSource
    BaseSample <|-- SugarSample
    BaseSample <|-- DensitySample
    BaseSample <|-- CelsiusSample
    Fermentation "1" --> "*" BaseSample : contains
    Fermentation "1" --> "*" FermentationNote : has notes
    Fermentation "1" --> "*" FermentationLotSource : sources
    Fermentation --> FermentationStatus : status
    BaseSample --> SampleType : type
```

---

## 2. Analysis Engine Module - Class Diagram

```mermaid
classDiagram
    %% ====== BASE CLASSES ======
    class BaseEntity {
        int id
        datetime created_at
        datetime updated_at
        datetime deleted_at
    }
    
    %% ====== AGGREGATE ROOT ======
    class Analysis {
        int id
        int fermentation_id
        int winery_id
        string status
        datetime analyzed_at
        string notes
        bool is_deleted
        add_anomaly(anomaly)
        add_recommendation(recommendation)
        get_anomaly_count()
        get_severity()
    }
    
    %% ====== VALUE OBJECTS ======
    class ComparisonResult {
        <<value_object>>
        float difference
        float percentage_change
        string trend_direction
    }
    
    class DeviationScore {
        <<value_object>>
        float score_value
        float max_value
        bool is_critical()
    }
    
    class ConfidenceLevel {
        <<value_object>>
        float confidence
        string interpretation
    }
    
    %% ====== COMPOSED ENTITIES ======
    class Anomaly {
        int id
        int analysis_id
        int winery_id
        string anomaly_type
        string severity
        float deviation_value
        string description
        datetime detected_at
    }
    
    class Recommendation {
        int id
        int analysis_id
        int anomaly_id
        int template_id
        string action
        string priority
        string status
        datetime implemented_at
    }
    
    class RecommendationTemplate {
        int id
        int winery_id
        string name
        string anomaly_type
        string action_text
        string expected_result
        bool is_active
    }
    
    %% ====== ENUMS ======
    class AnomalyType {
        <<enumeration>>
        SLOW_FERMENTATION
        STUCK_FERMENTATION
        HIGH_TEMPERATURE
        LOW_TEMPERATURE
        RAPID_COMPLETION
        INCOMPLETE_FERMENTATION
        UNUSUAL_DENSITY_JUMP
        CONTAMINATION_RISK
    }
    
    class SeverityLevel {
        <<enumeration>>
        LOW
        MEDIUM
        HIGH
        CRITICAL
    }
    
    class AnalysisStatus {
        <<enumeration>>
        PENDING
        IN_PROGRESS
        COMPLETED
        FAILED
    }
    
    %% ====== REPOSITORY INTERFACES ======
    class IAnalysisRepository {
        <<interface>>
        create(analysis)
        get_by_id(id, winery_id)
        get_by_fermentation(fermentation_id)
        update(id, updates)
    }
    
    class IAnomalyRepository {
        <<interface>>
        create(anomaly)
        get_by_analysis(analysis_id)
        get_critical(winery_id)
    }
    
    class IRecommendationRepository {
        <<interface>>
        create(recommendation)
        get_by_analysis(analysis_id)
        get_pending(winery_id)
    }
    
    class IRecommendationTemplateRepository {
        <<interface>>
        get_by_anomaly_type(anomaly_type, winery_id)
        get_all_active(winery_id)
    }
    
    %% ====== RELATIONSHIPS ======
    BaseEntity <|-- Analysis
    BaseEntity <|-- Anomaly
    BaseEntity <|-- Recommendation
    BaseEntity <|-- RecommendationTemplate
    Analysis "1" --> "*" Anomaly : contains
    Analysis "1" --> "*" Recommendation : has
    Anomaly --> AnomalyType : type
    Anomaly --> SeverityLevel : severity
    Anomaly --> DeviationScore : deviation
    Anomaly --> ComparisonResult : comparison
    Recommendation --> ConfidenceLevel : confidence
    Recommendation --> RecommendationTemplate : uses
    Analysis --> AnalysisStatus : status
```

---

## 3. Protocol Compliance Engine - Class Diagram (ADR-021)

> ⚠️ **Status**: 📋 PROPOSED (Not yet implemented)

```mermaid
classDiagram
    %% ====== BASE CLASSES ======
    class BaseEntity {
        int id
        int winery_id
        datetime created_at
        datetime updated_at
        datetime deleted_at
    }
    
    %% ====== MAIN ENTITIES ======
    class FermentationProtocol {
        int id
        int winery_id
        string varietal
        string protocol_name
        string description
        int total_steps
        float target_duration_days
        bool is_active
        get_step_by_order()
        get_next_step()
    }
    
    class ProtocolStep {
        int id
        int protocol_id
        int step_order
        string step_type
        string description
        int expected_day
        int duration_hours
        string notes
        bool is_critical
        float criticality_score
    }
    
    class ProtocolExecution {
        int id
        int fermentation_id
        int protocol_id
        int winery_id
        datetime start_date
        string status
        float compliance_score
        int completed_steps
        start_execution()
        mark_complete()
        calculate_compliance()
    }
    
    class StepCompletion {
        int id
        int execution_id
        int step_id
        datetime completed_at
        string notes
        bool on_schedule
        string verified_by_user_id
    }
    
    %% ====== ENUMS ======
    class StepType {
        <<enumeration>>
        YEAST_COUNT
        DAP_ADDITION
        H2S_CHECK
        PUNCHING_DOWN
        TEMPERATURE_CHECK
        DENSITY_MEASUREMENT
        NUTRIENT_ADDITION
        RELEASE_CO2
    }
    
    class ComplianceStatus {
        <<enumeration>>
        NOT_STARTED
        ON_SCHEDULE
        DELAYED
        SKIPPED
        COMPLETED
        DEVIATION_DETECTED
    }
    
    %% ====== REPOSITORY INTERFACES ======
    class IFermentationProtocolRepository {
        <<interface>>
        get_by_id(id, winery_id)
        get_by_varietal(varietal, winery_id)
        create(protocol)
        update(id, updates)
        list_active(winery_id)
    }
    
    class IProtocolExecutionRepository {
        <<interface>>
        create(execution)
        get_by_fermentation(fermentation_id)
        update_compliance_score(id, score)
        get_by_winery(winery_id)
    }
    
    class IStepCompletionRepository {
        <<interface>>
        create(completion)
        get_by_execution(execution_id)
        get_by_step(step_id)
        list_pending(execution_id)
    }
    
    %% ====== RELATIONSHIPS ======
    BaseEntity <|-- FermentationProtocol
    BaseEntity <|-- ProtocolStep
    BaseEntity <|-- ProtocolExecution
    BaseEntity <|-- StepCompletion
    
    FermentationProtocol "1" --> "*" ProtocolStep : contains
    ProtocolExecution --> FermentationProtocol : follows
    ProtocolExecution "1" --> "*" StepCompletion : logs
    StepCompletion --> ProtocolStep : completes
    
    ProtocolStep --> StepType : type
    ProtocolExecution --> ComplianceStatus : status
    StepCompletion --> ComplianceStatus : compliance
```

---

## 4. Fruit Origin Module - Class Diagram

```mermaid
classDiagram
    %% ====== BASE CLASSES ======
    class BaseEntity {
        int id
        datetime created_at
        datetime updated_at
        datetime deleted_at
    }
    
    %% ====== MAIN ENTITIES ======
    class Vineyard {
        int id
        int winery_id
        string name
        string region
        string classification
        string description
        bool is_active
        get_block_count()
        get_total_area()
    }
    
    class VineyardBlock {
        int id
        int vineyard_id
        string block_name
        float area_hectares
        int year_planted
        string soil_type
        string aspect
    }
    
    class HarvestLot {
        int id
        int vineyard_id
        int winery_id
        int harvest_year
        string lot_name
        float quantity_kg
        string harvest_date
        string harvest_method
        float ripeness_brix
        get_age_days()
    }
    
    class Grape {
        int id
        int harvest_lot_id
        string variety
        float percentage_composition
        string skin_type
        float sugar_content_brix
    }
    
    %% ====== ENUMS ======
    class GrapeVariety {
        <<enumeration>>
        CABERNET_SAUVIGNON
        CHARDONNAY
        PINOT_NOIR
        MERLOT
        SAUVIGNON_BLANC
        RIESLING
    }
    
    class SkinType {
        <<enumeration>>
        RED
        WHITE
    }
    
    class HarvestMethod {
        <<enumeration>>
        MANUAL
        MECHANICAL
        WHOLE_CLUSTER
    }
    
    %% ====== REPOSITORY INTERFACES ======
    class IVineyardRepository {
        <<interface>>
        create(vineyard)
        get_by_id(id, winery_id)
        get_all(winery_id)
        update(id, updates)
    }
    
    class IHarvestLotRepository {
        <<interface>>
        create(harvest_lot)
        get_by_id(id, winery_id)
        get_by_vineyard(vineyard_id)
        get_by_year(harvest_year, winery_id)
    }
    
    %% ====== RELATIONSHIPS ======
    BaseEntity <|-- Vineyard
    BaseEntity <|-- VineyardBlock
    BaseEntity <|-- HarvestLot
    BaseEntity <|-- Grape
    Vineyard "1" --> "*" VineyardBlock : contains
    HarvestLot --> GrapeVariety : variety
    HarvestLot --> HarvestMethod : method
    Grape --> SkinType : skin_type
    HarvestLot "1" --> "*" Grape : contains
    Vineyard "1" --> "*" HarvestLot : produces
```

---

## 4. Authentication Module - Class Diagram

```mermaid
classDiagram
    %% ====== BASE CLASSES ======
    class BaseEntity {
        int id
        datetime created_at
        datetime updated_at
        datetime deleted_at
    }
    
    %% ====== MAIN ENTITY ======
    class User {
        int id
        int winery_id
        string email
        string username
        string hashed_password
        string role
        bool is_active
        datetime last_login
        verify_password(password)
        can_access_winery(winery_id)
        get_permissions()
    }
    
    %% ====== ENUMS ======
    class UserRole {
        <<enumeration>>
        ADMIN
        WINEMAKER
        OPERATOR
        VIEWER
    }
    
    %% ====== DTOs ======
    class UserContext {
        <<DTO>>
        int user_id
        int winery_id
        string username
        string role
    }
    
    class LoginRequest {
        <<DTO>>
        string username
        string password
    }
    
    class LoginResponse {
        <<DTO>>
        string access_token
        string token_type
        int expires_in
    }
    
    class UserCreate {
        <<DTO>>
        string email
        string username
        string password
        string role
    }
    
    class UserResponse {
        <<DTO>>
        int id
        string email
        string username
        string role
        bool is_active
    }
    
    %% ====== REPOSITORY INTERFACE ======
    class IUserRepository {
        <<interface>>
        create(user)
        get_by_id(id, winery_id)
        get_by_username(username)
        get_by_email(email)
        update(id, updates)
    }
    
    %% ====== RELATIONSHIPS ======
    BaseEntity <|-- User
    User --> UserRole : role
    User --> UserContext : context
    LoginRequest --> User : authenticates
    LoginResponse --> UserContext : returns
    UserCreate --> User : creates
    User --> UserResponse : serializes
```

---

## 5. Winery Module - Class Diagram

```mermaid
classDiagram
    %% ====== BASE CLASSES ======
    class BaseEntity {
        int id
        datetime created_at
        datetime updated_at
        datetime deleted_at
    }
    
    %% ====== MAIN ENTITY (Multi-Tenancy Root) ======
    class Winery {
        int id
        string name
        string region
        string country
        string website
        string phone
        string email
        float latitude
        float longitude
        bool is_active
        datetime established_date
        get_user_count()
        get_fermentation_count()
        get_total_production()
    }
    
    %% ====== VALUE OBJECTS ======
    class Location {
        <<value_object>>
        string region
        string country
        float latitude
        float longitude
    }
    
    class ContactInfo {
        <<value_object>>
        string email
        string phone
        string website
    }
    
    %% ====== DTOs ======
    class WineryCreate {
        <<DTO>>
        string name
        string region
        string country
        string email
        string phone
    }
    
    class WineryUpdate {
        <<DTO>>
        string name
        string region
        string email
    }
    
    class WineryResponse {
        <<DTO>>
        int id
        string name
        string region
        string country
        string email
    }
    
    %% ====== REPOSITORY INTERFACE ======
    class IWineryRepository {
        <<interface>>
        create(winery)
        get_by_id(id)
        get_all()
        update(id, updates)
        get_by_region(region)
    }
    
    %% ====== RELATIONSHIPS ======
    BaseEntity <|-- Winery
    Winery --> Location : location
    Winery --> ContactInfo : contact
    WineryCreate --> Winery : creates
    WineryUpdate --> Winery : modifies
    Winery --> WineryResponse : serializes
```

---

## Summary

| Component | Entities | Value Objects | Enums | Interfaces | Status |
|-----------|----------|---|-------|------------|--------|
| **Fermentation** | 6 | - | 2 | 2 | ✅ Complete |
| **Protocol Compliance** | 4 | - | 2 | 3 | 📋 Proposed |
| **Analysis Engine** | 4 | 3 | 3 | 4 | 🔄 Phase 1 Done |
| **Fruit Origin** | 4 | - | 3 | 2 | ✅ Complete |
| **Authentication** | 1 | - | 1 | 1 | ✅ Complete |
| **Winery** | 1 | 2 | - | 1 | ✅ Complete |

---

## Navigation
👈 [Back to Architecture Diagrams](README.md)
👈 [Quick Reference](00-QUICK-REFERENCE.md)
👈 [Sequence Diagrams](04-SEQUENCE-DIAGRAMS.md)

```mermaid
classDiagram
    %% ====== DOMAIN LAYER - ENTITIES ======
    class Base {
        uuid id
        int winery_id
        datetime created_at
        datetime updated_at
    }
    
    class Analysis {
        uuid id
        uuid fermentation_id
        int winery_id
        string status
        datetime analyzed_at
        dict comparison_result
        dict confidence_level
        int historical_samples_count
        start()
        complete()
        add_anomaly()
        add_recommendation()
    }
    
    class Anomaly {
        uuid id
        uuid analysis_id
        string type
        string severity
        float deviation_score
        string description
    }
    
    class Recommendation {
        uuid id
        uuid analysis_id
        string category
        string action
        float confidence
        int expected_success_rate
        string reasoning
    }
    
    class RecommendationTemplate {
        uuid id
        int winery_id
        string anomaly_type
        string severity_level
        string action
        string instructions
        int effectiveness_score
    }
    
    %% ====== VALUE OBJECTS ======
    class ComparisonResult {
        float current_value
        float expected_min
        float expected_max
        float percentile_rank
        float deviation_percentage
        is_within_range()
    }
    
    class DeviationScore {
        float z_score
        float percentile
        float sigma_value
        is_critical()
        is_warning()
    }
    
    class ConfidenceLevel {
        string level
        float score
        int sample_count
    }
    
    %% ====== DOMAIN LAYER - ENUMS & INTERFACES ======
    class AnomalyType {
        SLOW_FERMENTATION
        STUCK_FERMENTATION
        HIGH_TEMPERATURE
        LOW_TEMPERATURE
        STUCK_WITH_TEMP
        H2S_PRODUCTION
        OX_STRESS
        INFECTION
    }
    
    class SeverityLevel {
        LOW
        MEDIUM
        HIGH
        CRITICAL
    }
    
    class AnalysisStatus {
        PENDING
        IN_PROGRESS
        COMPLETED
        ERROR
    }
    
    class IAnalysisRepository {
        <<interface>>
        +create(analysis)
        +get_by_id(id)
        +get_by_fermentation_id(ferm_id)
        +update_status(id, status)
        +list_by_winery(winery_id)
    }
    
    class IAnomalyRepository {
        <<interface>>
        +create_bulk(anomalies)
        +get_by_analysis_id(analysis_id)
        +get_by_type(type)
    }
    
    class IRecommendationRepository {
        <<interface>>
        +create_bulk(recommendations)
        +get_by_analysis_id(analysis_id)
        +rank_by_confidence(analysis_id)
    }
    
    class IRecommendationTemplateRepository {
        <<interface>>
        +get_by_type_severity(type, severity)
        +list_by_winery(winery_id)
        +get_most_effective(type)
    }
    
    %% ====== SERVICE LAYER - INTERFACES ======
    class IAnomalyDetectionService {
        <<interface>>
        +detect_slow_fermentation()
        +detect_stuck_fermentation()
        +detect_temperature_issues()
        +detect_h2s_production()
        +run_all_detections()
    }
    
    class IRecommendationService {
        <<interface>>
        +generate_recommendations()
        +rank_recommendations()
        +select_best_actions()
    }
    
    class IPatternAnalysisService {
        <<interface>>
        +extract_patterns()
        +compare_vs_historical()
        +score_similarity()
    }
    
    %% ====== SERVICE LAYER - IMPLEMENTATIONS ======
    class AnomalyDetectionService {
        -anomaly_repo: IAnomalyRepository
        -pattern_service: IPatternAnalysisService
        +detect_slow_fermentation()
        +detect_stuck_fermentation()
        +run_all_detections()
    }
    
    class RecommendationService {
        -rec_repo: IRecommendationRepository
        -template_repo: IRecommendationTemplateRepository
        +generate_recommendations()
        +rank_recommendations()
    }
    
    class PatternAnalysisService {
        +extract_patterns()
        +compare_vs_historical()
    }
    
    class AnalysisOrchestratorService {
        -analysis_repo: IAnalysisRepository
        -anomaly_detector: IAnomalyDetectionService
        -rec_service: IRecommendationService
        +orchestrate_analysis()
        +run_complete_analysis()
    }
    
    %% ====== REPOSITORY LAYER ======
    class AnalysisRepository {
        +create()
        +get_by_id()
        +update_status()
    }
    
    class AnomalyRepository {
        +create_bulk()
        +get_by_analysis_id()
    }
    
    class RecommendationRepository {
        +create_bulk()
        +get_by_analysis_id()
    }
    
    class RecommendationTemplateRepository {
        +get_by_type_severity()
        +list_by_winery()
    }
    
    class BaseRepository {
        #session: AsyncSession
    }
    
    %% ====== API LAYER - SCHEMAS ======
    class AnalysisRequest {
        fermentation_id: uuid
    }
    
    class AnomalyResponse {
        type: str
        severity: str
        description: str
        deviation_score: float
    }
    
    class RecommendationResponse {
        action: str
        confidence: float
        reasoning: str
    }
    
    class AnalysisResponse {
        status: str
        anomalies: List[AnomalyResponse]
        recommendations: List[RecommendationResponse]
    }
    
    %% ====== RELATIONSHIPS ======
    Base <|-- Analysis
    Base <|-- Anomaly
    Base <|-- Recommendation
    Base <|-- RecommendationTemplate
    
    Analysis "1" --o "0..*" Anomaly
    Analysis "1" --o "0..*" Recommendation
    
    Anomaly -- AnomalyType
    Anomaly -- SeverityLevel
    Analysis -- AnalysisStatus
    Recommendation -- SeverityLevel
    
    Analysis -- ComparisonResult
    Analysis -- DeviationScore
    Analysis -- ConfidenceLevel
    
    AnalysisRepository --|> IAnalysisRepository
    AnomalyRepository --|> IAnomalyRepository
    RecommendationRepository --|> IRecommendationRepository
    RecommendationTemplateRepository --|> IRecommendationTemplateRepository
    
    AnalysisRepository --|> BaseRepository
    AnomalyRepository --|> BaseRepository
    RecommendationRepository --|> BaseRepository
    RecommendationTemplateRepository --|> BaseRepository
    
    AnomalyDetectionService --|> IAnomalyDetectionService
    RecommendationService --|> IRecommendationService
    PatternAnalysisService --|> IPatternAnalysisService
    
    AnomalyDetectionService --> IAnomalyRepository
    AnomalyDetectionService --> IPatternAnalysisService
    
    RecommendationService --> IRecommendationRepository
    RecommendationService --> IRecommendationTemplateRepository
    
    AnalysisOrchestratorService --> IAnalysisRepository
    AnalysisOrchestratorService --> IAnomalyDetectionService
    AnalysisOrchestratorService --> IRecommendationService
    
    AnalysisRequest --> Analysis
    AnomalyResponse --> Anomaly
    RecommendationResponse --> Recommendation
    AnalysisResponse --> Analysis
```

---

## Fruit Origin Module - Class Diagram

```mermaid
classDiagram
    %% ====== DOMAIN LAYER - ENTITIES ======
    class BaseEntity {
        int id
        datetime created_at
        datetime updated_at
        deleted_at
    }
    
    class Vineyard {
        int winery_id
        string code
        string name
        string notes
        bool is_deleted
    }
    
    class VineyardBlock {
        int vineyard_id
        string code
        string name
        float hectares
    }
    
    class HarvestLot {
        int winery_id
        int vineyard_id
        int grape_variety_id
        string code
        string harvest_date
        string grape_type
        float kg_harvested
        string harvest_method
        string notes
        is_available()
        close_lot()
    }
    
    class Grape {
        string variety_name
        string skin_type
    }
    
    %% ====== DOMAIN LAYER - ENUMS & INTERFACES ======
    class GrapeVariety {
        CABERNET_SAUVIGNON
        CHARDONNAY
        PINOT_NOIR
        MERLOT
        SAUVIGNON_BLANC
    }
    
    class SkinType {
        RED
        WHITE
    }
    
    class HarvestMethod {
        MANUAL
        MECHANICAL
        WHOLE_CLUSTER
    }
    
    class IVineyardRepository {
        <<interface>>
        +get_by_id(id, winery_id)
        +create(vineyard, user_id)
        +update(id, data, user_id)
        +list_by_winery(winery_id)
    }
    
    class IHarvestLotRepository {
        <<interface>>
        +get_by_id(id, winery_id)
        +create(lot, user_id)
        +update(id, data, user_id)
        +list_by_vineyard(vineyard_id)
        +list_available(winery_id)
    }
    
    %% ====== SERVICE LAYER - INTERFACES ======
    class IVineyardService {
        <<interface>>
        +create_vineyard()
        +get_vineyard()
        +update_vineyard()
        +add_block()
        +remove_block()
    }
    
    class IHarvestLotService {
        <<interface>>
        +create_harvest_lot()
        +get_harvest_lot()
        +update_harvest_lot()
        +close_harvest_lot()
    }
    
    %% ====== SERVICE LAYER - IMPLEMENTATIONS ======
    class VineyardService {
        -repo: IVineyardRepository
        +create_vineyard()
        +get_vineyard()
        +update_vineyard()
    }
    
    class HarvestLotService {
        -repo: IHarvestLotRepository
        +create_harvest_lot()
        +get_harvest_lot()
        +close_harvest_lot()
    }
    
    %% ====== REPOSITORY LAYER ======
    class VineyardRepository {
        +get_by_id()
        +create()
        +update()
        +list_by_winery()
    }
    
    class HarvestLotRepository {
        +get_by_id()
        +create()
        +update()
        +list_by_vineyard()
    }
    
    class BaseRepository {
        #session: AsyncSession
    }
    
    %% ====== API LAYER - SCHEMAS ======
    class VineyardCreateRequest {
        code: str
        name: str
        notes: Optional[str]
    }
    
    class HarvestLotCreateRequest {
        vineyard_id: int
        grape_variety: str
        code: str
        harvest_date: str
        kg_harvested: float
    }
    
    %% ====== RELATIONSHIPS ======
    BaseEntity <|-- Vineyard
    BaseEntity <|-- VineyardBlock
    BaseEntity <|-- HarvestLot
    BaseEntity <|-- Grape
    
    Vineyard "1" --o "0..*" VineyardBlock
    HarvestLot --> Vineyard
    HarvestLot --> Grape
    
    Grape -- GrapeVariety
    Grape -- SkinType
    HarvestLot -- HarvestMethod
    
    VineyardRepository --|> IVineyardRepository
    HarvestLotRepository --|> IHarvestLotRepository
    
    VineyardRepository --|> BaseRepository
    HarvestLotRepository --|> BaseRepository
    
    VineyardService --|> IVineyardService
    HarvestLotService --|> IHarvestLotService
    
    VineyardService --> IVineyardRepository
    HarvestLotService --> IHarvestLotRepository
    
    VineyardCreateRequest --> Vineyard
    HarvestLotCreateRequest --> HarvestLot
```

---

## Authentication Module - Class Diagram

```mermaid
classDiagram
    %% ====== DOMAIN LAYER - ENTITIES ======
    class BaseEntity {
        int id
        datetime created_at
        datetime updated_at
    }
    
    class User {
        int id
        int winery_id
        string email
        string username
        string full_name
        string hashed_password
        UserRole role
        bool is_active
        bool is_verified
        datetime last_login_at
        get_permissions()
        has_permission()
    }
    
    %% ====== DOMAIN LAYER - ENUMS & INTERFACES ======
    class UserRole {
        ADMIN
        WINEMAKER
        OPERATOR
        VIEWER
        get_permissions()
    }
    
    class UserContext {
        int user_id
        int winery_id
        string email
        UserRole role
        datetime iat
        datetime exp
    }
    
    class IUserRepository {
        <<interface>>
        +get_by_id(id)
        +get_by_email(email)
        +get_by_username(username)
        +create(user)
        +update(id, data)
        +delete(id)
    }
    
    class IPasswordService {
        <<interface>>
        +hash_password(password)
        +verify_password(password, hash)
    }
    
    class IJwtService {
        <<interface>>
        +encode_token(claims)
        +decode_token(token)
        +refresh_token(refresh_token)
    }
    
    class IAuthService {
        <<interface>>
        +login(email, password)
        +register(data)
        +logout()
        +refresh_access_token(token)
        +change_password()
        +verify_email()
    }
    
    %% ====== DTOs ======
    class LoginRequest {
        string email
        string password
    }
    
    class LoginResponse {
        string access_token
        string refresh_token
        string token_type
    }
    
    class UserCreate {
        string email
        string username
        string password
        string full_name
        int winery_id
    }
    
    class UserResponse {
        int id
        string email
        string username
        string full_name
        int winery_id
        UserRole role
        bool is_active
    }
    
    class PasswordChangeRequest {
        string old_password
        string new_password
    }
    
    %% ====== SERVICE LAYER - IMPLEMENTATIONS ======
    class PasswordService {
        -config: PasswordConfig
        +hash_password()
        +verify_password()
    }
    
    class JwtService {
        -config: JwtConfig
        +encode_token()
        +decode_token()
        +refresh_token()
    }
    
    class AuthService {
        -user_repo: IUserRepository
        -password_service: IPasswordService
        -jwt_service: IJwtService
        +login()
        +register()
        +change_password()
    }
    
    %% ====== REPOSITORY LAYER ======
    class UserRepository {
        +get_by_id()
        +get_by_email()
        +get_by_username()
        +create()
        +update()
        +delete()
    }
    
    class BaseRepository {
        #session: AsyncSession
    }
    
    %% ====== API LAYER ======
    class AuthRouter {
        +login()
        +register()
        +refresh()
        +logout()
        +change_password()
    }
    
    %% ====== RELATIONSHIPS ======
    BaseEntity <|-- User
    User -- UserRole
    User -- UserContext
    
    UserRepository --|> IUserRepository
    UserRepository --|> BaseRepository
    
    PasswordService --|> IPasswordService
    JwtService --|> IJwtService
    AuthService --|> IAuthService
    
    AuthService --> IUserRepository
    AuthService --> IPasswordService
    AuthService --> IJwtService
    
    LoginRequest --> AuthService
    LoginResponse --> JwtService
    UserCreate --> User
    UserResponse --> User
    PasswordChangeRequest --> AuthService
    


