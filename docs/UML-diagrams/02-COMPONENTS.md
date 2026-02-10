# Component Diagrams

> **Overview**: Detailed component relationships showing how different parts work together.

## Fermentation Module Components

```mermaid
graph TB
    subgraph DomainComp["🎯 Domain Component"]
        FermEntity["Fermentation Entity"]
        SampleHier["Sample Hierarchy<br/>BaseSample<br/>└─ SugarSample<br/>└─ DensitySample<br/>└─ CelsiusSample"]
        FermNoteEntity["FermentationNote Entity"]
        LotSourceEntity["FermentationLotSource Entity"]
        
        FermRepoInterface["IFermentationRepository"]
        SampleRepoInterface["ISampleRepository"]
        FermNoteRepoInterface["IFermentationNoteRepository"]
        
        SampleType["SampleType Enum<br/>(SUGAR, DENSITY, TEMP)"]
        Status["Status Enum<br/>(ACTIVE, COMPLETED,<br/>STUCK, PROBLEM)"]
        
        FermErrors["Domain Errors<br/>FermentationNotFound<br/>InvalidSample<br/>ChronologyError"]
    end
    
    subgraph RepoComp["🗄️ Repository Component"]
        FermRepo["FermentationRepository<br/>- get_by_id()<br/>- create()<br/>- update()<br/>- list_by_winery()"]
        
        SampleRepo["SampleRepository<br/>- create()<br/>- get_latest()<br/>- list_for_ferm()"]
        
        LotSourceRepo["LotSourceRepository<br/>- get_by_ferm_id()"]
        
        FermNoteRepo["FermentationNoteRepository<br/>- create()<br/>- list_for_ferm()"]
        
        BaseRepo["BaseRepository<br/>(infrastructure helper)"]
        ErrorMapper["Error Mapper<br/>DB errors →<br/>Domain errors"]
    end
    
    subgraph ServiceComp["⚙️ Service Component"]
        FermService["FermentationService<br/>- create_fermentation()<br/>- get_fermentation()<br/>- update_fermentation()<br/>- list_fermentations()"]
        
        SampleService["SampleService<br/>- create_sample()<br/>- get_latest_sample()<br/>- validate_sample()"]
        
        ValidationOrch["ValidationOrchestrator<br/>- orchestrate_validations()<br/>- value_validation()<br/>- chronology_validation()"]
        
        ValueValidator["ValueValidationService<br/>- validate_range()<br/>- check_business_rules()"]
        
        ChronoValidator["ChronologyValidationService<br/>- check_sample_order()<br/>- validate_timing()"]
        
        BizRuleValidator["BusinessRuleValidationService<br/>- check_fermentation_status()<br/>- validate_transitions()"]
    end
    
    subgraph ApiComp["🔌 API Component"]
        FermRouter["Fermentation Router<br/>GET /fermentations<br/>POST /fermentations<br/>GET /fermentations/{id}<br/>PUT /fermentations/{id}"]
        
        SampleRouter["Sample Router<br/>GET /fermentations/{id}/samples<br/>POST /fermentations/{id}/samples<br/>GET /fermentations/{id}/samples/{sample_id}"]
        
        HistoricalRouter["Historical Router (ADR-032)<br/>GET /fermentations/{id}/historical<br/>GET /fermentations/{id}/compare"]
        
        FermSchema["Request/Response DTOs<br/>FermentationCreate<br/>FermentationUpdate<br/>FermentationResponse"]
        
        SampleSchema["Request/Response DTOs<br/>SampleCreate<br/>SampleResponse"]
    end
    
    subgraph Tests["🧪 Tests"]
        UnitTests["Unit Tests<br/>- Service layer<br/>- Validators<br/>- Entities"]
        IntegrationTests["Integration Tests<br/>- Repository<br/>- Service + Repository<br/>- End-to-end"]
        Fixtures["Test Fixtures<br/>- WineryFixture<br/>- FermentationFixture<br/>- SampleFixture"]
    end
    
    %% Domain connections
    FermEntity -->|composites| SampleHier
    FermEntity -->|composites| FermNoteEntity
    FermEntity -->|references| LotSourceEntity
    
    FermRepoInterface -->|contracts| FermEntity
    SampleRepoInterface -->|contracts| SampleHier
    FermNoteRepoInterface -->|contracts| FermNoteEntity
    
    SampleType -->|used by| SampleHier
    Status -->|used by| FermEntity
    
    %% Repository connections
    FermRepo -->|implements| FermRepoInterface
    SampleRepo -->|implements| SampleRepoInterface
    LotSourceRepo -->|accesses| LotSourceEntity
    FermNoteRepo -->|implements| FermNoteRepoInterface
    
    FermRepo -->|extends| BaseRepo
    SampleRepo -->|extends| BaseRepo
    ErrorMapper -->|helps| BaseRepo
    
    %% Service connections
    FermService -->|uses| FermRepoInterface
    FermService -->|coordinates| ValidationOrch
    
    SampleService -->|uses| SampleRepoInterface
    SampleService -->|calls| ValidationOrch
    
    ValidationOrch -->|delegates to| ValueValidator
    ValidationOrch -->|delegates to| ChronoValidator
    ValidationOrch -->|delegates to| BizRuleValidator
    
    %% API connections
    FermRouter -->|calls| FermService
    SampleRouter -->|calls| SampleService
    HistoricalRouter -->|calls| FermService
    
    FermSchema -->|serializes| FermEntity
    SampleSchema -->|serializes| SampleHier
    
    %% Test connections
    UnitTests -->|tests| ServiceComp
    IntegrationTests -->|tests| RepoComp
    Fixtures -->|supports| Tests
    
    style DomainComp fill:#f57f17,color:#fff
    style RepoComp fill:#2e7d32,color:#fff
    style ServiceComp fill:#0277bd,color:#fff
    style ApiComp fill:#d32f2f,color:#fff
    style Tests fill:#7b1fa2,color:#fff
```

---

## Protocol Compliance Engine Components (ADR-021)

> ⚠️ **Status**: 📋 PROPOSED (Not yet implemented)  
> **Purpose**: Track fermentation protocol steps, detect deviations, audit compliance

```mermaid
graph TB
    subgraph DomainComp["🎯 Domain Component"]
        ProtocolEntity["FermentationProtocol Entity<br/>(Master protocol<br/>by varietal)"]
        StepEntity["ProtocolStep Entity<br/>(Ordered steps)"]
        ExecutionEntity["ProtocolExecution Entity<br/>(Track per ferm)"]
        ComplianceEntity["StepCompletion Entity<br/>(Audit log)"]
        
        StepType["StepType Enum<br/>(YEAST_COUNT,<br/>DAP_ADDITION,<br/>H2S_CHECK,<br/>PUNCHING_DOWN)"]
        
        ComplianceStatus["ComplianceStatus Enum<br/>(ON_SCHEDULE,<br/>DELAYED,<br/>SKIPPED,<br/>COMPLETED)"]
        
        ProtocolRepoInterface["IFermentationProtocolRepository"]
        ExecutionRepoInterface["IProtocolExecutionRepository"]
    end
    
    subgraph RepoComp["🗄️ Repository Component"]
        ProtocolRepo["ProtocolRepository<br/>- create_protocol()<br/>- get_by_varietal()"]
        
        ExecutionRepo["ProtocolExecutionRepository<br/>- start_execution()<br/>- log_completion()"]
    end
    
    subgraph ServiceComp["⚙️ Service Component"]
        ProtocolService["ProtocolService (Phase 1)<br/>- create_protocol()<br/>- get_next_steps()"]
        
        ComplianceService["ComplianceTrackingService (Phase 2)<br/>- mark_step_complete()<br/>- detect_deviations()<br/>- calculate_score()"]
    end
    
    subgraph ApiComp["🔌 API Component"]
        ProtocolRouter["Protocol Router (Phase 3)<br/>GET /fermentations/{id}/protocol<br/>POST /fermentations/{id}/steps/{step_id}/complete"]
    end
    
    %% Connections
    ProtocolEntity -->|contains| StepEntity
    ProtocolEntity -->|linked to| ExecutionEntity
    ExecutionEntity -->|records| ComplianceEntity
    
    ProtocolRepo -->|implements| ProtocolRepoInterface
    ExecutionRepo -->|implements| ExecutionRepoInterface
    
    ProtocolService -->|uses| ProtocolRepoInterface
    ComplianceService -->|uses| ExecutionRepoInterface
    
    ProtocolRouter -->|calls| ProtocolService
    ProtocolRouter -->|calls| ComplianceService
    
    style DomainComp fill:#f57f17,color:#fff
    style RepoComp fill:#2e7d32,color:#fff
    style ServiceComp fill:#0277bd,color:#fff
    style ApiComp fill:#d32f2f,color:#fff
```

### Implementation Status
| Phase | Component | Status |
|-------|-----------|--------|
| 0 | Domain Entities | 📋 Proposed |
| 1 | Repository Layer | 📋 Proposed |
| 2 | Service Layer | 📋 Proposed |
| 3 | API Layer | 📋 Proposed |

**Reference**: [ADR-021: Fermentation Protocol Compliance Engine](../../.ai-context/adr/ADR-021-protocol-compliance-engine.md)

---

## Analysis Engine Components

```mermaid
graph TB
    subgraph DomainComp["🎯 Domain Component"]
        AnalysisEntity["Analysis Entity<br/>(Aggregate Root)"]
        AnomalyEntity["Anomaly Entity"]
        RecommendationEntity["Recommendation Entity"]
        TemplateEntity["RecommendationTemplate Entity"]
        
        ComparisonResult["ComparisonResult<br/>(Value Object)"]
        DeviationScore["DeviationScore<br/>(Value Object)"]
        ConfidenceLevel["ConfidenceLevel<br/>(Value Object)"]
        
        AnomalyType["AnomalyType Enum<br/>(SLOW_FERMENTATION,<br/>STUCK_FERMENTATION,<br/>HIGH_TEMPERATURE,<br/>LOW_TEMPERATURE,<br/>STUCK_WITH_TEMP,<br/>H2S_PRODUCTION,<br/>OX_STRESS,<br/>INFECTION)"]
        
        SeverityLevel["SeverityLevel Enum<br/>(LOW, MEDIUM,<br/>HIGH, CRITICAL)"]
        
        AnalysisStatus["AnalysisStatus Enum<br/>(PENDING, IN_PROGRESS,<br/>COMPLETED, ERROR)"]
        
        AnalysisRepoInterface["IAnalysisRepository"]
        AnomalyRepoInterface["IAnomalyRepository"]
        RecommendationRepoInterface["IRecommendationRepository"]
        TemplateRepoInterface["IRecommendationTemplateRepository"]
    end
    
    subgraph RepoComp["🗄️ Repository Component"]
        AnalysisRepo["AnalysisRepository<br/>- create()<br/>- get_by_id()<br/>- get_by_fermentation_id()<br/>- update_status()"]
        
        AnomalyRepo["AnomalyRepository<br/>- create_bulk()<br/>- get_by_analysis_id()<br/>- get_by_type()"]
        
        RecommendationRepo["RecommendationRepository<br/>- create_bulk()<br/>- get_by_analysis_id()<br/>- rank_by_confidence()"]
        
        TemplateRepo["RecommendationTemplateRepository<br/>- get_by_type()<br/>- get_by_severity()<br/>- list_by_winery()"]
        
        AnalysisReadModel["AnalysisReadModel<br/>(Optimized queries)"]
    end
    
    subgraph ServiceComp["⚙️ Service Component"]
        AnomalyDetectionService["AnomalyDetectionService (Phase 2)<br/>- detect_slow_fermentation()<br/>- detect_stuck_fermentation()<br/>- detect_temperature_issues()<br/>- detect_h2s_production()<br/>- calculate_deviation()"]
        
        RecommendationService["RecommendationService (Phase 3)<br/>- generate_recommendations()<br/>- rank_recommendations()<br/>- apply_template()"]
        
        PatternAnalysisService["PatternAnalysisService (ADR-034)<br/>- extract_patterns()<br/>- compare_vs_historical()<br/>- score_similarity()"]
        
        AnalysisOrchestratorService["AnalysisOrchestratorService (Phase 4)<br/>- orchestrate_analysis()<br/>- run_all_detectors()<br/>- correlate_results()"]
    end
    
    subgraph ApiComp["🔌 API Component"]
        AnalysisRouter["Analysis Router (Phase 3)<br/>POST /fermentations/{id}/analyze<br/>GET /fermentations/{id}/analysis<br/>GET /fermentations/{id}/anomalies<br/>GET /fermentations/{id}/recommendations"]
        
        AnalysisSchema["Request/Response DTOs<br/>AnalysisRequest<br/>AnalysisResponse<br/>AnomalyResponse<br/>RecommendationResponse"]
    end
    
    subgraph Tests["🧪 Tests"]
        UnitTests["Unit Tests<br/>- Detection algorithms<br/>- Scoring logic<br/>- Ranking"]
        IntegrationTests["Integration Tests<br/>- Repository layer<br/>- Service coordination<br/>- End-to-end analysis"]
        Fixtures["Test Fixtures<br/>- SampleData<br/>- HistoricalPatterns<br/>- AnalysisExpectations"]
    end
    
    %% Domain connections
    AnalysisEntity -->|composites| AnomalyEntity
    AnalysisEntity -->|composites| RecommendationEntity
    AnalysisEntity -->|uses| ComparisonResult
    AnalysisEntity -->|uses| DeviationScore
    AnalysisEntity -->|uses| ConfidenceLevel
    
    AnomalyType -->|used by| AnomalyEntity
    SeverityLevel -->|used by| AnomalyEntity
    SeverityLevel -->|used by| RecommendationEntity
    AnalysisStatus -->|used by| AnalysisEntity
    
    AnalysisRepoInterface -->|contracts| AnalysisEntity
    AnomalyRepoInterface -->|contracts| AnomalyEntity
    RecommendationRepoInterface -->|contracts| RecommendationEntity
    TemplateRepoInterface -->|contracts| TemplateEntity
    
    %% Repository connections
    AnalysisRepo -->|implements| AnalysisRepoInterface
    AnomalyRepo -->|implements| AnomalyRepoInterface
    RecommendationRepo -->|implements| RecommendationRepoInterface
    TemplateRepo -->|implements| TemplateRepoInterface
    
    AnalysisReadModel -->|optimizes| AnalysisRepo
    
    %% Service connections
    AnomalyDetectionService -->|uses| AnomalyRepoInterface
    AnomalyDetectionService -->|uses| PatternAnalysisService
    AnomalyDetectionService -->|produces| AnomalyEntity
    
    RecommendationService -->|uses| RecommendationRepoInterface
    RecommendationService -->|uses| TemplateRepoInterface
    RecommendationService -->|produces| RecommendationEntity
    
    PatternAnalysisService -->|reads from| AnalysisRepo
    
    AnalysisOrchestratorService -->|orchestrates| AnomalyDetectionService
    AnalysisOrchestratorService -->|orchestrates| RecommendationService
    AnalysisOrchestratorService -->|uses| AnalysisRepoInterface
    
    %% API connections
    AnalysisRouter -->|calls| AnalysisOrchestratorService
    AnalysisSchema -->|serializes| AnalysisEntity
    
    %% Test connections
    UnitTests -->|tests| ServiceComp
    IntegrationTests -->|tests| RepoComp
    Fixtures -->|supports| Tests
    
    style DomainComp fill:#f57f17,color:#fff
    style RepoComp fill:#2e7d32,color:#fff
    style ServiceComp fill:#0277bd,color:#fff
    style ApiComp fill:#d32f2f,color:#fff
    style Tests fill:#7b1fa2,color:#fff
```

### Implementation Status
| Phase | Component | Status | Notes |
|-------|-----------|--------|-------|
| 1 | Domain + Repository | ✅ Implemented | 44 tests passing |
| 2-5 | Service + API | 📋 Pending | Planned for MVP Phase 2 |

> **Integration with Protocol Compliance Engine (ADR-021)**:  
> Analysis Engine can use Protocol Compliance Score as contextual factor:
> - `ComplianceScore < 80%` → Lower confidence in anomaly detection
> - `StepSkipped('H2S_CHECK')` → Flag for H₂S monitoring
> - See [Protocol Compliance Engine Components](#protocol-compliance-engine-components-adr-021) for details

**Cross-References**:
- [Protocol Compliance Engine](#protocol-compliance-engine-components-adr-021) - Integration points
- [Class Diagrams: Analysis Engine](03-CLASS-DIAGRAMS.md#2-analysis-engine-module---class-diagram) - Detailed entity structure

---

## Fruit Origin Module Components

```mermaid
graph TB
    subgraph DomainComp["🎯 Domain Component"]
        VineyardEntity["Vineyard Entity"]
        VineyardBlockEntity["VineyardBlock Entity"]
        HarvestLotEntity["HarvestLot Entity"]
        GrapeEntity["Grape Entity"]
        
        VineyardRepoInterface["IVineyardRepository"]
        HarvestLotRepoInterface["IHarvestLotRepository"]
        
        Enums["Enums<br/>GrapeVariety<br/>SkinType<br/>HarvestMethod"]
        
        Errors["Domain Errors<br/>VineyardNotFound<br/>HarvestLotNotFound<br/>InvalidLocation"]
    end
    
    subgraph RepoComp["🗄️ Repository Component"]
        VineyardRepo["VineyardRepository<br/>- create()<br/>- get_by_id()<br/>- list_by_winery()"]
        
        HarvestLotRepo["HarvestLotRepository<br/>- create()<br/>- get_by_id()<br/>- list_by_vineyard()"]
        
        GrapeVarietyRepo["GrapeVarietyRepository<br/>(read-only)<br/>- get_by_name()"]
    end
    
    subgraph ServiceComp["⚙️ Service Component"]
        VineyardService["VineyardService (ADR-014)<br/>- create_vineyard()<br/>- get_vineyard()<br/>- update_vineyard()<br/>- add_block()"]
        
        HarvestLotService["HarvestLotService (ADR-014)<br/>- create_harvest_lot()<br/>- get_harvest_lot()<br/>- close_harvest_lot()"]
    end
    
    subgraph ApiComp["🔌 API Component"]
        VineyardRouter["Vineyard Router (ADR-018)<br/>GET /vineyards<br/>POST /vineyards<br/>GET /vineyards/{id}"]
        
        HarvestLotRouter["HarvestLot Router (ADR-018)<br/>GET /harvest-lots<br/>POST /harvest-lots<br/>PUT /harvest-lots/{id}"]
    end
    
    subgraph Tests["🧪 Tests"]
        UnitTests["Unit Tests"]
        IntegrationTests["Integration Tests"]
    end
    
    %% Connections
    VineyardEntity -->|composites| VineyardBlockEntity
    HarvestLotEntity -->|references| VineyardEntity
    HarvestLotEntity -->|references| GrapeEntity
    
    Enums -->|used by| HarvestLotEntity
    Errors -->|raised by| ServiceComp
    
    VineyardRepo -->|implements| VineyardRepoInterface
    HarvestLotRepo -->|implements| HarvestLotRepoInterface
    
    VineyardService -->|uses| VineyardRepoInterface
    HarvestLotService -->|uses| HarvestLotRepoInterface
    
    VineyardRouter -->|calls| VineyardService
    HarvestLotRouter -->|calls| HarvestLotService
    
    style DomainComp fill:#f57f17,color:#fff
    style RepoComp fill:#2e7d32,color:#fff
    style ServiceComp fill:#0277bd,color:#fff
    style ApiComp fill:#d32f2f,color:#fff
    style Tests fill:#7b1fa2,color:#fff
```

---

## Authentication Module Components

```mermaid
graph TB
    subgraph DomainComp["🎯 Domain Component"]
        UserEntity["User Entity<br/>id, email, username<br/>full_name, winery_id<br/>role, is_active"]
        
        UserRole["UserRole Enum<br/>ADMIN<br/>WINEMAKER<br/>OPERATOR<br/>VIEWER"]
        
        UserDTOs["DTOs<br/>UserContext<br/>LoginRequest/Response<br/>UserCreate/Update<br/>UserResponse<br/>RefreshTokenRequest<br/>PasswordChangeRequest"]
        
        Errors["Domain Errors<br/>AuthenticationError<br/>InvalidCredentialsError<br/>TokenExpiredError<br/>UserNotFoundError<br/>UserAlreadyExistsError"]
        
        IUserRepository["IUserRepository"]
        IPasswordService["IPasswordService"]
        IJwtService["IJwtService"]
        IAuthService["IAuthService"]
    end
    
    subgraph RepoComp["🗄️ Repository Component"]
        UserRepository["UserRepository<br/>- get_by_id()<br/>- get_by_email()<br/>- get_by_username()<br/>- create()<br/>- update()<br/>- delete()"]
    end
    
    subgraph ServiceComp["⚙️ Service Component"]
        PasswordService["PasswordService<br/>- hash_password()<br/>- verify_password()"]
        
        JwtService["JwtService<br/>- encode_token()<br/>- decode_token()<br/>- refresh_token()"]
        
        AuthService["AuthService<br/>- login()<br/>- register()<br/>- logout()<br/>- change_password()"]
    end
    
    subgraph ApiComp["🔌 API Component"]
        AuthRouter["Auth Router<br/>POST /auth/login<br/>POST /auth/register<br/>POST /auth/refresh<br/>POST /auth/logout<br/>POST /auth/change-password"]
        
        AuthDeps["FastAPI Dependencies<br/>get_current_user()<br/>get_current_admin()"]
    end
    
    subgraph Tests["🧪 Tests"]
        UnitTests["Unit Tests<br/>- Password hashing<br/>- JWT encoding<br/>- Auth flows"]
        IntegrationTests["Integration Tests<br/>- Login workflow<br/>- Token refresh<br/>- User creation"]
    end
    
    %% Connections
    UserEntity -->|has| UserRole
    UserEntity -->|referenced by| UserDTOs
    
    Errors -->|raised by| ServiceComp
    
    UserRepository -->|implements| IUserRepository
    PasswordService -->|implements| IPasswordService
    JwtService -->|implements| IJwtService
    AuthService -->|implements| IAuthService
    
    AuthService -->|uses| IUserRepository
    AuthService -->|uses| IPasswordService
    AuthService -->|uses| IJwtService
    
    AuthRouter -->|calls| AuthService
    AuthDeps -->|uses| JwtService
    
    UnitTests -->|tests| ServiceComp
    IntegrationTests -->|tests| RepoComp
    
    style DomainComp fill:#f57f17,color:#fff
    style RepoComp fill:#2e7d32,color:#fff
    style ServiceComp fill:#0277bd,color:#fff
    style ApiComp fill:#d32f2f,color:#fff
    style Tests fill:#7b1fa2,color:#fff
```

---

## Status

| Component | Status | Phase |
|-----------|--------|-------|
| **Fermentation Module** | ✅ Complete | Domain + Service + API + Tests |
| **Protocol Compliance Engine** | 📋 Proposed | Phase 0-3 Pending (ADR-021) |
| **Analysis Engine** | 🔄 In Progress | Phase 1 Domain + Phase 2-5 Pending |
| **Fruit Origin Module** | ✅ Complete | Domain + Service + API + Tests |
| **Authentication Module** | ✅ Complete | Domain + Service + API + Tests |

