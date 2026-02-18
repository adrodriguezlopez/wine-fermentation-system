# General Architecture Diagram

> **Overview**: Complete system architecture showing all modules, their relationships, and data flow.

## System Architecture (High-Level)

```mermaid
graph TB
    subgraph User["🧑 User Layer"]
        API["REST API<br/>FastAPI"]
        WEB["Web Frontend<br/>React/Vue"]
    end

    subgraph Auth["🔐 Shared Authentication"]
        AuthModule["Auth Module<br/>domain/service/repo"]
        User["User Entity<br/>roles, winery_id"]
    end

    subgraph Fermentation["🍇 Fermentation Module"]
        FermDomain["Domain<br/>Fermentation, Samples<br/>BaseSample, SugarSample,<br/>DensitySample"]
        FermService["Service Layer<br/>FermentationService<br/>SampleService<br/>ValidationOrchestrator"]
        FermRepo["Repository Layer<br/>FermentationRepository<br/>SampleRepository<br/>LotSourceRepository"]
    end

    subgraph FruitOrigin["🌍 Fruit Origin Module"]
        FruitDomain["Domain<br/>Vineyard, VineyardBlock<br/>HarvestLot, GrapeVariety"]
        FruitService["Service Layer<br/>VineyardService<br/>HarvestLotService"]
        FruitRepo["Repository Layer<br/>VineyardRepository<br/>HarvestLotRepository"]
    end

    subgraph Winery["🏪 Winery Module"]
        WineryDomain["Domain<br/>Winery Entity"]
        WineryService["Service Layer<br/>WineryService"]
        WineryRepo["Repository Layer<br/>WineryRepository"]
    end

    subgraph Protocol["📋 Protocol Compliance Engine"]
        ProtocolDomain["Domain<br/>FermentationProtocol<br/>ProtocolStep, ProtocolExecution<br/>StepCompletion"]
        ProtocolService["Service Layer (Phase 1-3)<br/>ProtocolService<br/>ComplianceTrackingService<br/>ProtocolAlertService"]
        ProtocolRepo["Repository Layer<br/>ProtocolRepository<br/>ExecutionRepository"]
    end

    subgraph Analysis["📊 Analysis Engine"]
        AnalysisDomain["Domain<br/>Analysis, Anomaly<br/>Recommendation<br/>RecommendationTemplate"]
        AnalysisService["Service Layer (Phase 2-5)<br/>AnomalyDetectionService<br/>RecommendationService<br/>PatternAnalysisService"]
        AnalysisRepo["Repository Layer<br/>AnalysisRepository<br/>AnomalyRepository<br/>RecommendationRepository<br/>TemplateRepository"]
    end

    subgraph Historical["📚 Historical Data"]
        HistDomain["Domain<br/>ETL Models"]
        HistService["Service Layer<br/>ETLService<br/>PatternExtractorService"]
        HistRepo["Repository Layer<br/>HistoricalRepository"]
    end

    subgraph Shared["🔗 Shared Infrastructure"]
        DB["PostgreSQL Database"]
        ORM["SQLAlchemy ORM<br/>BaseEntity"]
        Logger["Structured Logging<br/>Loguru + Structlog"]
        ErrorHandler["Error Handling<br/>Custom Exceptions"]
        Testing["Testing Infrastructure<br/>Fixtures, Factories"]
    end

    %% Connections
    API -->|authenticates| AuthModule
    WEB -->|calls| API
    
    API -->|routes to| FermDomain
    API -->|routes to| FruitDomain
    API -->|routes to| WineryDomain
    API -->|routes to| ProtocolDomain
    API -->|routes to| AnalysisDomain
    
    AuthModule --> User
    User -->|owns fermentations| FermDomain
    
    FermDomain --> FermService
    FermService --> FermRepo
    FermRepo --> DB
    
    FruitDomain --> FruitService
    FruitService --> FruitRepo
    FruitRepo --> DB
    
    WineryDomain --> WineryService
    WineryService --> WineryRepo
    WineryRepo --> DB
    
    ProtocolDomain --> ProtocolService
    ProtocolService --> ProtocolRepo
    ProtocolRepo --> DB
    
    AnalysisDomain --> AnalysisService
    AnalysisService --> AnalysisRepo
    AnalysisRepo --> DB
    
    HistDomain --> HistService
    HistService --> HistRepo
    HistRepo --> DB
    
    FermService -.->|compares with| HistService
    FermService -.->|tracked by| ProtocolService
    ProtocolService -.->|compliance score to| AnalysisService
    FermService -.->|triggers| AnalysisService
    
    FermDomain -->|uses| ORM
    FruitDomain -->|uses| ORM
    WineryDomain -->|uses| ORM
    ProtocolDomain -->|uses| ORM
    AnalysisDomain -->|uses| ORM
    HistDomain -->|uses| ORM
    
    FermService -->|logs| Logger
    ProtocolService -->|logs| Logger
    AnalysisService -->|logs| Logger
    FermService -->|handles| ErrorHandler
    ProtocolService -->|handles| ErrorHandler
    AnalysisService -->|handles| ErrorHandler
    
    Testing -->|supports all| Fermentation
    Testing -->|supports all| Analysis
    
    style User fill:#1976d2,color:#fff
    style Auth fill:#f57c00,color:#fff
    style Fermentation fill:#7b1fa2,color:#fff
    style FruitOrigin fill:#388e3c,color:#fff
    style Winery fill:#c2185b,color:#fff
    style Protocol fill:#2e7d32,color:#fff
    style Analysis fill:#0277bd,color:#fff
    style Historical fill:#f57f17,color:#fff
    style Shared fill:#424242,color:#fff
    style Analysis fill:#558b2f,color:#fff
    style Historical fill:#4a148c,color:#fff
    style Shared fill:#424242,color:#fff
```

---

## Module Dependencies

```mermaid
graph LR
    WEB["🖥️ Frontend"]
    API["🔌 API Layer"]
    
    subgraph Modules["Domain Modules"]
        AUTH["🔐 Auth<br/>(Shared)"]
        WINERY["🏪 Winery"]
        FRUIT["🌍 Fruit Origin"]
        FERM["🍇 Fermentation"]
        ANALYSIS["📊 Analysis Engine"]
        HIST["📚 Historical Data"]
    end
    
    DB["🗄️ PostgreSQL"]
    
    WEB --> API
    API --> AUTH
    API --> WINERY
    API --> FRUIT
    API --> FERM
    API --> ANALYSIS
    
    WINERY --> DB
    FRUIT --> DB
    FERM --> DB
    ANALYSIS --> DB
    HIST --> DB
    
    FERM -.->|references| FRUIT
    FERM -.->|references| AUTH
    ANALYSIS -.->|analyzes| FERM
    ANALYSIS -.->|compares with| HIST
    FERM -.->|triggered by| ANALYSIS
    
    style AUTH fill:#f57c00,color:#fff
    style WINERY fill:#c2185b,color:#fff
    style FRUIT fill:#388e3c,color:#fff
    style FERM fill:#7b1fa2,color:#fff
    style ANALYSIS fill:#558b2f,color:#fff
    style HIST fill:#4a148c,color:#fff
```

---

## Data Flow: New Measurement

```mermaid
sequenceDiagram
    actor User
    participant API
    participant FermService
    participant SampleService
    participant FermRepo
    participant SampleRepo
    participant DB
    participant AnalysisService
    
    User->>API: POST /fermentations/{id}/samples<br/>(new measurement)
    
    API->>FermService: create_sample(fermentation_id, data)
    
    FermService->>FermService: validate_sample_data()
    
    FermService->>FermRepo: get_fermentation(id, winery_id)
    FermRepo-->>DB: SELECT * FROM fermentations
    FermRepo-->>FermService: Fermentation entity
    
    FermService->>SampleService: create_sample(fermentation, data)
    
    SampleService->>SampleService: validate_value()<br/>validate_chronology()
    
    SampleService->>SampleRepo: add_sample(sample)
    SampleRepo-->>DB: INSERT INTO samples
    SampleRepo-->>SampleService: Sample entity
    
    SampleService-->>FermService: Sample entity
    FermService-->>API: Sample entity
    API-->>User: 200 Created
    
    Note over AnalysisService: Asynchronously triggered
    
    AnalysisService->>AnalysisService: analyze_fermentation(fermentation_id)
    AnalysisService->>FermRepo: get_samples(fermentation_id)
    FermRepo-->>DB: SELECT * FROM samples
    AnalysisService->>AnalysisService: detect_anomalies()
    AnalysisService->>AnalysisService: generate_recommendations()
```

---

## Clean Architecture Layers

```mermaid
graph TB
    subgraph Layer1["🎯 Domain Layer"]
        Entities["Entities<br/>(Fermentation, Sample,<br/>Analysis, etc.)"]
        Enums["Enums<br/>(Status, AnomalyType,<br/>SeverityLevel)"]
        Interfaces["Repository Interfaces<br/>(IFermentationRepository,<br/>ISampleRepository)"]
        Errors["Domain Errors<br/>(Custom Exceptions)"]
    end
    
    subgraph Layer2["🛠️ Infrastructure Layer"]
        Repositories["Repository Implementations<br/>(FermentationRepository,<br/>SampleRepository)"]
        ORM["ORM Mapping<br/>(SQLAlchemy)"]
        Database["Database<br/>(PostgreSQL)"]
    end
    
    subgraph Layer3["⚙️ Service Layer"]
        Services["Services<br/>(FermentationService,<br/>SampleService,<br/>ValidationOrchestrator)"]
        Validators["Validators<br/>(Value, Business Rule,<br/>Chronology)"]
    end
    
    subgraph Layer4["🔌 API/Presentation Layer"]
        Routers["Route Handlers<br/>(FastAPI Routers)"]
        Schemas["Request/Response DTOs<br/>(Pydantic)"]
        Middleware["Middleware<br/>(Auth, Error Handling)"]
    end
    
    Repositories -.->|implement| Interfaces
    ORM -.->|uses| Entities
    ORM -.->|maps to| Database
    
    Services -.->|depend on| Interfaces
    Services -.->|handle| Enums
    Services -.->|use| Errors
    
    Validators -.->|validate| Entities
    
    Routers -.->|call| Services
    Schemas -.->|serialize| Entities
    Middleware -.->|uses| Errors
    
    Layer4 -.->|depends on| Layer3
    Layer3 -.->|depends on| Layer2
    Layer2 -.->|implements| Layer1
    
    style Layer1 fill:#f57f17,color:#fff
    style Layer2 fill:#2e7d32,color:#fff
    style Layer3 fill:#0277bd,color:#fff
    style Layer4 fill:#d32f2f,color:#fff
```

---

## Multi-Tenancy Architecture

```mermaid
graph TB
    subgraph Tenant1["🏪 Winery A"]
        Auth1["User A<br/>winery_id=1"]
        Ferm1["Fermentations<br/>winery_id=1"]
        Hist1["Historical Data<br/>winery_id=1<br/>(Proprietary)"]
    end
    
    subgraph Tenant2["🏪 Winery B"]
        Auth2["User B<br/>winery_id=2"]
        Ferm2["Fermentations<br/>winery_id=2"]
        Hist2["Historical Data<br/>winery_id=2<br/>(Proprietary)"]
    end
    
    API["API Layer<br/>Security Check:<br/>Verify winery_id<br/>in JWT + path"]
    
    API -->|isolates| Tenant1
    API -->|isolates| Tenant2
    
    Auth1 -->|scope| Ferm1
    Auth1 -->|scope| Hist1
    
    Auth2 -->|scope| Ferm2
    Auth2 -->|scope| Hist2
    
    Ferm1 -.->|cannot access| Ferm2
    Ferm1 -.->|cannot access| Hist2
    Ferm2 -.->|cannot access| Ferm1
    Ferm2 -.->|cannot access| Hist1
    
    style Tenant1 fill:#1565c0,color:#fff
    style Tenant2 fill:#ad1457,color:#fff
```

---

## Status

| Component | Status | Phase |
|-----------|--------|-------|
| **General Architecture** | ✅ Complete | - |
| **Module Integration** | ✅ Complete | - |
| **Clean Architecture** | ✅ Complete | - |
| **Multi-Tenancy** | ✅ Complete | - |

