# Entity Relationship Diagram (Database)

This ER diagram is derived from the Alembic migrations in `alembic/versions/`.

## Full Relational ERD

```mermaid
erDiagram
    WINERIES {
        int id PK
        string code UK
        string name UK
    }

    USERS {
        int id PK
        int winery_id FK
        string username UK
        string email UK
        string role
    }

    VINEYARDS {
        int id PK
        int winery_id FK
        string code
        string name
    }

    VINEYARD_BLOCKS {
        int id PK
        int vineyard_id FK
        string code
    }

    HARVEST_LOTS {
        int id PK
        int winery_id FK
        int block_id FK
        string code
        date harvest_date
    }

    FERMENTATIONS {
        int id PK
        int fermented_by_user_id FK
        int winery_id FK
        string vessel_code
        string status
    }

    FERMENTATION_NOTES {
        int id PK
        int fermentation_id FK
        int created_by_user_id FK
    }

    FERMENTATION_LOT_SOURCES {
        int id PK
        int fermentation_id FK
        int harvest_lot_id FK
        float mass_used_kg
    }

    SAMPLES {
        int id PK
        int fermentation_id FK
        string sample_type
        datetime recorded_at
    }

    RECOMMENDATION_TEMPLATE {
        uuid id PK
        string code UK
        string category
    }

    ANALYSIS {
        uuid id PK
        uuid fermentation_id
        uuid winery_id
        string status
    }

    ANOMALY {
        uuid id PK
        uuid analysis_id FK
        uuid sample_id
        string anomaly_type
        string severity
    }

    RECOMMENDATION {
        uuid id PK
        uuid analysis_id FK
        uuid anomaly_id FK
        uuid recommendation_template_id FK
        int priority
    }

    FERMENTATION_PROTOCOLS {
        int id PK
        int winery_id
        int template_id FK
        string varietal_code
        string version
        string state
    }

    PROTOCOL_STEPS {
        int id PK
        int protocol_id FK
        int depends_on_step_id FK
        int step_order
        string step_type
    }

    PROTOCOL_EXECUTIONS {
        int id PK
        int protocol_id FK
        int fermentation_id
        int winery_id
        string status
    }

    STEP_COMPLETIONS {
        int id PK
        int execution_id FK
        int step_id FK
        bool was_skipped
    }

    PROTOCOL_ALERTS {
        int id PK
        int execution_id FK
        int protocol_id FK
        int step_id FK
        int winery_id
        string alert_type
        string status
    }

    PROTOCOL_ADVISORY {
        uuid id PK
        uuid fermentation_id
        uuid analysis_id
        uuid execution_id
        string advisory_type
        string risk_level
    }

    WINEMAKER_ACTIONS {
        int id PK
        int winery_id FK
        int fermentation_id FK
        int execution_id FK
        int step_id FK
        int alert_id FK
        int recommendation_id
        string action_type
        string outcome
    }

    WINERIES ||--o{ USERS : has
    WINERIES ||--o{ VINEYARDS : has
    WINERIES ||--o{ HARVEST_LOTS : has
    WINERIES ||--o{ FERMENTATIONS : has
    WINERIES ||--o{ WINEMAKER_ACTIONS : has

    VINEYARDS ||--o{ VINEYARD_BLOCKS : contains
    VINEYARD_BLOCKS ||--o{ HARVEST_LOTS : produces

    USERS ||--o{ FERMENTATIONS : fermented_by
    USERS ||--o{ FERMENTATION_NOTES : creates

    FERMENTATIONS ||--o{ SAMPLES : has
    FERMENTATIONS ||--o{ FERMENTATION_NOTES : has
    FERMENTATIONS ||--o{ FERMENTATION_LOT_SOURCES : sources

    HARVEST_LOTS ||--o{ FERMENTATION_LOT_SOURCES : contributes

    ANALYSIS ||--o{ ANOMALY : contains
    ANALYSIS ||--o{ RECOMMENDATION : suggests
    ANOMALY ||--o{ RECOMMENDATION : optional_context
    RECOMMENDATION_TEMPLATE ||--o{ RECOMMENDATION : template_for

    FERMENTATION_PROTOCOLS ||--o{ PROTOCOL_STEPS : defines
    FERMENTATION_PROTOCOLS ||--o{ PROTOCOL_EXECUTIONS : governs
    FERMENTATION_PROTOCOLS ||--o{ PROTOCOL_ALERTS : scoped_by
    FERMENTATION_PROTOCOLS ||--o{ FERMENTATION_PROTOCOLS : parent_template

    PROTOCOL_STEPS ||--o{ PROTOCOL_STEPS : depends_on
    PROTOCOL_STEPS ||--o{ STEP_COMPLETIONS : completed_as
    PROTOCOL_STEPS ||--o{ PROTOCOL_ALERTS : triggers
    PROTOCOL_STEPS ||--o{ WINEMAKER_ACTIONS : acted_on

    PROTOCOL_EXECUTIONS ||--o{ STEP_COMPLETIONS : tracks
    PROTOCOL_EXECUTIONS ||--o{ PROTOCOL_ALERTS : emits
    PROTOCOL_EXECUTIONS ||--o{ WINEMAKER_ACTIONS : context_for

    PROTOCOL_ALERTS ||--o{ WINEMAKER_ACTIONS : motivates
    FERMENTATIONS ||--o{ WINEMAKER_ACTIONS : receives_action
```

## Notes on Intentional Non-FK Links

Some references are intentionally stored without foreign key constraints to keep module boundaries independent (for example, analysis/protocol cross-module identifiers).

Important examples:

- `analysis.fermentation_id`, `analysis.winery_id`
- `anomaly.sample_id`
- `protocol_executions.fermentation_id`, `protocol_executions.winery_id`
- `protocol_advisory.fermentation_id`, `protocol_advisory.analysis_id`, `protocol_advisory.execution_id`
- `winemaker_actions.recommendation_id`
