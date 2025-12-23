# Production Deployment Checklist - ADR-027 Logging

**Wine Fermentation System**  
**Version:** 1.0  
**Last Updated:** December 22, 2025

---

## Pre-Deployment Checklist

### 1. Environment Configuration

- [ ] **Set LOG_LEVEL environment variable**
  ```bash
  export LOG_LEVEL=INFO  # Production default
  # or LOG_LEVEL=DEBUG for troubleshooting
  ```

- [ ] **Set LOG_FORMAT for structured logging**
  ```bash
  export LOG_FORMAT=json  # Required for CloudWatch/ELK/Datadog
  ```

- [ ] **Configure database connection logging**
  ```bash
  # Optional: Reduce SQLAlchemy noise
  export SQLALCHEMY_LOG_LEVEL=WARNING
  ```

### 2. Application Configuration

- [ ] **Verify main.py logging configuration**
  ```python
  # In src/modules/fermentation/src/main.py
  configure_logging(
      log_level=os.getenv("LOG_LEVEL", "INFO"),
      use_json=(os.getenv("LOG_FORMAT", "json") == "json")
  )
  ```

- [ ] **Confirm middleware order**
  ```python
  # LoggingMiddleware MUST be first
  app.add_middleware(LoggingMiddleware)      # ← First
  app.add_middleware(UserContextMiddleware)  # ← Second
  app.add_middleware(CORSMiddleware, ...)    # ← Third
  ```

- [ ] **Verify error handlers include logging**
  - Check `error_handlers.py` has `get_logger(__name__)`
  - All exception handlers log before raising HTTPException

### 3. Dependencies

- [ ] **Verify structlog installed**
  ```bash
  cd src/modules/fermentation
  poetry show structlog  # Should show ^25.5.0
  ```

- [ ] **Verify colorama installed** (for console output in dev)
  ```bash
  poetry show colorama  # Should show ^0.4.6
  ```

### 4. Testing

- [ ] **Run all unit tests**
  ```bash
  cd src/modules/fermentation
  poetry run pytest tests/unit/ -v
  # Expected: 223/223 passing
  ```

- [ ] **Test logging configuration**
  ```bash
  # Start app with different log levels
  LOG_LEVEL=DEBUG poetry run uvicorn src.main:app --port 8000
  LOG_LEVEL=INFO poetry run uvicorn src.main:app --port 8000
  ```

- [ ] **Verify correlation IDs in responses**
  ```bash
  curl -i http://localhost:8000/health
  # Check for: X-Correlation-ID header in response
  ```

- [ ] **Test structured JSON output**
  ```bash
  LOG_FORMAT=json poetry run uvicorn src.main:app --port 8000
  # Logs should be JSON: {"event": "...", "timestamp": "..."}
  ```

---

## Docker Deployment

### Dockerfile Configuration

- [ ] **Set environment variables in Dockerfile**
  ```dockerfile
  # In src/modules/fermentation/Dockerfile
  ENV LOG_LEVEL=INFO
  ENV LOG_FORMAT=json
  ENV DATABASE_URL=postgresql://...
  ```

- [ ] **Verify CMD uses correct entry point**
  ```dockerfile
  CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```

### Docker Compose

- [ ] **Configure logging in docker-compose.yml**
  ```yaml
  services:
    fermentation:
      environment:
        - LOG_LEVEL=INFO
        - LOG_FORMAT=json
      logging:
        driver: "json-file"
        options:
          max-size: "10m"
          max-file: "3"
  ```

### Build & Test

- [ ] **Build Docker image**
  ```bash
  cd src/modules/fermentation
  docker build -t wine-fermentation:latest .
  ```

- [ ] **Test container locally**
  ```bash
  docker run -p 8000:8000 \
    -e LOG_LEVEL=INFO \
    -e LOG_FORMAT=json \
    -e DATABASE_URL=postgresql://... \
    wine-fermentation:latest
  ```

- [ ] **Verify logs are JSON formatted**
  ```bash
  docker logs <container_id>
  # Should show structured JSON logs
  ```

---

## Cloud Platform Deployment

### AWS (ECS/Fargate + CloudWatch)

- [ ] **Configure task definition environment variables**
  ```json
  {
    "environment": [
      {"name": "LOG_LEVEL", "value": "INFO"},
      {"name": "LOG_FORMAT", "value": "json"}
    ]
  }
  ```

- [ ] **Set up CloudWatch Log Group**
  ```bash
  aws logs create-log-group --log-group-name /ecs/wine-fermentation
  ```

- [ ] **Configure log routing**
  ```json
  {
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/wine-fermentation",
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": "fermentation"
      }
    }
  }
  ```

- [ ] **Create CloudWatch dashboard**
  - Request count by endpoint
  - Average response time
  - Error rate (4xx/5xx)
  - Correlation ID tracking

- [ ] **Set up CloudWatch alarms**
  ```bash
  # Example: Alert on error rate > 5%
  aws cloudwatch put-metric-alarm \
    --alarm-name fermentation-high-error-rate \
    --metric-name ErrorCount \
    --threshold 5 \
    --comparison-operator GreaterThanThreshold
  ```

### Azure (App Service + Application Insights)

- [ ] **Configure App Settings**
  ```bash
  az webapp config appsettings set \
    --resource-group wine-rg \
    --name wine-fermentation \
    --settings LOG_LEVEL=INFO LOG_FORMAT=json
  ```

- [ ] **Enable Application Insights**
  ```bash
  az monitor app-insights component create \
    --app wine-fermentation \
    --location eastus \
    --resource-group wine-rg
  ```

- [ ] **Configure structured logging integration**
  - Logs automatically ingested as custom events
  - Correlation IDs tracked in dependency telemetry

### GCP (Cloud Run + Cloud Logging)

- [ ] **Deploy with environment variables**
  ```bash
  gcloud run deploy wine-fermentation \
    --image gcr.io/project/wine-fermentation \
    --set-env-vars LOG_LEVEL=INFO,LOG_FORMAT=json
  ```

- [ ] **Verify Cloud Logging ingestion**
  ```bash
  gcloud logging read "resource.type=cloud_run_revision" --limit 50
  ```

- [ ] **Create log-based metrics**
  - Request duration (P50, P95, P99)
  - Error count by endpoint
  - User operations by winery_id

---

## Monitoring & Alerting

### CloudWatch Logs Insights Queries

- [ ] **Save common queries**

**Find slow operations:**
```
fields @timestamp, event, duration_ms, correlation_id
| filter duration_ms > 1000
| sort duration_ms desc
| limit 20
```

**Track fermentation operations:**
```
fields @timestamp, event, fermentation_id, user_id, winery_id
| filter event in ["fermentation_created", "status_updated", "sample_added"]
| sort @timestamp desc
```

**Find errors by endpoint:**
```
fields @timestamp, error_type, endpoint, error_message
| filter level = "error"
| stats count() by endpoint
```

**Monitor validation failures:**
```
fields @timestamp, event, fermentation_id, error_count
| filter event = "validation_failed"
| stats sum(error_count) by bin(5m)
```

### ELK Stack (Elasticsearch + Kibana)

- [ ] **Configure Filebeat for log shipping**
  ```yaml
  filebeat.inputs:
  - type: container
    paths:
      - '/var/lib/docker/containers/*/*.log'
    json.keys_under_root: true
    json.add_error_key: true
  
  output.elasticsearch:
    hosts: ["elasticsearch:9200"]
    index: "wine-fermentation-%{+yyyy.MM.dd}"
  ```

- [ ] **Create Kibana dashboards**
  - Request rate (by endpoint)
  - Response time percentiles
  - Error rate trend
  - Correlation ID drill-down

- [ ] **Set up alerts**
  - Error rate > 5%
  - Response time P95 > 2s
  - Validation failures spike

### Datadog

- [ ] **Install Datadog agent**
  ```yaml
  # docker-compose.yml
  services:
    datadog:
      image: datadog/agent:latest
      environment:
        - DD_API_KEY=${DD_API_KEY}
        - DD_LOGS_ENABLED=true
        - DD_LOGS_CONFIG_CONTAINER_COLLECT_ALL=true
  ```

- [ ] **Configure log pipeline**
  - Parse JSON logs automatically
  - Extract correlation_id as trace ID
  - Tag logs by: env, service, winery_id

- [ ] **Create monitors**
  - APM: Trace correlation_id through stack
  - Logs: Error rate by endpoint
  - Metrics: Request duration by operation

---

## Performance Baselines

### Expected Log Volume

**Development:**
- LOG_LEVEL=DEBUG: ~1,000-5,000 events/minute
- Size: ~500KB - 2MB/minute

**Production:**
- LOG_LEVEL=INFO: ~100-500 events/minute (depends on traffic)
- Size: ~50KB - 200KB/minute
- Storage: ~72MB - 288MB/day

### Performance Impact

- **LogTimer overhead:** <1ms per operation
- **Middleware overhead:** ~2-5ms per request
- **JSON serialization:** <1ms per log event

### Optimization Tips

- [ ] Use `LOG_LEVEL=INFO` in production (not DEBUG)
- [ ] Avoid logging in tight loops
- [ ] Use `LogTimer` only for operations >10ms
- [ ] Sample high-frequency events if needed

---

## Security Checklist

- [ ] **Verify sensitive data sanitization**
  - Passwords redacted
  - JWT tokens redacted
  - API keys redacted
  - Authorization headers sanitized

- [ ] **Test sanitization**
  ```python
  from src.shared.wine_fermentator_logging import sanitize_log_data
  
  data = {"password": "secret", "email": "user@test.com"}
  safe = sanitize_log_data(data)
  assert safe["password"] == "***REDACTED***"
  ```

- [ ] **Audit trail compliance**
  - All operations log: user_id, winery_id, timestamp
  - Fermentation creation/deletion logged
  - Status changes logged
  - Data access logged

- [ ] **Log retention policy**
  - Development: 7 days
  - Production: 30-90 days (compliance requirement)
  - Archive: S3/GCS for long-term storage

---

## Troubleshooting Guide

### Issue: No logs appearing

**Diagnostic:**
```bash
# Check if logging is configured
python -c "from src.shared.wine_fermentator_logging import get_logger; logger = get_logger('test'); logger.info('test')"
```

**Solutions:**
1. Set `LOG_LEVEL=DEBUG` temporarily
2. Check structlog is installed: `poetry show structlog`
3. Verify `configure_logging()` called in main.py

### Issue: Logs not structured (not JSON)

**Diagnostic:**
```bash
# Check LOG_FORMAT
echo $LOG_FORMAT
```

**Solutions:**
1. Set `LOG_FORMAT=json`
2. Restart application
3. Check `configure_logging(use_json=True)` in code

### Issue: Missing correlation_id

**Diagnostic:**
```bash
# Test middleware
curl -H "X-Correlation-ID: test-123" http://localhost:8000/health
# Check response header for X-Correlation-ID
```

**Solutions:**
1. Ensure `LoggingMiddleware` registered first
2. Check middleware order in main.py
3. Verify app instance has middleware: `app.middleware`

### Issue: Performance degradation

**Diagnostic:**
```bash
# Check log volume
tail -f logs.json | wc -l  # Lines per second
```

**Solutions:**
1. Increase LOG_LEVEL to WARNING (reduce volume)
2. Remove DEBUG logs from hot paths
3. Sample high-frequency events
4. Use async log handlers

---

## Rollback Plan

If logging causes issues in production:

### Quick Disable (Emergency)

```bash
# Set log level to ERROR only
export LOG_LEVEL=ERROR

# Or disable structured logging temporarily
export LOG_FORMAT=console

# Restart service
systemctl restart wine-fermentation
```

### Gradual Disable

1. **Remove middleware** (preserves basic logging):
   ```python
   # Comment out in main.py
   # app.add_middleware(LoggingMiddleware)
   # app.add_middleware(UserContextMiddleware)
   ```

2. **Remove repository logging** (if causing DB issues):
   ```python
   # Temporarily comment out LogTimer in repositories
   ```

3. **Full rollback**:
   ```bash
   git revert <ADR-027-commits>
   poetry install
   poetry run pytest  # Ensure tests still pass
   ```

---

## Post-Deployment Validation

### Within 1 hour of deployment:

- [ ] Verify logs appearing in CloudWatch/ELK/Datadog
- [ ] Check correlation IDs in logs
- [ ] Confirm user_id/winery_id in logs
- [ ] Verify request timing logs
- [ ] Test error logging (trigger 404, 422, 500)

### Within 24 hours:

- [ ] Review log volume vs. baseline
- [ ] Check CloudWatch costs
- [ ] Verify no performance degradation
- [ ] Confirm audit trail completeness
- [ ] Test log-based alerts

### Within 1 week:

- [ ] Analyze slow operations (duration_ms > 1000)
- [ ] Review error patterns
- [ ] Optimize noisy logs
- [ ] Train team on log queries
- [ ] Document common troubleshooting scenarios

---

## Success Criteria

✅ Deployment is successful when:

1. All logs are structured JSON in production
2. Correlation IDs present in all logs
3. User context (user_id, winery_id) bound automatically
4. Request/response timing measured
5. All errors logged before HTTP response
6. No performance degradation (< 5ms overhead)
7. Log volume within expected range
8. CloudWatch/ELK dashboards functional
9. Alerts configured and tested
10. Team trained on log queries

---

## Support Contacts

- **Logging Issues:** Check [Troubleshooting Guide](#troubleshooting-guide)
- **Performance Issues:** Review [Performance Baselines](#performance-baselines)
- **Security Concerns:** See [Security Checklist](#security-checklist)

---

**For detailed implementation, see:**
- [Logging Best Practices](./.ai-context/logging-best-practices.md)
- [ADR-027 Documentation](./.ai-context/adr/ADR-027-structured-logging-observability.md)
