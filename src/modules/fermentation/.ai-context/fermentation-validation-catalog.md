# Fermentation Validation Catalog: Implemented vs. Missing

---

## 1. Implemented Validations (as of code analysis)

### Value/Range Validations
- `ValueValidationService.validate_sample_value`: Checks for None, empty string, valid number, and supported sample type. Converts to float and fails if not possible.
- `ValueValidationService.validate_numeric_value`: (Interface present) Numeric bounds validation, but actual min/max logic not shown in code excerpt.

### Business Rule Validations
- `BusinessRuleValidationService.validate_sugar_trend`: Ensures sugar (Brix) does not increase (current ≤ previous + tolerance). Uses repository to fetch previous value.
- `BusinessRuleValidationService.validate_temperature_range`: (Signature present) Checks temperature is within allowed range (details not shown in code excerpt).

### Chronological Validations
- `ChronologyValidationService.validate_sample_chronology`: Ensures sample type and timestamp are present. (Full ordering logic not shown in code excerpt.)
- `ChronologyValidationService.validate_fermentation_timeline`: (Signature present) Should check sample is after fermentation start (implementation not shown).

### Data Integrity
- `BaseSample`: Model constraint for required fields (value, units, user, fermentation, sample_type, recorded_at). Soft delete via `is_deleted` flag.
- Uniqueness and ordering constraints are implied in service logic, not enforced at DB/model level in code excerpts.

### Validation Result Structure
- All validation services return a `ValidationResult` object, which can contain errors and warnings (with field, message, value context).

---

## 2. Validation Gaps / TODOs / Not Yet Implemented

- No explicit scientific parameter ranges (e.g., Brix 0–40, Temp 10–35°C) are enforced in the code excerpts—only generic numeric validation is present.
- No Pydantic `@validator` decorators or model-level validation logic found in schemas/entities.
- No explicit minimum interval between samples or sample frequency rules implemented.
- No cross-parameter validation (e.g., density and sugar correlation) implemented.
- No explicit status transition rules or stage-specific validation logic found.
- No database-level uniqueness constraints for (fermentation_id, sample_type, recorded_at) in model code.
- No user permission checks (e.g., is_active, is_verified) in validation services.
- Some service interfaces have method signatures but lack full implementation in code excerpts (e.g., temperature range, chronology ordering).
- No evidence of warning/info-only validations—most logic is critical/failure.
- No comments or TODOs about missing validations found in code excerpts.

---

## 3. Current Validation Structure & Patterns

- **Service-based pattern:** All validations are implemented as service classes (`ValueValidationService`, `BusinessRuleValidationService`, `ChronologyValidationService`).
- **Interface-driven:** Each service implements an interface (e.g., `IValueValidationService`).
- **ValidationResult:** All validation returns are structured, supporting errors and warnings.
- **Repository dependency:** Business and chronology validations depend on repository access for historical/contextual checks.
- **Model constraints:** Required fields and soft delete are enforced at the ORM/entity level.

### What is missing?
- Model-level (Pydantic/SQLAlchemy) constraints for scientific ranges and uniqueness.
- Full implementation of all interface methods (some are stubs or partial).
- Explicit warning/info-level validations.
- Cross-field and stage-specific rules.
- User permission and status checks in validation logic.

---

## 4. Recommended Scientific Ranges (Based on Industry Research)

### Configurable Validation Parameters Architecture

**Implementation Strategy**: Create configurable validation parameters that can be customized per winery/operation:

```python
# Configuration-based validation ranges (should be externalized)
class WineryValidationConfig:
    def __init__(self, config_source: dict):
        self.brix_ranges = config_source.get("brix_ranges", DEFAULT_BRIX_RANGES)
        self.temperature_ranges = config_source.get("temperature_ranges", DEFAULT_TEMP_RANGES)
        self.timing_rules = config_source.get("timing_rules", DEFAULT_TIMING_RULES)
        self.density_ranges = config_source.get("density_ranges", DEFAULT_DENSITY_RANGES)

# Default ranges based on scientific research (fallback values)
DEFAULT_BRIX_RANGES = {
    "initial_white": {"min": 20, "max": 24},      # Starting range for white wines
    "initial_red": {"min": 22, "max": 26},        # Starting range for red wines  
    "fermentation": {"min": -1.0, "max": 40},     # During fermentation (-1 = complete)
    "daily_drop_white": {"max": 3},               # Max drop per day for whites
    "daily_drop_red": {"max": 4}                  # Max drop per day for reds
}

DEFAULT_TEMP_RANGES = {
    "white_fermentation": {"min": 7, "max": 20},    # 45-68°F optimal for whites
    "red_fermentation": {"min": 20, "max": 30},     # 70-85°F optimal for reds
    "critical_abort": {"max": 35},                  # >35°C fermentation fails
    "storage": {"min": 10, "max": 18}               # Storage temperature
}

DEFAULT_TIMING_RULES = {
    "min_interval_minutes": 60,                      # Min time between samples of same type
    "max_gap_hours": 48,                            # Max time without samples (alert)
    "fermentation_phases": {
        "lag": {"duration_hours": 24},               # First 24h - slow start
        "active": {"duration_days": 7},              # Main fermentation
        "completion": {"duration_days": 14}          # Until dry
    }
}

DEFAULT_DENSITY_RANGES = {
    "initial_sg": {"min": 1.085, "max": 1.120},     # Starting specific gravity
    "dry_wine": {"max": 0.995},                      # Dry wine threshold
    "correlation_check": True                        # Check sugar-density correlation
}
```

### Winery-Specific Customization Examples

```python
# Example: High-altitude winery configuration
HIGH_ALTITUDE_CONFIG = {
    "brix_ranges": {
        "initial_white": {"min": 18, "max": 22},    # Lower due to altitude effects
        "initial_red": {"min": 20, "max": 24},      # Adjusted for climate
    },
    "temperature_ranges": {
        "white_fermentation": {"min": 5, "max": 18}, # Cooler climate adjustment
        "red_fermentation": {"min": 18, "max": 28},   # Adjusted for altitude
    }
}

# Example: Dessert wine producer configuration  
DESSERT_WINE_CONFIG = {
    "brix_ranges": {
        "initial_white": {"min": 28, "max": 45},    # Higher sugar for dessert wines
        "fermentation": {"min": 10, "max": 45},     # Residual sugar expected
    }
}
```

---

## 5. Critical Validations Missing

### Immediately Required
1. **Scientific range validation** - Complete `validate_numeric_value` with configurable ranges
2. **Temperature range by wine type** - Complete `validate_temperature_range` 
3. **Daily Brix drop rate validation** - Extend `validate_sugar_trend`
4. **Sample frequency validation** - Complete `validate_sample_chronology`

### Important for Production
5. **Cross-parameter validation** (sugar-density correlation)
6. **Fermentation stage-specific rules**
7. **User permission checks** in validation services
8. **Database constraints** for uniqueness (fermentation_id, sample_type, recorded_at)

### Enhancement Features
9. **Warning-level validations** (non-blocking alerts)
10. **Seasonal/varietal adjustments** to ranges
11. **Integration with fermentation status** transitions

---

## 6. Architecture Agent Knowledge Gaps

**For the Architecture Agent to be effective, it needs:**

### Currently Available
- Service structure and patterns
- Validation result formats  
- Repository integration patterns
- Domain entity relationships

### Missing for Agent Effectiveness
- **Complete validation rule catalog** with all scientific ranges
- **Business rule hierarchy** (critical vs warning vs info)
- **Validation error handling patterns** for each rule type
- **Performance impact** of each validation type
- **Integration points** where validations are called
- **Configuration management strategy** for winery-specific parameters

---

## 7. Configuration Management Recommendations

### Implementation Strategy
1. **External configuration files** (JSON/YAML) per winery environment
2. **Database-stored configurations** with admin interface for parameter adjustment
3. **Environment-specific overrides** (development, staging, production)
4. **Validation parameter versioning** for audit trail
5. **Real-time configuration updates** without service restart

### Architecture Considerations
- Configuration should be injected into validation services via dependency injection
- Default scientific ranges should serve as fallback values
- Configuration changes should be logged for compliance/audit purposes
- Consider caching configuration values for performance
- Validate configuration parameters themselves on startup

This approach allows each winery to customize validation parameters based on their specific grape varieties, climate conditions, and production methods while maintaining scientifically sound defaults.