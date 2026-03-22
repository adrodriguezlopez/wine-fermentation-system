"""
WinemakerAction Entity (ADR-041)

Records a corrective or proactive action taken by a winemaker during fermentation,
optionally linked to an alert, protocol step, execution, or analysis recommendation.

Table: winemaker_actions
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infra.orm.base_entity import BaseEntity
from src.modules.fermentation.src.domain.enums.step_type import ActionType, ActionOutcome


class WinemakerAction(BaseEntity):
    """
    A corrective or proactive action taken by a winemaker.

    Lifecycle:
        created (outcome=PENDING) → winemaker observes result →
        PATCH /outcome updates outcome to RESOLVED | NO_EFFECT | WORSENED

    FK design (ADR-028 module independence):
        - taken_by_user_id  — plain int, no FK to users
        - recommendation_id — plain int, no FK to analysis_results
        - All other FKs are within the fermentation module and nullable.
    """

    __tablename__ = "winemaker_actions"
    __table_args__ = (
        Index("ix_winemaker_actions_winery_id",        "winery_id"),
        Index("ix_winemaker_actions_fermentation_id",  "fermentation_id"),
        Index("ix_winemaker_actions_execution_id",     "execution_id"),
        Index("ix_winemaker_actions_alert_id",         "alert_id"),
        Index("ix_winemaker_actions_taken_at",         "taken_at"),
        CheckConstraint(
            "outcome IN ('PENDING', 'RESOLVED', 'NO_EFFECT', 'WORSENED')",
            name="ck_winemaker_actions_outcome",
        ),
        {"extend_existing": True},
    )

    # Multi-tenancy
    winery_id: Mapped[int] = mapped_column(
        ForeignKey("wineries.id"), nullable=False
    )

    # Optional contextual links (any combination may be present)
    fermentation_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("fermentations.id", ondelete="CASCADE"), nullable=True
    )
    execution_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("protocol_executions.id", ondelete="SET NULL"), nullable=True
    )
    step_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("protocol_steps.id", ondelete="SET NULL"), nullable=True
    )
    alert_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("protocol_alerts.id", ondelete="SET NULL"), nullable=True
    )
    # Cross-module reference — stored as plain int (no ORM FK per ADR-028)
    recommendation_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Action classification & content
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    taken_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    # Audit — no FK to users (cross-module independence)
    taken_by_user_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Outcome tracking (updated separately via PATCH /outcome)
    outcome: Mapped[str] = mapped_column(
        String(20), nullable=False,
        default=ActionOutcome.PENDING.value,
        server_default="PENDING",
    )
    outcome_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    outcome_recorded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
