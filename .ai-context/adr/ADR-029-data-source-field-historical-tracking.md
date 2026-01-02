# ADR-029: Data Source Field for Historical Data Tracking

**Status:** Accepted  
**Date:** 2025-12-30  
**Authors:** System

> **📋 Context Files:**
> - [Architectural Guidelines](../ARCHITECTURAL_GUIDELINES.md)
> - [ADR-018: Historical Data Module Architecture](./ADR-018-historical-data-module.md)
> - [ADR-019: ETL Pipeline Design](./ADR-019-etl-pipeline-historical-data.md)

---

## Context

During Historical Data Module design (ADR-018), an important architectural decision emerged: how to distinguish fermentations created by the system from those imported from historical Excel data.

**Original proposal:** Create separate `HistoricalFermentation` and `HistoricalSample` entities, duplicating existing entities.

**Problem identified:**
- Massive code duplication (entities, repositories, services)
- Complex queries when combining both sources
- Maintenance burden (changes must be applied twice)
- Violation of DRY principle

**Alternative proposed:** Reuse existing `Fermentation` and `Sample` entities, adding a `data_source` field to distinguish data origin.

---

## Decision

Add `data_source` field to `Fermentation` and `Sample` entities instead of creating separate historical entities:

1. **Add enum field `data_source`** with values: SYSTEM, IMPORTED, MIGRATED
2. **Add indexed column** for query performance
3. **Add `imported_at` timestamp** for import tracking (nullable)
4. **Default value SYSTEM** for backward compatibility
5. **Reuse existing entities** (no HistoricalFermentation duplication)

---

## Implementation Notes

```
fermentation/
├── entities/
│   ├── fermentation.py        # Add data_source + imported_at fields
│   └── samples/
│       └── base_sample.py     # Add data_source + imported_at fields
├── domain/
│   └── enums.py               # DataSource enum
└── repositories/
    ├── fermentation_repository.py  # Add list_by_data_source()
    └── sample_repository.py        # Add list_by_data_source()
```

**Entity changes:**

```python
# domain/enums.py
class DataSource(str, Enum):
    SYSTEM = "system"      # Created through API operations
    IMPORTED = "imported"  # Imported from historical Excel
    MIGRATED = "migrated"  # Future: migrated from legacy systems

# entities/fermentation.py
class Fermentation:
    # ... existing fields ...
    
    data_source: Mapped[str] = mapped_column(
        String(20), 
        nullable=False, 
        default=DataSource.SYSTEM.value,
        index=True  # Query performance
    )
    
    imported_at: Mapped[datetime] = mapped_column(
        nullable=True,
        comment="Timestamp when data was imported"
    )
```

**Repository additions:**

```python
class FermentationRepository:
    async def list_by_data_source(
        self, 
        winery_id: UUID,
        data_source: DataSource
    ) -> List[Fermentation]:
        """Filter fermentations by data source"""
        pass
```

---

## Architectural Considerations

> **Default:** Follows [Architectural Guidelines](../ARCHITECTURAL_GUIDELINES.md)

**Alternative patterns considered:**

1. **Separate tables (HistoricalFermentation)**
   - **Rejected:** Massive duplication, complex queries
   
2. **Boolean is_historical field**
   - **Rejected:** Not extensible (only 2 values, no future sources)
   
3. **No field at all (YAGNI)**
   - **Rejected:** Loses auditing capability, debugging becomes harder

**Performance trade-offs:**
- **Cost:** 20 bytes per record + index storage
- **Benefit:** Fast filtering queries, clear audit trail
- **Trade-off:** Accepted (minimal cost, significant value)

---

## Consequences

✅ **Benefits:**
- Single entity hierarchy (no duplication)
- Unified queries with easy filtering
- Extensible for future data sources
- Clear audit trail for data origin
- Backward compatible (default value)
- Index enables fast queries by source

⚠️ **Trade-offs:**
- 20 bytes overhead per record (minimal)
- Need migration for existing data (automatic with default)
- Tests must cover all data sources

❌ **Accepted Limitations:**
- Field can't be changed after creation (by design)
- Requires discipline to set correctly in ETL

---

## TDD Plan

**Repository:**
- `list_by_data_source(SYSTEM)` → returns only system-created fermentations
- `list_by_data_source(IMPORTED)` → returns only imported fermentations
- `list()` with no filter → returns all fermentations (default behavior)

**Entity:**
- New Fermentation without data_source → defaults to SYSTEM
- New Fermentation with data_source=IMPORTED → imported_at required
- Query with index on data_source → < 50ms for 10K records

**ETL:**
- Import fermentation → sets data_source=IMPORTED + imported_at=now()
- Re-import fermentation → preserves original data_source + updates imported_at

---

## Quick Reference

- ✅ **Field**: `data_source: Mapped[str]` (String(20), indexed, default='system')
- ✅ **Enum**: DataSource.SYSTEM, IMPORTED, MIGRATED
- ✅ **Timestamp**: `imported_at: Mapped[datetime]` (nullable)
- ✅ **Benefits**: Auditing, debugging, UI differentiation, future-proofing
- ✅ **Cost**: 20 bytes per record
- ✅ **Performance**: Indexed for fast queries
- ✅ **Migration**: Automatic with default value

---

## API Examples

```python
# DTOs include data_source
class FermentationResponse(BaseModel):
    id: UUID
    code: str
    # ... existing fields ...
    data_source: DataSource
    imported_at: datetime | None = None

# API responses show data source
GET /api/v1/fermentations/{id}
{
    "id": "uuid",
    "code": "F2023-001",
    "data_source": "imported",
    "imported_at": "2023-03-15T10:30:00Z",
    ...
}

# Repository queries
# Get only system-created
fermentations = await repo.list_by_data_source(
    winery_id=winery_id,
    data_source=DataSource.SYSTEM
)

# Get only imported historical data
historical = await repo.list_by_data_source(
    winery_id=winery_id,
    data_source=DataSource.IMPORTED
)

# Get all (default)
all_fermentations = await repo.list(winery_id=winery_id)
```

---

## Error Catalog

N/A - This is a data field addition, no new error types introduced.

---

## Acceptance Criteria

- [ ] Migration adds data_source column with default 'system'
- [ ] Migration adds imported_at column (nullable)
- [ ] Migration creates index on data_source
- [ ] Existing fermentations get data_source='system' automatically
- [ ] New fermentations default to data_source='system'
- [ ] ETL sets data_source='imported' when importing
- [ ] ETL sets imported_at timestamp when importing
- [ ] Repository list_by_data_source() filters correctly
- [ ] Query by data_source uses index (< 50ms for 10K records)
- [ ] DTOs include data_source in responses
- [ ] UI shows badge/indicator for imported data
- [ ] All tests pass with new field

---

## Status

Accepted
