"""ADR-040: Create protocol_alerts table (Mar 8, 2026)

Revision ID: 002_create_protocol_alerts_table
Revises: 001_create_protocol_tables
Create Date: 2026-03-08

Creates 1 new table for Alert Persistence (ADR-040):
- protocol_alerts: Durable storage for protocol execution alerts

Replaces the in-memory AlertDetail dataclass with database persistence,
enabling alert history, status tracking, and cross-session queries.

Schema matches ProtocolAlert entity exactly:
    src/modules/fermentation/src/domain/entities/protocol_alert.py

Alert lifecycle: PENDING → SENT → ACKNOWLEDGED | DISMISSED
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "002_create_protocol_alerts_table"
down_revision: Union[str, None] = "001_create_protocol_tables"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # Create protocol_alerts table
    # Persistent storage for alerts generated during protocol execution
    op.create_table(
        'protocol_alerts',
        sa.Column('id', sa.Integer(), nullable=False),

        # Scope — which execution/protocol/winery generated this alert
        sa.Column('execution_id', sa.Integer(), nullable=False),
        sa.Column('protocol_id', sa.Integer(), nullable=False),
        sa.Column('winery_id', sa.Integer(), nullable=False),

        # Optional step link (null for execution-level alerts)
        sa.Column('step_id', sa.Integer(), nullable=True),
        sa.Column('step_name', sa.String(length=255), nullable=True),

        # Classification
        sa.Column(
            'alert_type', sa.String(length=50), nullable=False,
            comment='STEP_OVERDUE | STEP_DUE_SOON | EXECUTION_NEARING_COMPLETION | EXECUTION_BEHIND_SCHEDULE | CRITICAL_DEVIATION',
        ),
        sa.Column(
            'severity', sa.String(length=20), nullable=False,
            comment='INFO | WARNING | CRITICAL',
        ),
        sa.Column(
            'status', sa.String(length=20), nullable=False,
            server_default='PENDING',
            comment='PENDING | SENT | ACKNOWLEDGED | DISMISSED',
        ),

        # Content
        sa.Column('message', sa.Text(), nullable=False),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('dismissed_at', sa.DateTime(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['execution_id'], ['protocol_executions.id'],
            ondelete='CASCADE', name='fk_alerts_execution',
        ),
        sa.ForeignKeyConstraint(
            ['protocol_id'], ['fermentation_protocols.id'],
            name='fk_alerts_protocol',
        ),
        sa.ForeignKeyConstraint(
            ['step_id'], ['protocol_steps.id'],
            name='fk_alerts_step',
        ),
        sa.CheckConstraint(
            "alert_type IN ('STEP_OVERDUE','STEP_DUE_SOON','EXECUTION_NEARING_COMPLETION','EXECUTION_BEHIND_SCHEDULE','CRITICAL_DEVIATION')",
            name='ck_alerts_alert_type',
        ),
        sa.CheckConstraint(
            "severity IN ('INFO','WARNING','CRITICAL')",
            name='ck_alerts_severity',
        ),
        sa.CheckConstraint(
            "status IN ('PENDING','SENT','ACKNOWLEDGED','DISMISSED')",
            name='ck_alerts_status',
        ),
    )

    # Composite index for the most common query: pending alerts for an execution
    op.create_index(
        'ix_protocol_alerts__execution_status',
        'protocol_alerts',
        ['execution_id', 'status'],
    )

    # Index for winery-level alert dashboard
    op.create_index(
        'ix_protocol_alerts__winery_id',
        'protocol_alerts',
        ['winery_id'],
    )


def downgrade() -> None:
    op.drop_index('ix_protocol_alerts__winery_id', table_name='protocol_alerts')
    op.drop_index('ix_protocol_alerts__execution_status', table_name='protocol_alerts')
    op.drop_table('protocol_alerts')
