"""
ProtocolAlert Entity (ADR-040)

ORM model for persisting protocol execution alerts.
Replaces the in-memory AlertDetail dataclass with durable database storage,
enabling alert history, status tracking, and cross-session queries.

Table: protocol_alerts
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.infra.orm.base_entity import BaseEntity

if TYPE_CHECKING:
    from src.modules.fermentation.src.domain.entities.protocol_execution import ProtocolExecution
    from src.modules.fermentation.src.domain.entities.protocol_step import ProtocolStep


class ProtocolAlert(BaseEntity):
    """
    Persistent protocol execution alert.

    Captures alerts generated when protocol steps are overdue, executions are
    nearing completion, or critical deviations are detected. The winemaker can
    acknowledge or dismiss alerts via the API.

    Lifecycle:
        PENDING → acknowledged/dismissed by winemaker
        SENT → delivery confirmed (future: email/push)
    """

    __tablename__ = "protocol_alerts"
    __table_args__ = (
        Index("ix_protocol_alerts__execution_status", "execution_id", "status"),
        Index("ix_protocol_alerts__winery_id", "winery_id"),
    )

    # Scope
    execution_id: Mapped[int] = mapped_column(
        ForeignKey("protocol_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    protocol_id: Mapped[int] = mapped_column(
        ForeignKey("fermentation_protocols.id"),
        nullable=False,
    )
    winery_id: Mapped[int] = mapped_column(
        ForeignKey("wineries.id"),
        nullable=False,
    )

    # Optional step link (null for execution-level alerts)
    step_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("protocol_steps.id"),
        nullable=True,
    )
    step_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Classification
    alert_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="STEP_OVERDUE | STEP_DUE_SOON | EXECUTION_NEARING_COMPLETION | EXECUTION_BEHIND_SCHEDULE | CRITICAL_DEVIATION",
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="INFO | WARNING | CRITICAL",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
        comment="PENDING | SENT | ACKNOWLEDGED | DISMISSED",
    )

    # Content
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    dismissed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships (lazy to avoid N+1)
    execution: Mapped["ProtocolExecution"] = relationship(
        "ProtocolExecution",
        foreign_keys=[execution_id],
        lazy="select",
    )

    def acknowledge(self) -> None:
        """Mark alert as acknowledged with current timestamp."""
        self.status = "ACKNOWLEDGED"
        self.acknowledged_at = datetime.utcnow()

    def dismiss(self) -> None:
        """Mark alert as dismissed by the winemaker."""
        self.status = "DISMISSED"
        self.dismissed_at = datetime.utcnow()

    def mark_sent(self) -> None:
        """Mark alert as delivered (email / push)."""
        self.status = "SENT"
        self.sent_at = datetime.utcnow()

    @property
    def is_pending(self) -> bool:
        return self.status == "PENDING"

    @property
    def is_critical(self) -> bool:
        return self.severity == "CRITICAL"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "execution_id": self.execution_id,
            "protocol_id": self.protocol_id,
            "winery_id": self.winery_id,
            "step_id": self.step_id,
            "step_name": self.step_name,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "status": self.status,
            "message": self.message,
            "created_at": self.created_at.isoformat(),
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "dismissed_at": self.dismissed_at.isoformat() if self.dismissed_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<ProtocolAlert(id={self.id}, execution_id={self.execution_id}, "
            f"type={self.alert_type}, severity={self.severity}, status={self.status})>"
        )
