# UML Diagrams - Complete System Architecture

> **Purpose**: Comprehensive visual documentation of the Wine Fermentation Monitoring System using Mermaid diagrams.

## 🎬 How to View Diagrams

**New to this documentation?** 👉 [**Click here for viewing instructions**](HOWTO-VIEW-DIAGRAMS.md)

Quick summary:
- **VS Code**: Press `Ctrl+Shift+V` to see preview
- **GitHub**: Diagrams render automatically
- **Online**: Use https://mermaid.live for instant preview

---

## 📚 Quick Navigation

| Diagram | File | Purpose |
|---------|------|---------|
| **How to View** | [HOWTO-VIEW-DIAGRAMS.md](HOWTO-VIEW-DIAGRAMS.md) | Instructions for viewing Mermaid diagrams in different tools |
| **General Architecture** | [01-GENERAL-ARCHITECTURE.md](01-GENERAL-ARCHITECTURE.md) | System-level overview, module dependencies, clean architecture layers, multi-tenancy |
| **Component Diagrams** | [02-COMPONENTS.md](02-COMPONENTS.md) | Detailed component relationships (Fermentation, **Analysis Engine**, **Protocol Compliance Engine**, Fruit Origin, Auth modules) |
| **Class Diagrams** | [03-CLASS-DIAGRAMS.md](03-CLASS-DIAGRAMS.md) | **REORGANIZED**: Entities, interfaces, services separated by component (Fermentation, Analysis, Fruit, Auth, Winery) |
| **Sequence Diagrams** | [04-SEQUENCE-DIAGRAMS.md](04-SEQUENCE-DIAGRAMS.md) | Workflow interactions (Create fermentation, Add sample, Analysis, Login, etc.) |
| **Use Case Diagrams** | [05-USE-CASES.md](05-USE-CASES.md) | User interactions and system behaviors (UC-001 through UC-012) |
| **Deployment & Infrastructure** | [06-DEPLOYMENT-INFRASTRUCTURE.md](06-DEPLOYMENT-INFRASTRUCTURE.md) | System deployment, data flow, CI/CD pipeline, database schema |

---

## 🎯 Diagrams by Type

### System Architecture
- ✅ High-level system overview
- ✅ Module dependencies and relationships
- ✅ Clean architecture layers (Domain, Service, Repository, API)
- ✅ Multi-tenancy architecture
- **File**: [01-GENERAL-ARCHITECTURE.md](01-GENERAL-ARCHITECTURE.md)

### Component Architecture
- ✅ Fermentation Module components (Domain, Repository, Service, API)
- ✅ Analysis Engine components (Domain, Repository, Service, API)
- ✅ Fruit Origin Module components
- ✅ Authentication Module components
- ✅ Test fixtures and integration points
- **File**: [02-COMPONENTS.md](02-COMPONENTS.md)

### Class & Type Diagrams (Reorganized per Module)
- ✅ **Fermentation Module**: 6 entities, 2 enums, 2 interfaces
- ✅ **Analysis Engine Module**: 4 entities, 3 value objects, 3 enums, 4 interfaces
- ✅ **Fruit Origin Module**: 4 entities, 3 enums, 2 interfaces
- ✅ **Authentication Module**: 1 entity, 1 enum, 7 DTOs, 1 interface
- ✅ **Winery Module**: 1 entity, 2 value objects, 3 DTOs, 1 interface
- **File**: [03-CLASS-DIAGRAMS.md](03-CLASS-DIAGRAMS.md)
- ✅ Soft Delete workflow
- **File**: [04-SEQUENCE-DIAGRAMS.md](04-SEQUENCE-DIAGRAMS.md)

### Use Cases
- ✅ Fermentation Management (UC-001 to UC-005)
- ✅ Analysis & Recommendations (UC-006 to UC-009)
- ✅ Historical Insights (UC-010 to UC-012)
- ✅ Error scenarios and recovery
- ✅ Preconditions and postconditions
- **File**: [05-USE-CASES.md](05-USE-CASES.md)

### Deployment & Infrastructure
- ✅ Cloud deployment architecture (AWS/Azure/DigitalOcean)
- ✅ On-premise deployment option
- ✅ Module interaction & data flow
- ✅ Database schema architecture
- ✅ Docker Compose infrastructure
- ✅ CI/CD pipeline (GitHub Actions)
- **File**: [06-DEPLOYMENT-INFRASTRUCTURE.md](06-DEPLOYMENT-INFRASTRUCTURE.md)

---

## 🏗️ Architecture by Module

### 🔐 Authentication Module
**Status**: ✅ Complete  
**Diagrams**:
- General Architecture: [System Overview](01-GENERAL-ARCHITECTURE.md#system-architecture-high-level)
- Components: [Auth Module Components](02-COMPONENTS.md#authentication-module-components)
- Classes: [Auth Class Diagram](03-CLASS-DIAGRAMS.md#authentication-module---class-diagram)
- Sequence: [Login Workflow](04-SEQUENCE-DIAGRAMS.md#user-login-sequence)
- Use Cases: [UC-016, UC-017, UC-018](05-USE-CASES.md#authentication)

### 🍇 Fermentation Module
**Status**: ✅ Complete (Domain + Service + API + Tests)  
**Diagrams**:
- General Architecture: [System Overview](01-GENERAL-ARCHITECTURE.md#system-architecture-high-level)
- Components: [Fermentation Components](02-COMPONENTS.md#fermentation-module-components)
- Classes: [Fermentation Class Diagram](03-CLASS-DIAGRAMS.md#fermentation-module---class-diagram)
- Sequences: 
  - [Create Fermentation](04-SEQUENCE-DIAGRAMS.md#create-fermentation-sequence)
  - [Add Sample](04-SEQUENCE-DIAGRAMS.md#add-sample-to-fermentation-sequence)
- Use Cases:
  - [UC-001: Create Fermentation](05-USE-CASES.md#uc-001-create-fermentation)
  - [UC-002: Record Sample](05-USE-CASES.md#uc-002-record-daily-sample)

### 📊 Analysis Engine
**Status**: 🔄 Phase 1 Complete (Domain + Repository); Phases 2-5 Pending  
**Diagrams**:
- General Architecture: [System Overview](01-GENERAL-ARCHITECTURE.md#system-architecture-high-level)
- Components: [Analysis Engine Components](02-COMPONENTS.md#analysis-engine-components)
- Classes: [Analysis Class Diagram](03-CLASS-DIAGRAMS.md#analysis-engine---class-diagram)
- Sequence: [Fermentation Analysis Workflow](04-SEQUENCE-DIAGRAMS.md#fermentation-analysis-sequence)
- Use Cases:
  - [UC-006: Trigger Analysis](05-USE-CASES.md#uc-006-trigger-analysis)
  - [UC-007: View Anomalies](05-USE-CASES.md#uc-007-view-detected-anomalies)
  - [UC-008: Get Recommendations](05-USE-CASES.md#uc-008-get-recommendations)

### 🌍 Fruit Origin Module
**Status**: ✅ Complete (Domain + Service + API + Tests)  
**Diagrams**:
- General Architecture: [Module Relationships](01-GENERAL-ARCHITECTURE.md#module-dependencies)
- Components: [Fruit Origin Components](02-COMPONENTS.md#fruit-origin-module-components)
- Classes: [Fruit Origin Class Diagram](03-CLASS-DIAGRAMS.md#fruit-origin-module---class-diagram)
- Use Cases: [UC-013 to UC-015](05-USE-CASES.md#vineyard--admin)

### 🏪 Winery Module
**Status**: ✅ Complete (Domain + Service + API + Tests)  
**Diagrams**:
- General Architecture: [System Overview](01-GENERAL-ARCHITECTURE.md#system-architecture-high-level)
- Use Cases: Multi-tenancy root context

---

## 📊 Data Models

### Fermentation Domain
```
Fermentation (Root Aggregate)
├── BaseSample (composition)
│   ├── SugarSample
│   ├── DensitySample
│   └── CelsiusSample
├── FermentationNote (composition)
└── FermentationLotSource (reference to HarvestLot)
```

### Analysis Domain
```
Analysis (Root Aggregate)
├── Anomaly (composition)
│   ├── type: AnomalyType (enum)
│   └── severity: SeverityLevel (enum)
└── Recommendation (composition)
    ├── category: RecommendationCategory (enum)
    └── confidence: float
```

### Multi-Tenancy
```
Winery (Root Aggregate)
├── Users (owned)
├── Vineyards (owned)
├── HarvestLots (owned)
├── Fermentations (owned)
├── HistoricalSamples (owned)
└── RecommendationTemplates (owned)

Security: winery_id enforced at all layers
```

---

## 🔄 Key Workflows

### Fermentation Creation & Analysis
1. **User creates fermentation** (UC-001)
   - Validation at API layer
   - Domain validation
   - Persistence via repository
   - Multi-tenancy check via winery_id

2. **User records sample** (UC-002)
   - Value range validation
   - Chronology validation
   - Business rule validation
   - Async analysis trigger

3. **System runs analysis** (UC-006)
   - Load historical patterns
   - Run anomaly detection (4 algorithms)
   - Generate recommendations (template-based)
   - Calculate confidence scores
   - Persist results

---

## 🧪 Testing Coverage

| Module | Unit Tests | Integration Tests | Total |
|--------|------------|-------------------|-------|
| **Fermentation** | 234 | 49 | 283 |
| **Analysis Engine** | 44 | - | 44 |
| **Fruit Origin** | - | 177 | 177 |
| **Winery** | 44 | 35 | 79 |
| **Authentication** | 159 | 24 | 183 |
| **Shared Infrastructure** | - | 52 | 52 |
| **TOTAL** | 481 | 337 | **1,158** |

---

## 🔐 Security Considerations

### Multi-Tenancy
- ✅ Winery ID scoping at all layers
- ✅ JWT token validation on every request
- ✅ Security by obscurity (404 for unauthorized access)
- ✅ User role-based permissions (ADMIN, WINEMAKER, OPERATOR, VIEWER)

### Data Isolation
- ✅ Each winery's historical data remains proprietary
- ✅ No cross-winery data leakage
- ✅ Soft delete allows recovery without exposing deleted data

### Authentication
- ✅ Password hashing (bcrypt)
- ✅ JWT token pairs (access + refresh)
- ✅ Token expiration (15 min access, 7 day refresh)
- ✅ Session timeout

---

## 🚀 Scalability

### Horizontal Scaling
- ✅ Stateless API servers (can run multiple instances)
- ✅ Database replication (primary + replica)
- ✅ Redis caching for session management
- ✅ Load balancer distribution

### Asynchronous Processing
- ✅ Background analysis jobs via Celery
- ✅ Non-blocking API responses
- ✅ Message queue (RabbitMQ) for job distribution
- ✅ Multiple worker processes

### Monitoring & Observability
- ✅ Structured logging (Loguru + Structlog)
- ✅ Metrics collection (Prometheus)
- ✅ Dashboard visualization (Grafana)
- ✅ Error tracking (Sentry)

---

## 📈 System Capacity

**MVP Target**:
- 5-20 simultaneous fermentations per winery
- 2-5 winemakers per winery
- 50-100 measurements per fermentation
- 2-4 week fermentation periods
- Real-time anomaly detection (within minutes)

**Scaling Capability**:
- Can handle 100+ fermentations with horizontal scaling
- Database replication supports read-heavy workloads
- Cache layer reduces DB pressure
- Async processing prevents API bottlenecks

---

## 📋 Diagram Maintenance

### When to Update
- ✅ Adding new modules
- ✅ Changing API contracts
- ✅ Modifying database schema
- ✅ Updating deployment infrastructure
- ✅ Adding new use cases

### How to Update
1. Edit the relevant Markdown file
2. Update Mermaid diagrams
3. Update status tables
4. Validate diagram rendering in GitHub/IDE
5. Commit changes with descriptive message

---

## 🔗 Related Documentation

- [Project Context](../../.ai-context/project-context.md) - System overview
- [Architectural Guidelines](../../.ai-context/ARCHITECTURAL_GUIDELINES.md) - Design principles
- [ADR Index](../../.ai-context/adr/ADR-INDEX.md) - Architecture decision records
- [Module Contexts](../../src/modules/) - Per-module documentation

---

## ✅ Diagram Status Summary

| Diagram Type | Status | Coverage |
|------|--------|----------|
| **General Architecture** | ✅ Complete | 100% |
| **Components** | ✅ Complete | 100% (4 modules) |
| **Classes** | ✅ Complete | 100% (4 modules) |
| **Sequences** | ✅ Complete | 100% (7 workflows) |
| **Use Cases** | ✅ Complete | 100% (12 use cases) |
| **Deployment** | ✅ Complete | 100% |

---

**Last Updated**: February 6, 2026  
**System Status**: MVP Phase (Core functionality complete, Analysis Engine Phase 2-5 pending)  
**Total Diagrams**: 30+ Mermaid diagrams  
**Documentation Pages**: 6

