"""ADR-041: Create winemaker_actions table

Revision ID: 007_create_winemaker_actions
Revises: 006_protocol_template_fields
Create Date: 2026-03-22

Creates the winemaker_actions table for recording corrective/proactive actions
taken by winemakers in response to alerts, anomalies, or missed protocol steps.

Business rules:
- All FK references are nullable except winery_id — an action may target a
  fermentation, execution, step, or alert independently.
- taken_by_user_id is a plain integer (no FK) — consistent with the cross-module
  independence pattern used by ProtocolExecution.created_by_user_id.
- outcome defaults to PENDING and is updated via a separate PATCH /outcome endpoint.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "007_create_winemaker_actions"
down_revision: Union[str, None] = "006_protocol_template_fields"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "winemaker_actions",

        sa.Column("id", sa.Integer(), nullable=False),

        # Multi-tenancy
        sa.Column("winery_id", sa.Integer(), nullable=False),

        # Optional links — action may reference any combination of these
        sa.Column("fermentation_id", sa.Integer(), nullable=True),
        sa.Column("execution_id", sa.Integer(), nullable=True),
        sa.Column("step_id", sa.Integer(), nullable=True),
        sa.Column("alert_id", sa.Integer(), nullable=True),
        sa.Column("recommendation_id", sa.Integer(), nullable=True),  # plain int, no FK (cross-module)

        # Action classification
        sa.Column("action_type", sa.String(50), nullable=False),

        # Free-text description written by the winemaker
        sa.Column("description", sa.Text(), nullable=False),

        # When the action was physically taken (may be in the past)
        sa.Column("taken_at", sa.DateTime(), nullable=False),

        # Audit — no FK to users to avoid cross-module dependency
        sa.Column("taken_by_user_id", sa.Integer(), nullable=False),

        # Outcome tracking (updated hours/days after the action)
        sa.Column("outcome", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("outcome_notes", sa.Text(), nullable=True),
        sa.Column("outcome_recorded_at", sa.DateTime(), nullable=True),

        # Timestamps
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),

        sa.PrimaryKeyConstraint("id"),

        sa.ForeignKeyConstraint(["winery_id"], ["wineries.id"],
                                name="fk_winemaker_actions_winery"),
        sa.ForeignKeyConstraint(["fermentation_id"], ["fermentations.id"],
                                ondelete="CASCADE",
                                name="fk_winemaker_actions_fermentation"),
        sa.ForeignKeyConstraint(["execution_id"], ["protocol_executions.id"],
                                ondelete="SET NULL",
                                name="fk_winemaker_actions_execution"),
        sa.ForeignKeyConstraint(["step_id"], ["protocol_steps.id"],
                                ondelete="SET NULL",
                                name="fk_winemaker_actions_step"),
        sa.ForeignKeyConstraint(["alert_id"], ["protocol_alerts.id"],
                                ondelete="SET NULL",
                                name="fk_winemaker_actions_alert"),

        sa.CheckConstraint(
            "outcome IN ('PENDING', 'RESOLVED', 'NO_EFFECT', 'WORSENED')",
            name="ck_winemaker_actions_outcome",
        ),
    )

    op.create_index("ix_winemaker_actions_winery_id",
                    "winemaker_actions", ["winery_id"])
    op.create_index("ix_winemaker_actions_fermentation_id",
                    "winemaker_actions", ["fermentation_id"])
    op.create_index("ix_winemaker_actions_execution_id",
                    "winemaker_actions", ["execution_id"])
    op.create_index("ix_winemaker_actions_alert_id",
                    "winemaker_actions", ["alert_id"])
    op.create_index("ix_winemaker_actions_taken_at",
                    "winemaker_actions", ["taken_at"])


def downgrade() -> None:
    op.drop_index("ix_winemaker_actions_taken_at",    table_name="winemaker_actions")
    op.drop_index("ix_winemaker_actions_alert_id",    table_name="winemaker_actions")
    op.drop_index("ix_winemaker_actions_execution_id", table_name="winemaker_actions")
    op.drop_index("ix_winemaker_actions_fermentation_id", table_name="winemaker_actions")
    op.drop_index("ix_winemaker_actions_winery_id",   table_name="winemaker_actions")
    op.drop_table("winemaker_actions")
