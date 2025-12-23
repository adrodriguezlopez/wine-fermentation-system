# Logging Best Practices Guide

**Wine Fermentation System - ADR-027 Implementation**  
**Version:** 1.0  
**Last Updated:** December 22, 2025

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [When to Log](#when-to-log)
3. [Log Levels](#log-levels)
4. [Structured Logging Patterns](#structured-logging-patterns)
5. [Context Binding](#context-binding)
6. [Performance Measurement](#performance-measurement)
7. [Error Logging](#error-logging)
8. [Security & Sensitive Data](#security--sensitive-data)
9. [Production Configuration](#production-configuration)
10. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Adding Logging to Your Code

```python
from src.shared.wine_fermentator_logging import get_logger, LogTimer

logger = get_logger(__name__)

async def my_function(user_id: int, data: dict):
    # Log operation start
    logger.info("operation_started", user_id=user_id, data_keys=list(data.keys()))
    
    # Use LogTimer for performance tracking
    with LogTimer(logger, "database_operation"):
        result = await database_call()
    
    # Log success
    logger.info("operation_completed", result_id=result.id)
    return result
```

---

## When to Log

### ✅ DO Log

**Repository Layer** (DEBUG/INFO):
- Database queries with filters (DEBUG)
- Record creation/updates (INFO)
- Multi-tenant query filters (DEBUG)
- Soft delete operations (INFO)

**Service Layer** (INFO/WARNING):
- Business operation start/completion (INFO)
- Validation failures (WARNING)
- Status transitions (INFO)
- Blend operations (INFO with lot details)

**API Layer** (INFO/WARNING/ERROR):
- All incoming requests (INFO - via middleware)
- Request/response timing (INFO - via middleware)
- Business rule violations (WARNING)
- Authentication failures (WARNING)
- Unexpected errors (ERROR)

### ❌ DON'T Log

- Passwords, tokens, API keys (use `sanitize_log_data()` if needed)
- Personal data without business justification
- Inside tight loops (affects performance)
- Redundant information already in context
- Implementation details users don't care about

---

## Log Levels

### DEBUG
**Use for:** Technical details useful during development

```python
logger.debug(
    "database_query_executed",
    query_type="select",
    filters={"winery_id": winery_id, "status": status},
    result_count=len(results)
)
```

**Production:** Usually disabled (`LOG_LEVEL=INFO`)

### INFO
**Use for:** Normal business operations, audit trail

```python
logger.info(
    "fermentation_created",
    fermentation_id=fermentation.id,
    user_id=user_id,
    winery_id=winery_id,
    vintage_year=vintage_year
)
```

**Production:** Always enabled - creates audit trail

### WARNING
**Use for:** Expected errors, validation failures, not found scenarios

```python
logger.warning(
    "validation_failed",
    fermentation_id=fermentation_id,
    error_count=len(errors),
    error_types=[e.field for e in errors]
)
```

**Production:** Monitored for business rule issues

### ERROR
**Use for:** Unexpected errors, exceptions, system failures

```python
logger.error(
    "unexpected_error",
    error_type=type(e).__name__,
    error_message=str(e),
    fermentation_id=fermentation_id
)
```

**Production:** Triggers alerts, requires investigation

---

## Structured Logging Patterns

### Event-Driven Pattern

**✅ Good:**
```python
logger.info("fermentation_created", fermentation_id=123, vintage_year=2024)
```

**❌ Bad:**
```python
logger.info(f"Created fermentation {fermentation_id} for year {vintage_year}")
```

**Why:** Structured logs are searchable, aggregatable, and machine-readable.

### Context-Rich Logging

**✅ Good:**
```python
logger.info(
    "status_updated",
    fermentation_id=fermentation.id,
    old_status=old_status.value,
    new_status=new_status.value,
    user_id=user_id
)
```

**❌ Bad:**
```python
logger.info("status_updated", id=123)  # Missing context
```

### Operation Lifecycle

**Pattern:**
1. Log operation start (INFO/DEBUG)
2. Log critical steps (DEBUG)
3. Log result (INFO for success, WARNING for business failures, ERROR for system failures)

```python
async def create_fermentation(self, data: CreateFermentationDTO):
    logger.info("create_fermentation_started", user_id=data.user_id)
    
    with LogTimer(logger, "create_fermentation"):
        # Business logic
        logger.debug("validating_fermentation_data", vessel_code=data.vessel_code)
        
        fermentation = await self._repository.create(fermentation_data)
        
        logger.info(
            "fermentation_created_successfully",
            fermentation_id=fermentation.id,
            vessel_code=fermentation.vessel_code
        )
    
    return fermentation
```

---

## Context Binding

### Automatic Context (via Middleware)

These are **automatically available** in all logs when using the FastAPI app:

- `correlation_id` - Unique request ID
- `user_id` - Authenticated user (if logged in)
- `winery_id` - Current winery context (multi-tenancy)
- `method` - HTTP method (GET, POST, etc.)
- `path` - Request path

```python
# No need to pass these explicitly - they're in every log!
logger.info("operation_success", result_count=10)
# Output: {"event": "operation_success", "result_count": 10, "user_id": 123, "winery_id": 456, "correlation_id": "abc-123"}
```

### Manual Context Binding

For background tasks or operations outside HTTP requests:

```python
from structlog import contextvars

# Bind context for entire operation
contextvars.bind_contextvars(batch_id="batch-123", job_type="nightly_sync")

logger.info("batch_processing_started")  # Will include batch_id, job_type

# Clear context when done
contextvars.clear_contextvars()
```

---

## Performance Measurement

### Using LogTimer

**Basic Usage:**
```python
from src.shared.wine_fermentator_logging import LogTimer

with LogTimer(logger, "database_query"):
    results = await db.execute(query)

# Logs: {"event": "database_query_completed", "duration_ms": 45.2}
```

**With Additional Context:**
```python
with LogTimer(logger, "bulk_insert", record_count=len(records)):
    await db.bulk_insert(records)

# Logs: {"event": "bulk_insert_completed", "duration_ms": 123.5, "record_count": 50}
```

**Naming Convention:**
- `{operation}_query` - Database queries
- `{operation}_validation` - Validation operations
- `{operation}_processing` - Business logic
- `{operation}_api_call` - External API calls

---

## Error Logging

### Repository Layer Errors

```python
async def create(self, entity: Fermentation) -> Fermentation:
    try:
        logger.debug("creating_fermentation", winery_id=entity.winery_id)
        
        session.add(entity)
        await session.flush()
        
        logger.info("fermentation_created", fermentation_id=entity.id)
        return entity
        
    except IntegrityError as e:
        logger.error(
            "database_integrity_error",
            error_type="IntegrityError",
            winery_id=entity.winery_id,
            constraint=str(e.orig)
        )
        raise
```

### Service Layer Errors

```python
async def update_status(self, fermentation_id: int, new_status: FermentationStatus):
    logger.info("status_update_requested", fermentation_id=fermentation_id)
    
    # Business validation
    if not self._is_valid_transition(current, new_status):
        logger.warning(
            "invalid_status_transition",
            fermentation_id=fermentation_id,
            current_status=current.value,
            requested_status=new_status.value
        )
        raise ValidationError("Invalid status transition")
    
    try:
        result = await self._repository.update_status(fermentation_id, new_status)
        logger.info("status_updated_successfully", fermentation_id=fermentation_id)
        return result
        
    except Exception as e:
        logger.error(
            "status_update_failed",
            fermentation_id=fermentation_id,
            error_type=type(e).__name__
        )
        raise
```

### API Layer Errors

Error handlers automatically log all exceptions:

```python
# In error_handlers.py (already implemented)
except ValidationError as e:
    logger.warning(
        "api_validation_error",
        error_message=str(e),
        error_type="ValidationError",
        endpoint=func.__name__
    )
    raise HTTPException(status_code=422, detail=str(e))
```

---

## Security & Sensitive Data

### Automatic Sanitization

The `sanitize_log_data()` function automatically redacts:
- Passwords
- JWT tokens
- API keys
- Authorization headers

```python
from src.shared.wine_fermentator_logging import sanitize_log_data

user_data = {
    "email": "user@example.com",
    "password": "secret123",  # Will be redacted
    "token": "jwt.token.here"  # Will be redacted
}

logger.info("user_data", data=sanitize_log_data(user_data))
# Output: {"data": {"email": "user@example.com", "password": "***REDACTED***", "token": "***REDACTED***"}}
```

### Manual Sanitization

For custom sensitive fields:

```python
# Don't log full credit card numbers
logger.info("payment_processed", card_last_four=card_number[-4:])

# Don't log full addresses
logger.info("order_shipped", zip_code=address.zip_code)  # Just postal code, not full address
```

### Audit Trail Requirements

**Always log these for compliance:**
- WHO: `user_id`, `winery_id`
- WHAT: Operation name, entity ID
- WHEN: Automatic timestamp
- RESULT: Success/failure

```python
logger.info(
    "fermentation_deleted",
    fermentation_id=fermentation_id,
    user_id=user_id,
    winery_id=winery_id,
    reason="user_requested"
)
```

---

## Production Configuration

### Environment Variables

```bash
# Development
LOG_LEVEL=DEBUG
LOG_FORMAT=console  # Colorful, human-readable

# Production
LOG_LEVEL=INFO
LOG_FORMAT=json     # Structured for CloudWatch/ELK
```

### Application Startup

```python
# In main.py
from src.shared.wine_fermentator_logging import configure_logging
import os

# Configure on app startup
log_level = os.getenv("LOG_LEVEL", "INFO")
log_format = os.getenv("LOG_FORMAT", "json")

configure_logging(
    log_level=log_level,
    use_json=(log_format == "json")
)
```

### Docker Configuration

```dockerfile
# Dockerfile
ENV LOG_LEVEL=INFO
ENV LOG_FORMAT=json
```

### CloudWatch Integration

Logs are automatically structured as JSON, ready for CloudWatch Logs Insights:

```
# Query examples in CloudWatch:
fields @timestamp, event, user_id, correlation_id, duration_ms
| filter event = "fermentation_created"
| sort @timestamp desc
| limit 100

# Find slow operations
fields @timestamp, event, duration_ms
| filter duration_ms > 1000
| sort duration_ms desc
```

---

## Troubleshooting

### "Logs not appearing"

**Check:**
1. Log level configuration: `LOG_LEVEL=DEBUG` to see all logs
2. Logger name: Use `get_logger(__name__)` not `logging.getLogger()`
3. Middleware registered: Check `main.py` has `app.add_middleware(LoggingMiddleware)`

### "Missing correlation_id in logs"

**Cause:** LoggingMiddleware not registered or not outermost middleware

**Fix:**
```python
# In main.py - LoggingMiddleware must be FIRST
app.add_middleware(LoggingMiddleware)  # ← First
app.add_middleware(UserContextMiddleware)
app.add_middleware(CORSMiddleware, ...)
```

### "Missing user_id in logs"

**Cause:** UserContextMiddleware not registered or no authentication

**Fix:**
1. Ensure middleware registered: `app.add_middleware(UserContextMiddleware)`
2. Check endpoint uses `Depends(get_current_user)`
3. Verify JWT token in request: `Authorization: Bearer <token>`

### "Logs are messy in development"

**Use console format for development:**
```python
configure_logging(log_level="DEBUG", use_json=False)
```

### "Too many logs in production"

**Reduce log level:**
```bash
LOG_LEVEL=INFO  # Hides DEBUG logs
```

Or filter specific loggers:
```python
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
```

---

## Quick Reference

### Import Statement
```python
from src.shared.wine_fermentator_logging import get_logger, LogTimer, sanitize_log_data
```

### Logger Creation
```python
logger = get_logger(__name__)
```

### Log Events
```python
logger.debug("event_name", key1=value1, key2=value2)
logger.info("event_name", key1=value1)
logger.warning("event_name", error_type="ValidationError")
logger.error("event_name", error_message=str(e))
```

### Performance Timing
```python
with LogTimer(logger, "operation_name", context_key=value):
    # Your code here
    pass
```

### Sanitize Data
```python
safe_data = sanitize_log_data(user_input)
logger.info("event", data=safe_data)
```

---

## Examples by Layer

### Repository Layer
```python
from src.shared.wine_fermentator_logging import get_logger, LogTimer

logger = get_logger(__name__)

async def create(self, entity: Fermentation) -> Fermentation:
    logger.debug("repository_create_started", winery_id=entity.winery_id)
    
    with LogTimer(logger, "fermentation_insert"):
        session.add(entity)
        await session.flush()
    
    logger.info("fermentation_persisted", fermentation_id=entity.id)
    return entity
```

### Service Layer
```python
from src.shared.wine_fermentator_logging import get_logger, LogTimer

logger = get_logger(__name__)

async def create_fermentation(self, data: CreateFermentationDTO) -> Fermentation:
    logger.info("create_fermentation_requested", user_id=data.user_id)
    
    with LogTimer(logger, "create_fermentation"):
        fermentation = await self._repository.create(fermentation_entity)
    
    logger.info("fermentation_created", fermentation_id=fermentation.id)
    return fermentation
```

### API Layer
```python
from src.shared.wine_fermentator_logging import get_logger

logger = get_logger(__name__)

@router.post("/fermentations", response_model=FermentationResponse)
@handle_service_errors
async def create_fermentation(
    data: CreateFermentationRequest,
    user: UserContext = Depends(get_current_user)
):
    # Logging handled by middleware + error handlers
    # correlation_id, user_id, winery_id automatically bound
    fermentation = await fermentation_service.create_fermentation(data)
    return FermentationResponse.from_entity(fermentation)
```

---

**For more information, see:**
- [ADR-027: Structured Logging & Observability](./.ai-context/adr/ADR-027-structured-logging-observability.md)
- [Implementation Summary](./.ai-context/adr/ADR-027-Phase4-Summary.md)
