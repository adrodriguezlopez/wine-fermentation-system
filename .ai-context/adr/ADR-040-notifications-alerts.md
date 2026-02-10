# ADR-040: Protocol Notifications & Alerts Strategy

**Status**: ✅ Approved for Implementation  
**Date**: February 9, 2026  
**Decision Makers**: Development Team  
**Related ADRs**: ADR-038 (Deviation Detection), ADR-021 (Protocol Engine)  
**Timeline Context**: Phase 3 implementation (Week 7-8), **Offline-First Priority**

---

## Context and Problem Statement

From AI Enologist + user constraints:

1. **7-day/week fermentation coverage**: Alerts must reach winemakers anytime
2. **Offline capability**: App must cache recent protocol states
3. **<15 seconds to log**: UI can't have excessive polling for alerts
4. **Mobile-first**: Working from winery floor with spotty connectivity
5. **Multiple severities**: H2S detection ≠ visual inspection missed

Alert types include:
- **Critical**: H2S detected, fermentation stalled (immediate action)
- **High**: Step 1 day late, critical skip (same-day action)
- **Medium**: Step timing warning, deviation logged (routine check)
- **Low**: Informational only (archived, don't notify)

---

## Decision

### Alert Classification

```python
class AlertType(str, Enum):
    # CRITICAL - immediate action required
    CRITICAL_STEP_MISSED = "CRITICAL_STEP_MISSED"        # H2S check not done
    FERMENTATION_STALLED = "FERMENTATION_STALLED"          # Brix not changing
    H2S_DETECTED = "H2S_DETECTED"                           # Smell detected
    EQUIPMENT_FAILURE = "EQUIPMENT_FAILURE"               # Unable to proceed
    CONTAMINATION_DETECTED = "CONTAMINATION_DETECTED"     # Fermentation failed
    
    # HIGH - same-day action
    CRITICAL_STEP_LATE = "CRITICAL_STEP_LATE"             # 1+ days late
    CRITICAL_STEP_APPROACHING = "CRITICAL_STEP_APPROACHING"  # Due soon
    
    # MEDIUM - routine check
    STEP_APPROACHING = "STEP_APPROACHING"                 # Due in 12 hours
    DEVIATION_DETECTED = "DEVIATION_DETECTED"             # Minor deviation
    PROTOCOL_ADVISORY = "PROTOCOL_ADVISORY"               # Analysis suggestion
    
    # LOW - informational
    STEP_COMPLETED = "STEP_COMPLETED"                     # Audit trail only
    PROTOCOL_UPDATED = "PROTOCOL_UPDATED"                 # Change notification


class AlertSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    
    def should_notify_immediately(self) -> bool:
        return self in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]
    
    def should_cache_offline(self) -> bool:
        return self in [AlertSeverity.CRITICAL, AlertSeverity.HIGH, AlertSeverity.MEDIUM]
```

---

### Notification System Architecture

```
┌─────────────────────────────────────────┐
│ Event Source                            │
│ - Deviation detected (ADR-038)          │
│ - Analysis recommendation (ADR-037)     │
│ - Protocol step due (Scheduler)         │
│ - Manual escalation (Winemaker)         │
└────────────────┬────────────────────────┘
                 │ Event Emitted
                 ▼
┌─────────────────────────────────────────┐
│ Alert Generator                         │
│ - Determine severity                    │
│ - Route to channels                     │
│ - Respect preferences                   │
└────────────────┬────────────────────────┘
                 │
        ┌────────┴──────────┬────────────┐
        ▼                   ▼            ▼
    ┌───────────────┐  ┌─────────┐  ┌──────────┐
    │  In-App Alert │  │   SMS   │  │  Email   │
    │  (Real-time)  │  │(Critical)│  │ (All)    │
    └───────────────┘  └─────────┘  └──────────┘
        ▲                   ▲            ▲
        │ Cached            │            │
        │ Offline           │            │
        │ First             └────────────┴── Async Queued
        │
    ┌───┴──────────────┐
    │  Mobile App      │
    │  - Pull alerts   │
    │  - Offline list  │
    │  - Acknowledge   │
    └──────────────────┘
```

---

### Alert Generation

```python
class Alert(BaseEntity):
    """Alert record stored in DB for UI display and mobile sync"""
    
    id: int
    fermentation_id: int
    winery_id: int
    
    # Content
    alert_type: AlertType
    severity: AlertSeverity
    title: str  # "Critical Step Missed: H2S Check"
    message: str  # Detailed message
    recommended_action: str  # "Check for H2S smell and add aeration"
    
    # Source
    triggered_by: str  # "deviation_detected", "analysis_recommendation", etc.
    source_id: Optional[int]  # deviation_id, anomaly_id, etc.
    source_data: dict  # Raw data that triggered alert
    
    # State
    is_acknowledged: bool
    acknowledged_by_user_id: Optional[int]
    acknowledged_at: Optional[datetime]
    
    # Metadata
    created_at: datetime
    synced_to_mobile_at: Optional[datetime]  # For offline-first
    notified_channels: List[str]  # ["IN_APP", "SMS", "EMAIL"]


def generate_alert(
    fermentation_id: int,
    alert_type: AlertType,
    triggered_by: str,
    source_id: Optional[int] = None,
    source_data: dict = None
) -> Alert:
    """
    Create alert and route to appropriate channels based on severity.
    """
    
    execution = ProtocolExecution.get(fermentation_id=fermentation_id)
    fermentation = Fermentation.get(id=fermentation_id)
    winery = fermentation.winery
    
    # Determine severity
    severity = determine_alert_severity(alert_type)
    
    # Create alert record
    alert = Alert.create(
        fermentation_id=fermentation_id,
        winery_id=winery.id,
        alert_type=alert_type,
        severity=severity,
        title=get_alert_title(alert_type),
        message=get_alert_message(alert_type, source_data),
        recommended_action=get_recommended_action(alert_type),
        triggered_by=triggered_by,
        source_id=source_id,
        source_data=source_data or {}
    )
    
    # Notify user(s)
    notify_alert(alert)
    
    return alert


def determine_alert_severity(alert_type: AlertType) -> AlertSeverity:
    """Map alert types to severities"""
    severity_map = {
        AlertType.CRITICAL_STEP_MISSED: AlertSeverity.CRITICAL,
        AlertType.FERMENTATION_STALLED: AlertSeverity.CRITICAL,
        AlertType.H2S_DETECTED: AlertSeverity.CRITICAL,
        AlertType.EQUIPMENT_FAILURE: AlertSeverity.CRITICAL,
        AlertType.CONTAMINATION_DETECTED: AlertSeverity.CRITICAL,
        
        AlertType.CRITICAL_STEP_LATE: AlertSeverity.HIGH,
        AlertType.CRITICAL_STEP_APPROACHING: AlertSeverity.HIGH,
        
        AlertType.STEP_APPROACHING: AlertSeverity.MEDIUM,
        AlertType.DEVIATION_DETECTED: AlertSeverity.MEDIUM,
        AlertType.PROTOCOL_ADVISORY: AlertSeverity.MEDIUM,
        
        AlertType.STEP_COMPLETED: AlertSeverity.LOW,
        AlertType.PROTOCOL_UPDATED: AlertSeverity.LOW,
    }
    return severity_map.get(alert_type, AlertSeverity.MEDIUM)


def get_alert_title(alert_type: AlertType) -> str:
    """Generate alert title"""
    titles = {
        AlertType.CRITICAL_STEP_MISSED: "⚠️ CRITICAL: Required Step Not Completed",
        AlertType.FERMENTATION_STALLED: "🔴 Fermentation Stalled",
        AlertType.H2S_DETECTED: "🔴 CRITICAL: H2S Detected",
        AlertType.EQUIPMENT_FAILURE: "🔴 Equipment Failure",
        AlertType.CONTAMINATION_DETECTED: "🔴 Contamination Detected",
        
        AlertType.CRITICAL_STEP_LATE: "⚠️ Critical Step Late",
        AlertType.CRITICAL_STEP_APPROACHING: "⏰ Critical Step Due Soon",
        
        AlertType.STEP_APPROACHING: "Step Due in 12 Hours",
        AlertType.DEVIATION_DETECTED: "Deviation Detected",
        AlertType.PROTOCOL_ADVISORY: "Analysis Suggestion",
        
        AlertType.STEP_COMPLETED: "Step Completed",
        AlertType.PROTOCOL_UPDATED: "Protocol Updated",
    }
    return titles.get(alert_type, "Alert")
```

---

### Notification Channels

#### 1. In-App Alerts (Real-Time, Cached)

```python
def notify_in_app(alert: Alert, execution: ProtocolExecution) -> None:
    """
    Push alert to in-app notification system (WebSocket + polling fallback).
    Cache for offline-first mobile app.
    """
    
    # Identify recipients (all users of this winery with WINEMAKER+ role)
    recipients = User.filter(
        winery_id=alert.winery_id,
        role__in=[UserRole.ADMIN, UserRole.WINEMAKER]
    )
    
    for recipient in recipients:
        # Cache for offline-first
        if alert.severity.should_cache_offline():
            CachedAlert.create(
                user_id=recipient.id,
                alert_id=alert.id,
                cached_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=7)
            )
        
        # WebSocket push (if online)
        broadcast_websocket(
            channel=f"winery_{alert.winery_id}",
            event="alert_created",
            data={
                "alert_id": alert.id,
                "severity": alert.severity,
                "title": alert.title,
                "message": alert.message,
                "fermentation_id": alert.fermentation_id,
                "recommended_action": alert.recommended_action
            }
        )
    
    alert.notified_channels.append("IN_APP")
    alert.save()
```

#### 2. SMS Alerts (Critical Only)

```python
def notify_sms(alert: Alert, execution: ProtocolExecution) -> None:
    """
    Send SMS for CRITICAL+HIGH severity alerts.
    """
    
    # Only CRITICAL/HIGH alerts via SMS
    if alert.severity not in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
        return
    
    # Get winemaker's phone (from user profile)
    winemaker = execution.fermentation.created_by_user
    if not winemaker.phone_number:
        logger.warning(f"No phone for winemaker {winemaker.id}")
        return
    
    # Compose message (keep short, max 160 chars)
    sms_text = f"🍷 {alert.title}\n{alert.recommended_action}"
    
    # Send via Twilio (or equivalent)
    try:
        sms_client.send_message(
            to=winemaker.phone_number,
            from_=settings.TWILIO_PHONE,
            body=sms_text
        )
        logger.info(f"SMS sent to {winemaker.phone_number}")
    except Exception as e:
        logger.error(f"SMS send failed: {e}")
        # Fall back to email
        notify_email(alert, execution)
    
    alert.notified_channels.append("SMS")
    alert.save()
```

#### 3. Email Alerts (All Severities)

```python
def notify_email(alert: Alert, execution: ProtocolExecution) -> None:
    """
    Send email for all alerts (async, batched).
    """
    
    # Get recipients
    recipients = User.filter(
        winery_id=alert.winery_id,
        role__in=[UserRole.ADMIN, UserRole.WINEMAKER]
    )
    
    for recipient in recipients:
        # Queue email task (async)
        email_queue.enqueue(
            task_name="send_alert_email",
            kwargs={
                "recipient_email": recipient.email,
                "alert_data": {
                    "title": alert.title,
                    "message": alert.message,
                    "severity": alert.severity,
                    "fermentation_name": execution.fermentation.batch_name,
                    "recommended_action": alert.recommended_action,
                    "dashboard_url": f"{settings.FRONTEND_URL}/fermentations/{alert.fermentation_id}"
                }
            }
        )
    
    alert.notified_channels.append("EMAIL")
    alert.save()
```

---

### Schedule-Based Alerts

```python
# Scheduler job (runs every 6 hours)
def check_upcoming_steps() -> None:
    """
    Find fermentations where critical steps are due in next 12 hours.
    """
    
    executions = ProtocolExecution.filter(
        status=ProtocolExecutionStatus.ACTIVE
    )
    
    for execution in executions:
        protocol = execution.protocol
        current_time = datetime.now()
        
        for step in protocol.steps:
            # Already completed?
            if execution.is_step_completed(step.id):
                continue
            
            # Calculate expected completion time
            expected_time = execution.start_date + timedelta(
                days=step.expected_day,
                hours=step.tolerance_hours  # Start of window
            )
            
            time_until_due = (expected_time - current_time).total_seconds() / 3600
            
            # Due in 12 hours and not yet alerted?
            if 0 < time_until_due <= 12:
                alert_type = (
                    AlertType.CRITICAL_STEP_APPROACHING 
                    if step.is_critical 
                    else AlertType.STEP_APPROACHING
                )
                
                # Check for duplicate alert
                existing = Alert.filter(
                    fermentation_id=execution.fermentation_id,
                    alert_type=alert_type,
                    source_id=step.id,
                    created_at__gte=datetime.now() - timedelta(hours=6)
                )
                
                if not existing:
                    generate_alert(
                        fermentation_id=execution.fermentation_id,
                        alert_type=alert_type,
                        triggered_by="scheduler",
                        source_id=step.id,
                        source_data={
                            "step_description": step.description,
                            "hours_until_due": round(time_until_due, 1)
                        }
                    )
```

---

### Offline-First Mobile Sync

```python
# API endpoint for mobile app
@router.get("/api/fermentations/{fermentation_id}/alerts/cached")
def get_cached_alerts(fermentation_id: int, user: User) -> dict:
    """
    Return all non-acknowledged alerts for offline-first sync.
    Mobile app calls this on app launch + periodically.
    """
    
    execution = ProtocolExecution.get(fermentation_id=fermentation_id)
    
    cached_alerts = CachedAlert.filter(
        user_id=user.id,
        alert_id__in=Alert.filter(fermentation_id=fermentation_id)
    ).order_by("-created_at")
    
    return {
        "fermentation_id": fermentation_id,
        "batch_name": execution.fermentation.batch_name,
        "protocol_name": execution.protocol.protocol_name,
        "last_sync": datetime.now(),
        "alerts": [
            {
                "alert_id": ca.alert.id,
                "severity": ca.alert.severity,
                "title": ca.alert.title,
                "message": ca.alert.message,
                "recommended_action": ca.alert.recommended_action,
                "is_acknowledged": ca.alert.is_acknowledged,
                "created_at": ca.alert.created_at
            }
            for ca in cached_alerts
        ]
    }


@router.post("/api/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: int, user: User) -> dict:
    """
    Mark alert as read (works offline, syncs on reconnection).
    """
    
    alert = Alert.get(id=alert_id)
    alert.is_acknowledged = True
    alert.acknowledged_by_user_id = user.id
    alert.acknowledged_at = datetime.now()
    alert.save()
    
    return {"acknowledged_at": alert.acknowledged_at}
```

---

### Alert Suppression & Preferences

```python
class AlertPreference(BaseEntity):
    """User preferences for alert types"""
    
    user_id: int
    winery_id: int
    
    # Alert channel preferences
    notify_in_app: bool = True
    notify_sms_critical_only: bool = True  # Only SMS for CRITICAL
    notify_email_high_and_above: bool = True
    
    # Suppression rules
    quiet_hours_start: Optional[time]  # e.g., 22:00
    quiet_hours_end: Optional[time]    # e.g., 06:00
    suppress_informational: bool = True  # Don't notify on LOW severity
    
    # Do not disturb
    dnd_enabled: bool = False
    dnd_until: Optional[datetime]


def should_notify(alert: Alert, user: User) -> bool:
    """
    Check if user wants this alert based on preferences.
    """
    
    prefs = AlertPreference.get(user_id=user.id, winery_id=alert.winery_id)
    
    # During quiet hours?
    if prefs.quiet_hours_start and prefs.quiet_hours_end:
        now_time = datetime.now().time()
        if prefs.quiet_hours_start <= now_time <= prefs.quiet_hours_end:
            # Still notify CRITICAL regardless
            if alert.severity != AlertSeverity.CRITICAL:
                return False
    
    # During DND?
    if prefs.dnd_enabled and datetime.now() < prefs.dnd_until:
        # Still notify CRITICAL regardless
        if alert.severity != AlertSeverity.CRITICAL:
            return False
    
    # Suppress informational?
    if prefs.suppress_informational and alert.severity == AlertSeverity.LOW:
        return False
    
    return True
```

---

## Implementation Roadmap

### Phase 1: Core Alerts (Week 7)
- [ ] Create Alert + AlertPreference models
- [ ] Implement `generate_alert()` function
- [ ] In-app notifications (WebSocket + polling)

### Phase 2: SMS Alerts (Week 7)
- [ ] Integrate Twilio API
- [ ] SMS for CRITICAL/HIGH alerts
- [ ] Phone number validation

### Phase 3: Email Alerts (Week 8)
- [ ] Queue system (Celery/RQ)
- [ ] Email templates
- [ ] Batch sending for performance

### Phase 4: Scheduling (Week 8)
- [ ] Cron jobs for upcoming-step checks
- [ ] Duplicate alert prevention

### Phase 5: Mobile Sync (Week 8-9)
- [ ] CachedAlert model
- [ ] Offline-first sync endpoints
- [ ] Mobile app integration

### Phase 6: Preferences (Week 9)
- [ ] AlertPreference UI
- [ ] Quiet hours / DND support
- [ ] Channel preferences

---

## Consequences

### Positive ✅
- **Timely notifications**: Winemakers alerted immediately to critical issues
- **Offline-first**: Mobile app works without connectivity
- **Channel choices**: SMS for critical, email for routine
- **Preference control**: Users control notification flow
- **Audit trail**: All alerts logged and searchable

### Negative ⚠️
- **Alert fatigue**: Too many notifications could desensitize users
  - Mitigated: Suppress LOW severity, respect preferences
- **SMS cost**: Twilio charges per message
  - Mitigated: Only CRITICAL/HIGH via SMS

---

## Testing Strategy

```python
def test_critical_alert_generates_sms():
    """CRITICAL alert → SMS sent"""
    alert = generate_alert(
        fermentation_id=123,
        alert_type=AlertType.H2S_DETECTED,
        triggered_by="analysis"
    )
    assert "SMS" in alert.notified_channels

def test_low_alert_no_sms():
    """LOW alert → no SMS, only in-app"""
    alert = generate_alert(
        fermentation_id=123,
        alert_type=AlertType.STEP_COMPLETED,
        triggered_by="scheduler"
    )
    assert "SMS" not in alert.notified_channels
    assert "IN_APP" in alert.notified_channels

def test_quiet_hours_respected():
    """During quiet hours, no MEDIUM alerts"""
    prefs = AlertPreference(
        quiet_hours_start=time(22, 0),
        quiet_hours_end=time(6, 0)
    )
    with patch('datetime.now', return_value=datetime(2026, 2, 9, 23, 0)):
        assert not should_notify(Alert(severity=AlertSeverity.MEDIUM), user)

def test_critical_bypasses_quiet_hours():
    """CRITICAL alerts sent even during quiet hours"""
    prefs = AlertPreference(quiet_hours_start=time(22, 0))
    with patch('datetime.now', return_value=datetime(2026, 2, 9, 23, 0)):
        assert should_notify(Alert(severity=AlertSeverity.CRITICAL), user)

def test_offline_cache():
    """MEDIUM+ alerts cached for offline"""
    alert = generate_alert(
        fermentation_id=123,
        alert_type=AlertType.DEVIATION_DETECTED,
        triggered_by="protocol"
    )
    cached = CachedAlert.get(alert_id=alert.id)
    assert cached is not None
```

---

## Questions for Validation

- [ ] Should failed SMS delivery trigger email fallback immediately?
- [ ] What's max alert frequency per fermentation per day? (prevent spam)
- [ ] Should winemakers be able to customize severity mappings? (CRITICAL → HIGH for their taste)

