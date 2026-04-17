# Wine Fermentation System - Project Structure Map

**Last Update:** April 2026
**Purpose:** Navigation map for project structure and implementation status

---

## 📁 Core Structure

```
wine-fermentation-system/
├── .ai-context/                              # ADRs and context
│   ├── adr/                                  # Architecture Decision Records
│   ├── ARCHITECTURAL_GUIDELINES.md
│   ├── PROJECT_STRUCTURE_MAP.md              # This file
│   └── collaboration-principles.md
│
├── src/
│   ├── shared/
│   │   ├── infra/                            # ✅ DB config, sessions, BaseRepository
│   │   ├── auth/                             # ✅ JWT auth, RBAC, UserRepository
│   │   ├── testing/unit/                     # ✅ MockSessionManagerBuilder, EntityFactory
│   │   └── testing/integration/              # ✅ TestSessionManager, entity builders
│   │
│   └── modules/
│       ├── fermentation/                     # 🍷 Fermentation + Protocol Engine
│       ├── fruit_origin/                     # 🍇 Vineyard → Block → HarvestLot
│       ├── winery/                           # 🏭 Winery CRUD
│       └── analysis_engine/                  # 🔬 Anomaly Detection + Recommendations
│
├── frontend/                                 # React/Next.js (separate repo context)
└── docs/                                     # UML diagrams, ETL architecture, specs
```

---

## 🎯 Implementation Status (April 2026)

### ✅ COMPLETE

| Module | Source Files | Test Files | Test Functions | Notes |
|--------|-------------|-----------|---------------|-------|
| **fermentation** | ~80 | 62 | ~700 | Full stack: domain→repo→service→API + Protocol Engine |
| **fruit_origin** | ~30 | 11 | ~150 | Full stack: Vineyard→Block→HarvestLot API |
| **winery** | ~20 | 5 | ~75 | Full stack |
| **shared/auth** | ~20 | 14 | ~160 | JWT, RBAC |
| **shared/infra** | ~15 | 4 | ~40 | DB, sessions, BaseRepository |
| **shared/testing** | ~15 | 8 | ~138 | Unit + integration test utilities |
| **analysis_engine** | 54 | ~13 | ~185 | Domain+Service+Repo+API complete; tests written Apr 2026 |
| **TOTAL** | **~234** | **~117** | **~1,450+** | |

### 📁 Placeholder (empty dirs)
- `src/modules/action-tracking/` — future module
- `src/modules/historical-data/` — merged into fermentation module
- `src/modules/frontend/` — docs only

---

## 🗄️ Database Schema

| Table | Module | Purpose |
|-------|--------|---------|
| `users` | shared/auth | User authentication |
| `wineries` | winery | Winery information |
| `vineyards` | fruit_origin | Vineyard top-level |
| `vineyard_blocks` | fruit_origin | Vineyard parcels |
| `harvest_lots` | fruit_origin | Harvested fruit |
| `fermentations` | fermentation | Fermentation process |
| `fermentation_lot_sources` | fermentation | Links fermentation → lots |
| `samples` | fermentation | Measurements (single-table inheritance) |
| `fermentation_notes` | fermentation | Log entries |
| `fermentation_protocols` | fermentation | Protocol templates |
| `protocol_steps` | fermentation | Protocol step definitions |
| `protocol_executions` | fermentation | Active protocol runs |
| `step_completions` | fermentation | Audit trail for steps |
| `winemaker_actions` | fermentation | Logged winemaker interventions |
| `protocol_alerts` | fermentation | System-generated alerts |
| `analysis` | analysis_engine | Analysis aggregate root |
| `anomaly` | analysis_engine | Detected anomalies |
| `recommendation` | analysis_engine | Actionable suggestions |
| `recommendation_template` | analysis_engine | Reusable suggestion templates |
| `protocol_advisory` | analysis_engine | Analysis→Protocol advisories |

---

## 🔗 Key ADRs

- **ADR-001/002/003**: Repository architecture
- **ADR-005**: Service layer interfaces
- **ADR-006**: API layer design
- **ADR-011/012**: Test infrastructure
- **ADR-019/030/031**: ETL Pipeline
- **ADR-025**: Multi-tenancy security
- **ADR-027**: Structured logging
- **ADR-029**: Data source field tracking
- **ADR-032/034**: Historical data API
- **ADR-035–040**: Protocol Compliance Engine
- **ADR-037**: Protocol↔Analysis integration

---

## 📝 Quick Navigation

| Need to work on... | Path |
|---|---|
| Domain entities | `src/modules/{module}/src/domain/entities/` |
| Repository interfaces | `src/modules/{module}/src/domain/repositories/` |
| Repository implementations | `src/modules/{module}/src/repository_component/repositories/` |
| Service interfaces | `src/modules/{module}/src/service_component/interfaces/` |
| Service implementations | `src/modules/{module}/src/service_component/services/` |
| API routers | `src/modules/{module}/src/api/routers/` |
| Tests | `src/modules/{module}/tests/` |
| ADRs | `.ai-context/adr/` |
| System context | `.ai-context/project-context.md` |
| Architecture guidelines | `.ai-context/ARCHITECTURAL_GUIDELINES.md` |
