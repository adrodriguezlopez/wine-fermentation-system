# ADR-019: ETL Pipeline Design for Historical Data

**Status:** ✅ Accepted & Implemented  
**Date:** 2025-12-30  
**Completed:** 2026-01-11  
**Authors:** System

> **📋 Context Files:**
> - [Architectural Guidelines](../ARCHITECTURAL_GUIDELINES.md)
> - [ADR-018: Historical Data Module Architecture](./ADR-018-historical-data-module.md)
> - [ADR-029: Data Source Field](./ADR-029-data-source-field-historical-tracking.md)
> - [ADR-027: Structured Logging](./ADR-027-structured-logging-observability.md)

---

## Context

Historical Data Module requires robust ETL pipeline to import historical fermentation data from Excel files provided by each winery. This data feeds the Analysis Engine as reference patterns.

**Challenges:**
- Each winery may have different Excel formats
- Data may have inconsistencies (missing dates, values out of range)
- Files can be large (thousands of fermentations)
- Need clear user feedback on progress and errors
- Re-imports must handle existing data without duplication

**Related decisions:**
- ADR-029 defines `data_source` field for tracking imported data
- ADR-018 defines overall Historical Data Module architecture
- ADR-027 defines structured logging for ETL process

---

## Decision

Implement ETL pipeline with 3-layer validation, best-effort import strategy, and downloadable error reports:

1. **Use pandas + openpyxl** for Excel read/write operations
2. **3-layer validation**: pre-validate schema, row-validate data, post-validate integrity
3. **Best-effort import**: Import valid rows even if some fail, provide detailed error report
4. **Excel error reports**: Auto-generate Excel with errors/warnings highlighted (red/yellow)
5. **Async processing**: FastAPI Background Tasks for non-blocking imports
6. **Upsert strategy**: Re-import updates existing data without duplication
7. **1 row = 1 sample**: Excel format where fermentation metadata repeats on each row
8. **Sample merging**: Match by measured_at date (update if exists, create if not)

---

## Implementation Notes

```
historical_data/
├── entities/
│   └── import_job.py          # ImportJob entity with status tracking
├── services/
│   ├── etl_service.py          # Main ETL orchestrator
│   ├── etl_validator.py        # 3-layer validation
│   └── error_report_generator.py  # Excel error report generation
├── api/
│   └── endpoints/
│       └── historical.py       # Import endpoints
└── tests/
    ├── fixtures/
    │   ├── valid_import.xlsx
    │   └── invalid_import.xlsx
    └── test_etl_service.py
```

**Component Responsibilities:**

**ETLService:**
- Orchestrate full import pipeline
- Group rows by fermentation_code using pandas groupby
- Transaction per fermentation (not all-or-nothing)
- Generate error reports when errors exist
- Update ImportJob status

**ETLValidator:**
- `pre_validate()`: Check file size, required columns, basic schema
- `row_validate()`: Validate dates, ranges, types, required fields
- `post_validate()`: Check chronological order, business rules, sample count

**ErrorReportGenerator:**
- Load original Excel with pandas
- Add 'Errors' and 'Warnings' columns
- Filter to problematic rows only
- Apply styling with openpyxl (red for errors, yellow for warnings)
- Save to temp location for download

**Upsert Logic:**
- Lookup existing: `winery_id + code + data_source=IMPORTED`
- If exists: UPDATE fermentation metadata + MERGE samples by measured_at
- If not exists: CREATE fermentation + harvest lot + samples
- Never duplicate data

---

## Architectural Considerations

> **Default:** Follows [Architectural Guidelines](../ARCHITECTURAL_GUIDELINES.md)

**Deviations:**
- **Pandas in-memory loading**: Loads entire Excel into RAM (trade-off: simplicity vs memory)
  - **Mitigation**: 50MB file size limit in pre-validation
  - **Future**: Implement chunked processing if needed
  
**Performance trade-offs:**
- **Best-effort over atomic**: Valid rows imported even if others fail
  - **Justification**: Better UX, no lost work
  - **Risk**: Partial state if process crashes mid-import
  - **Mitigation**: Transaction per fermentation + ImportJob tracking

**Technology constraints:**
- **Background Tasks vs Celery**: Using FastAPI Background Tasks for MVP
  - **Limitation**: Single-process, no distribution
  - **When to upgrade**: If imports are frequent or files > 50MB
  - **Migration path**: Switch to Celery without API changes

---

## Consequences

✅ **Benefits:**
- Robust validation catches errors early (fail fast)
- No data loss with best-effort strategy
- Downloadable Excel reports improve UX significantly
- Visual formatting (colors) makes errors obvious
- Idempotent re-imports (no duplicates)
- Async processing doesn't block API
- pandas + groupby is highly performant

⚠️ **Trade-offs:**
- Memory usage scales with file size (50MB limit mitigates)
- Background Tasks limits to single worker (Celery upgrade path exists)
- Error reports stored temporarily (cleanup job needed)

❌ **Accepted Limitations:**
- No distributed processing in MVP (acceptable for current scale)
- No real-time progress updates (job status polling only)
- No partial file resume (must re-upload if process dies)

---

## TDD Plan

**ETLValidator:**
- `pre_validate()` with missing columns → returns errors with column names
- `pre_validate()` with file > 50MB → returns size error
- `row_validate()` with invalid date format → returns date parsing error
- `row_validate()` with density out of range [0.9, 1.2] → returns range error
- `row_validate()` with harvest_date > fermentation_start → returns chronology error
- `post_validate()` with samples not in order → returns warning (not error)
- `post_validate()` with < 3 samples → returns warning about insufficient data

**ETLService:**
- `import_from_excel()` with all valid rows → success_count == total_rows
- `import_from_excel()` with partial errors → imports valid, returns errors list
- `import_from_excel()` with duplicate fermentation_code → updates existing
- `import_from_excel()` with inconsistent fermentation fields → returns validation error
- `import_from_excel()` generates error report when errors exist → report_path not None

**ErrorReportGenerator:**
- `generate_error_report()` → Excel contains only error rows
- `generate_error_report()` → Error rows styled with red fill
- `generate_error_report()` → Warning rows styled with yellow fill
- `generate_error_report()` → Adds 'Errors' and 'Warnings' columns

**Upsert Logic:**
- Import new fermentation → creates fermentation + harvest lot + samples
- Re-import same code → updates metadata, merges samples
- Re-import with new sample date → adds new sample
- Re-import with existing sample date → updates sample value

---

## Quick Reference

- ✅ **Library**: pandas + openpyxl (read/write Excel)
- ✅ **Validation**: 3 layers (pre/row/post)
- ✅ **Error handling**: Best-effort + detailed report
- ✅ **Error Excel**: Auto-generated, color-coded (red/yellow)
- ✅ **Async**: FastAPI Background Tasks (upgrade to Celery if needed)
- ✅ **Format**: 1 row = 1 sample, fermentation metadata repeats
- ✅ **Re-import**: Upsert by winery_id + code + data_source
- ✅ **Performance**: 1K rows < 30s, 10K rows < 5min
- ✅ **Memory**: < 500MB per import
- ✅ **Success rate**: 95%+ valid rows imported

---

## API Examples

```python
# 1. Start import
POST /api/v1/historical/import
Content-Type: multipart/form-data

Response:
{
    "job_id": "uuid",
    "status": "processing",
    "message": "Import started. Use job_id to check progress."
}

# 2. Check status
GET /api/v1/historical/import/{job_id}

Response:
{
    "job_id": "uuid",
    "status": "PARTIAL_SUCCESS",  # PENDING, PROCESSING, SUCCESS, PARTIAL_SUCCESS, FAILED
    "filename": "historical_data.xlsx",
    "total_rows": 1000,
    "success_count": 950,
    "error_count": 50,
    "warning_count": 5,
    "has_error_report": true,
    "completed_at": "2025-12-30T10:30:00Z"
}

# 3. Download error report (if has_error_report: true)
GET /api/v1/historical/import/{job_id}/error-report

Response: Excel file download with:
- Only rows that had errors/warnings
- 'Errors' column with error messages (rows highlighted red)
- 'Warnings' column with warning messages (rows highlighted yellow)

# 4. Download template
GET /api/v1/historical/template

Response: Excel template with:
- Required columns with proper headers
- Example rows showing expected format
- Data validation rules (dates, ranges)
```

**Excel Format:**

```
Required Columns:
- fermentation_code: Unique identifier per fermentation
- fermentation_start_date: Date fermentation started
- fermentation_end_date: Date fermentation ended (NULL if ongoing)
- harvest_date: Date grapes were harvested
- vineyard_name: Name of vineyard (will lookup or create)
- grape_variety: Grape variety
- harvest_mass_kg: Mass harvested in kg
- sample_date: Date this sample was taken (unique per fermentation)
- density: Density in g/mL (range: 0.9-1.2)
- temperature_celsius: Temperature in °C (range: 0-40)
- sugar_brix: Sugar in Brix (optional, range: 0-30)

Example:
fermentation_code | fermentation_start | harvest_date | vineyard | grape | harvest_kg | sample_date | density | temp | sugar
F2023-001        | 2023-03-15         | 2023-03-14   | Block A  | CS    | 500        | 2023-03-16  | 1.090   | 18   | 24.5
F2023-001        | 2023-03-15         | 2023-03-14   | Block A  | CS    | 500        | 2023-03-17  | 1.085   | 19   | 22.1
F2023-001        | 2023-03-15         | 2023-03-14   | Block A  | CS    | 500        | 2023-03-18  | 1.080   | 20   | 19.8
```

**Validation Examples:**

```python
# Pre-validation (schema check)
class ETLValidator:
    async def pre_validate(self, file_path: Path) -> PreValidationResult:
        # Check file size
        if file_path.stat().st_size > 50 * 1024 * 1024:
            return PreValidationResult(
                is_valid=False,
                errors=["File too large. Maximum 50MB allowed."]
            )
        
        # Check required columns
        df = pd.read_excel(file_path, nrows=0)
        required = {'fermentation_code', 'fermentation_start_date', 'harvest_date', ...}
        missing = required - set(df.columns)
        
        if missing:
            return PreValidationResult(
                is_valid=False,
                errors=[f"Missing required columns: {missing}"]
            )
        
        return PreValidationResult(is_valid=True)

# Row-validation (data check)
    async def row_validate(self, row: pd.Series) -> RowValidationResult:
        errors = []
        
        # Date chronology
        if row['harvest_date'] > row['fermentation_start_date']:
            errors.append("harvest_date must be before fermentation_start_date")
        
        # Value ranges
        if not (0.9 <= row['density'] <= 1.2):
            errors.append(f"density {row['density']} out of range [0.9, 1.2]")
        
        if not (0 <= row['temperature_celsius'] <= 40):
            errors.append(f"temperature {row['temperature_celsius']} out of range [0, 40]")
        
        return RowValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
```

**Error Report Generation:**

```python
class ErrorReportGenerator:
    async def generate_error_report(
        self,
        original_file: Path,
        errors: List[RowError],
        warnings: List[RowWarning]
    ) -> Path:
        # Load original data
        df = pd.read_excel(original_file, engine='openpyxl')
        
        # Add error/warning columns
        df['Errors'] = ''
        df['Warnings'] = ''
        
        # Fill messages
        for error in errors:
            row_idx = error.row - 2  # Convert Excel row to DataFrame index
            if 0 <= row_idx < len(df):
                df.at[row_idx, 'Errors'] = error.error
        
        for warning in warnings:
            row_idx = warning.row - 2
            if 0 <= row_idx < len(df):
                df.at[row_idx, 'Warnings'] = warning.warning
        
        # Filter to only problematic rows
        df_filtered = df[(df['Errors'] != '') | (df['Warnings'] != '')]
        
        # Write with styling
        output_file = Path(f"/tmp/error_report_{uuid4()}.xlsx")
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df_filtered.to_excel(writer, index=False, sheet_name='Errors')
            
            # Apply styling
            worksheet = writer.sheets['Errors']
            from openpyxl.styles import PatternFill
            
            red_fill = PatternFill(start_color='FFCCCC', end_color='FFCCCC', fill_type='solid')
            yellow_fill = PatternFill(start_color='FFFFCC', end_color='FFFFCC', fill_type='solid')
            
            for idx, row in enumerate(worksheet.iter_rows(min_row=2, max_row=len(df_filtered)+1)):
                if df_filtered.iloc[idx]['Errors']:
                    for cell in row:
                        cell.fill = red_fill
                elif df_filtered.iloc[idx]['Warnings']:
                    for cell in row:
                        cell.fill = yellow_fill
        
        return output_file
```

---

## Error Catalog

**ETL Service Errors:**
- `FileToLargeError` → User notified with file size limit
- `InvalidSchemaError` → User notified with missing columns
- `ValidationError` → Included in error report Excel

**Domain Errors:**
- `FermentationNotFoundError` → When updating non-existent fermentation (shouldn't happen with upsert)
- `WineryNotFoundError` → If winery_id doesn't exist in DB

**Infrastructure Errors:**
- `DatabaseError` → Retry transaction, log error, mark ImportJob as FAILED
- `FileSystemError` → Log error, notify user, cleanup temp files

---

## Acceptance Criteria

- [ ] Pre-validation rejects files > 50MB with clear error message
- [ ] Pre-validation rejects files missing required columns with column names
- [ ] Row validation detects all out-of-range values (dates, density, temperature)
- [ ] Row validation detects chronology errors (harvest > fermentation)
- [ ] Post-validation warns about insufficient samples (< 3)
- [ ] Best-effort import: 950/1000 valid rows imported when 50 have errors
- [ ] Error report Excel generated automatically when errors exist
- [ ] Error report contains only problematic rows (not all 1000)
- [ ] Error rows highlighted in red, warning rows in yellow
- [ ] Error report downloadable via GET /import/{job_id}/error-report
- [ ] Upsert strategy: re-importing same code updates without duplicating
- [ ] Sample merge: re-importing same sample_date updates value
- [ ] Sample merge: re-importing new sample_date creates new sample
- [ ] ImportJob status accurately reflects PENDING/PROCESSING/SUCCESS/PARTIAL_SUCCESS/FAILED
- [ ] Performance: 1000 rows processed in < 30 seconds
- [ ] Performance: 10000 rows processed in < 5 minutes
- [ ] Memory: Import process uses < 500MB RAM
- [ ] Logging: All ETL stages logged with structured logging (ADR-027)
- [ ] Template Excel downloadable via GET /historical/template

---

## Status

✅ **Accepted & Implemented** (2025-12-30 → 2026-01-11)

### Implementation Summary

**Core Components:**
- ✅ **ETLService**: Full implementation with FruitOriginService integration (ADR-030)
- ✅ **ETLValidator**: 3-layer validation (pre-validate, row-validate, post-validate)
- ✅ **CancellationToken**: Thread-safe cancellation mechanism
- ✅ **ImportResult**: Comprehensive result tracking with error details

**Key Features Implemented:**
1. **Excel Import Pipeline**: pandas + openpyxl for read/write operations
2. **3-Layer Validation**:
   - Pre-validation: File size, required columns, data types
   - Row validation: Value ranges, chronology, data integrity
   - Post-validation: Integrity checks, business rules
3. **Partial Success**: Per-fermentation transactions (ADR-031)
4. **Progress Tracking**: Async callback support for UI updates
5. **Cancellation Support**: Graceful stop with partial data preserved
6. **Performance Optimizations** (ADR-030):
   - Batch vineyard loading (N+1 query elimination)
   - Shared default VineyardBlock (99% reduction in blocks)
   - Per-fermentation atomicity with partial success

**Test Coverage:**
- ✅ 21 unit tests (ETL service, validator, error handling)
- ✅ 12 integration tests (6 functional + 6 performance benchmarks)
- ✅ 983 total tests passing across full system

**Performance Validated:**
- ✅ 100 fermentations imported in ~4.75 seconds
- ✅ N+1 query elimination confirmed (1 batch query vs 100 individual)
- ✅ Shared default block optimization (100 fermentations → 1 block)
- ✅ Progress tracking overhead < 10%
- ✅ Cancellation with partial success working

**Dependencies:**
- ADR-030: ETL Cross-Module Architecture ✅
- ADR-031: Transaction Coordination Pattern ✅
- ADR-029: Data Source Field ✅
- ADR-027: Structured Logging ✅

---

## Related Documentation

- [ADR-030: ETL Cross-Module Architecture](./ADR-030-etl-cross-module-architecture-refactoring.md)
- [ADR-031: Transaction Coordination](./ADR-031-cross-module-transaction-coordination.md)
- [ADR-029: Data Source Field](./ADR-029-data-source-field-historical-tracking.md)
