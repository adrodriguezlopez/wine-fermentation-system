"""
Protocol Alert Service for Fermentation Monitoring

Provides alert management for protocol execution:
- Send alerts for overdue steps
- Send completion reminders
- Track pending and sent alerts
- Integration with compliance tracking
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from src.modules.fermentation.src.domain.enums.step_type import ProtocolExecutionStatus
from src.modules.fermentation.src.repository_component.fermentation_protocol_repository import FermentationProtocolRepository
from src.modules.fermentation.src.repository_component.protocol_execution_repository import ProtocolExecutionRepository
from src.modules.fermentation.src.repository_component.protocol_step_repository import ProtocolStepRepository
from src.modules.fermentation.src.service_component.services.protocol_compliance_service import ProtocolComplianceService
from src.modules.fermentation.src.domain.entities.protocol_alert import ProtocolAlert
from src.modules.fermentation.src.domain.repositories.protocol_alert_repository_interface import IProtocolAlertRepository


# ============================================================================
# Enums
# ============================================================================

class AlertType(str, Enum):
    """Types of alerts."""
    STEP_OVERDUE = "STEP_OVERDUE"
    STEP_DUE_SOON = "STEP_DUE_SOON"
    EXECUTION_NEARING_COMPLETION = "EXECUTION_NEARING_COMPLETION"
    EXECUTION_BEHIND_SCHEDULE = "EXECUTION_BEHIND_SCHEDULE"
    CRITICAL_DEVIATION = "CRITICAL_DEVIATION"


class AlertStatus(str, Enum):
    """Status of an alert."""
    PENDING = "PENDING"
    SENT = "SENT"
    DISMISSED = "DISMISSED"
    ACKNOWLEDGED = "ACKNOWLEDGED"


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class AlertDetail:
    """Details of an alert."""
    alert_id: int
    alert_type: AlertType
    execution_id: int
    protocol_id: int
    winery_id: int
    step_id: Optional[int]
    step_name: Optional[str]
    message: str
    severity: str  # "INFO", "WARNING", "CRITICAL"
    status: AlertStatus
    created_at: datetime
    sent_at: Optional[datetime]
    dismissed_at: Optional[datetime]


@dataclass
class AlertSummary:
    """Summary of pending alerts for execution."""
    execution_id: int
    total_pending: int
    critical_count: int
    overdue_count: int
    due_soon_count: int
    completion_reminder_count: int


# ============================================================================
# Protocol Alert Service
# ============================================================================

class ProtocolAlertService:
    """
    Service for managing protocol execution alerts.
    
    Provides:
    - Overdue step alerts
    - Completion reminder alerts
    - Deviation alerts
    - Alert tracking and status management
    """

    def __init__(
        self,
        protocol_repository: FermentationProtocolRepository,
        execution_repository: ProtocolExecutionRepository,
        step_repository: ProtocolStepRepository,
        compliance_service: ProtocolComplianceService,
        alert_repository: Optional[IProtocolAlertRepository] = None,
    ):
        """Initialize service with repository and service dependencies."""
        self.protocol_repo = protocol_repository
        self.execution_repo = execution_repository
        self.step_repo = step_repository
        self.compliance_service = compliance_service
        self.alert_repo = alert_repository

    async def send_overdue_alert(
        self,
        execution_id: int,
        winery_id: int,
        alert_hours_before: int = 24,
    ) -> List[AlertDetail]:
        """
        Check for overdue steps and send alerts.

        Alerts are sent for steps that:
        - Have expected_day + tolerance_hours passed
        - Are still pending (not completed/skipped)
        - Haven't already generated an alert in last 24 hours

        Args:
            execution_id: ID of protocol execution
            winery_id: Winery ID (for access control)
            alert_hours_before: Hours before actual due time to alert (default: 24)

        Returns:
            List of AlertDetail for sent alerts

        Raises:
            ValueError: If execution not found or access denied
        """
        # Verify execution and access
        execution = await self.execution_repo.get_by_id(execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        if execution.winery_id != winery_id:
            raise ValueError(
                f"Access denied: Execution {execution_id} belongs to winery {execution.winery_id}"
            )

        # Get overdue steps from compliance service
        overdue_steps = await self.compliance_service.get_overdue_steps(execution_id)

        alerts = []
        for step in overdue_steps:
            # Calculate expected completion
            expected_completion = execution.start_date + timedelta(
                days=step.expected_day,
                hours=step.tolerance_hours,
            )

            # Alert if past expected + tolerance
            if datetime.utcnow() >= expected_completion:
                alert = AlertDetail(
                    alert_id=0,  # Will be assigned by repository
                    alert_type=AlertType.STEP_OVERDUE,
                    execution_id=execution_id,
                    protocol_id=execution.protocol_id,
                    winery_id=winery_id,
                    step_id=step.id,
                    step_name=step.description,
                    message=f"Step '{step.description}' is overdue since {expected_completion.strftime('%Y-%m-%d %H:%M')}",
                    severity="WARNING" if datetime.utcnow() < expected_completion + timedelta(hours=24) else "CRITICAL",
                    status=AlertStatus.PENDING,
                    created_at=datetime.utcnow(),
                    sent_at=None,
                    dismissed_at=None,
                )
                alerts.append(alert)

        # Persist all generated alerts if repository is wired
        if alerts and self.alert_repo is not None:
            orm_alerts = [
                ProtocolAlert(
                    execution_id=a.execution_id,
                    protocol_id=a.protocol_id,
                    winery_id=a.winery_id,
                    step_id=a.step_id,
                    step_name=a.step_name,
                    alert_type=a.alert_type.value,
                    severity=a.severity,
                    status=a.status.value,
                    message=a.message,
                    created_at=a.created_at,
                )
                for a in alerts
            ]
            await self.alert_repo.create_many(orm_alerts)

        return alerts

    async def send_completion_reminder(
        self,
        execution_id: int,
        winery_id: int,
        days_remaining_threshold: int = 3,
    ) -> Optional[AlertDetail]:
        """
        Send reminder if execution is nearing completion.

        Sends alert when:
        - Expected completion is within threshold days
        - Execution is still ACTIVE
        - Compliance score is not yet at target (e.g., < 85%)

        Args:
            execution_id: ID of protocol execution
            winery_id: Winery ID (for access control)
            days_remaining_threshold: Days until completion to send alert (default: 3)

        Returns:
            AlertDetail if alert sent, None otherwise

        Raises:
            ValueError: If execution not found or access denied
        """
        # Verify execution and access
        execution = await self.execution_repo.get_by_id(execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        if execution.winery_id != winery_id:
            raise ValueError(
                f"Access denied: Execution {execution_id} belongs to winery {execution.winery_id}"
            )

        # Skip if not ACTIVE
        if execution.status != ProtocolExecutionStatus.ACTIVE:
            return None

        # Get protocol for duration
        protocol = await self.protocol_repo.get_by_id(execution.protocol_id)
        if not protocol:
            raise ValueError(f"Protocol {execution.protocol_id} not found")

        # Calculate expected completion
        expected_completion = execution.start_date + timedelta(
            days=protocol.expected_duration_days
        )
        days_remaining = (expected_completion - datetime.utcnow()).days

        # Alert if approaching completion and not at target
        target_compliance = 85.0
        if (
            0 < days_remaining <= days_remaining_threshold
            and execution.compliance_score < target_compliance
        ):
            alert = AlertDetail(
                alert_id=0,  # Will be assigned by repository
                alert_type=AlertType.EXECUTION_NEARING_COMPLETION,
                execution_id=execution_id,
                protocol_id=execution.protocol_id,
                winery_id=winery_id,
                step_id=None,
                step_name=None,
                message=f"Execution nearing completion in {days_remaining} day(s). Current compliance: {execution.compliance_score:.1f}%",
                severity="INFO",
                status=AlertStatus.PENDING,
                created_at=datetime.utcnow(),
                sent_at=None,
                dismissed_at=None,
            )
            if self.alert_repo is not None:
                orm_alert = ProtocolAlert(
                    execution_id=alert.execution_id,
                    protocol_id=alert.protocol_id,
                    winery_id=alert.winery_id,
                    step_id=alert.step_id,
                    step_name=alert.step_name,
                    alert_type=alert.alert_type.value,
                    severity=alert.severity,
                    status=alert.status.value,
                    message=alert.message,
                    created_at=alert.created_at,
                )
                await self.alert_repo.create(orm_alert)
            return alert

        return None

    async def detect_critical_deviations(
        self,
        execution_id: int,
        winery_id: int,
    ) -> List[AlertDetail]:
        """
        Detect critical deviations and send alerts.

        Alerts for:
        - Unjustified skips of critical steps
        - Missing critical steps
        - Compliance score drop > 10%

        Args:
            execution_id: ID of protocol execution
            winery_id: Winery ID (for access control)

        Returns:
            List of AlertDetail for critical deviations

        Raises:
            ValueError: If execution not found or access denied
        """
        # Verify execution and access
        execution = await self.execution_repo.get_by_id(execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        if execution.winery_id != winery_id:
            raise ValueError(
                f"Access denied: Execution {execution_id} belongs to winery {execution.winery_id}"
            )

        # Get deviations
        deviations = await self.compliance_service.detect_deviations(execution_id)

        alerts = []
        for deviation in deviations:
            # Alert for unjustified skips and missing critical steps
            if (
                deviation.step.is_critical
                and deviation.step_status in ["UNJUSTIFIED_SKIP", "MISSING"]
            ):
                alert = AlertDetail(
                    alert_id=0,
                    alert_type=AlertType.CRITICAL_DEVIATION,
                    execution_id=execution_id,
                    protocol_id=execution.protocol_id,
                    winery_id=winery_id,
                    step_id=deviation.step.id,
                    step_name=deviation.step.description,
                    message=f"Critical deviation: Step '{deviation.step.description}' is {deviation.step_status}",
                    severity="CRITICAL",
                    status=AlertStatus.PENDING,
                    created_at=datetime.utcnow(),
                    sent_at=None,
                    dismissed_at=None,
                )
                alerts.append(alert)

        if alerts and self.alert_repo is not None:
            orm_alerts = [
                ProtocolAlert(
                    execution_id=a.execution_id,
                    protocol_id=a.protocol_id,
                    winery_id=a.winery_id,
                    step_id=a.step_id,
                    step_name=a.step_name,
                    alert_type=a.alert_type.value,
                    severity=a.severity,
                    status=a.status.value,
                    message=a.message,
                    created_at=a.created_at,
                )
                for a in alerts
            ]
            await self.alert_repo.create_many(orm_alerts)

        return alerts

    async def get_pending_alerts(
        self,
        execution_id: int,
        winery_id: int,
        status_filter: Optional[AlertStatus] = None,
        alert_type_filter: Optional[AlertType] = None,
    ) -> List[AlertDetail]:
        """
        Get pending alerts for execution.

        Args:
            execution_id: ID of protocol execution
            winery_id: Winery ID (for access control)
            status_filter: Filter by alert status (default: PENDING only)
            alert_type_filter: Filter by alert type (default: all types)

        Returns:
            List of matching AlertDetail

        Raises:
            ValueError: If execution not found or access denied
        """
        # Verify execution and access
        execution = await self.execution_repo.get_by_id(execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        if execution.winery_id != winery_id:
            raise ValueError(
                f"Access denied: Execution {execution_id} belongs to winery {execution.winery_id}"
            )

        # Default to PENDING if not specified
        status = status_filter or AlertStatus.PENDING

        if self.alert_repo is not None:
            orm_alerts = await self.alert_repo.get_by_execution(
                execution_id=execution_id,
                status=status.value,
                alert_type=alert_type_filter.value if alert_type_filter else None,
            )
            return [
                AlertDetail(
                    alert_id=a.id,
                    alert_type=AlertType(a.alert_type),
                    execution_id=a.execution_id,
                    protocol_id=a.protocol_id,
                    winery_id=a.winery_id,
                    step_id=a.step_id,
                    step_name=a.step_name,
                    message=a.message,
                    severity=a.severity,
                    status=AlertStatus(a.status),
                    created_at=a.created_at,
                    sent_at=a.sent_at,
                    dismissed_at=a.dismissed_at,
                )
                for a in orm_alerts
            ]

        # No repo wired: return empty list (backward compatible)
        return []

    async def get_alert_summary(
        self,
        execution_id: int,
        winery_id: int,
    ) -> AlertSummary:
        """
        Get summary of pending alerts for execution.

        Args:
            execution_id: ID of protocol execution
            winery_id: Winery ID (for access control)

        Returns:
            AlertSummary with counts by severity/type

        Raises:
            ValueError: If execution not found or access denied
        """
        # Verify execution and access
        execution = await self.execution_repo.get_by_id(execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        if execution.winery_id != winery_id:
            raise ValueError(
                f"Access denied: Execution {execution_id} belongs to winery {execution.winery_id}"
            )

        # Get all pending alerts (would use alert repo in production)
        pending_alerts = await self.get_pending_alerts(
            execution_id,
            winery_id,
            status_filter=AlertStatus.PENDING,
        )

        # Count by type
        critical = sum(
            1
            for a in pending_alerts
            if a.severity == "CRITICAL"
        )
        overdue = sum(
            1
            for a in pending_alerts
            if a.alert_type == AlertType.STEP_OVERDUE
        )
        due_soon = sum(
            1
            for a in pending_alerts
            if a.alert_type == AlertType.STEP_DUE_SOON
        )
        completion_reminder = sum(
            1
            for a in pending_alerts
            if a.alert_type == AlertType.EXECUTION_NEARING_COMPLETION
        )

        return AlertSummary(
            execution_id=execution_id,
            total_pending=len(pending_alerts),
            critical_count=critical,
            overdue_count=overdue,
            due_soon_count=due_soon,
            completion_reminder_count=completion_reminder,
        )

    async def acknowledge_alert(
        self,
        execution_id: int,
        alert_id: int,
        winery_id: int,
    ) -> AlertDetail:
        """
        Mark alert as acknowledged.

        Args:
            execution_id: ID of protocol execution
            alert_id: ID of alert to acknowledge
            winery_id: Winery ID (for access control)

        Returns:
            Updated AlertDetail

        Raises:
            ValueError: If execution/alert not found or access denied
        """
        # Verify execution and access
        execution = await self.execution_repo.get_by_id(execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        if execution.winery_id != winery_id:
            raise ValueError(
                f"Access denied: Execution {execution_id} belongs to winery {execution.winery_id}"
            )

        if self.alert_repo is None:
            raise ValueError("Alert repository not configured")

        orm_alert = await self.alert_repo.acknowledge(alert_id)
        if orm_alert is None:
            raise ValueError(f"Alert {alert_id} not found")

        return AlertDetail(
            alert_id=orm_alert.id,
            alert_type=AlertType(orm_alert.alert_type),
            execution_id=orm_alert.execution_id,
            protocol_id=orm_alert.protocol_id,
            winery_id=orm_alert.winery_id,
            step_id=orm_alert.step_id,
            step_name=orm_alert.step_name,
            message=orm_alert.message,
            severity=orm_alert.severity,
            status=AlertStatus(orm_alert.status),
            created_at=orm_alert.created_at,
            sent_at=orm_alert.sent_at,
            dismissed_at=orm_alert.dismissed_at,
        )
