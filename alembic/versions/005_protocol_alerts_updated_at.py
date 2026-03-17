"""Add missing updated_at column to protocol_alerts table

Revision ID: 005_protocol_alerts_updated_at
Revises: 004_protocol_updated_at
Create Date: 2026-03-16

Migration 002 created protocol_alerts without an `updated_at` column.
BaseEntity defines updated_at, so the ORM includes it in every INSERT.
This migration adds the missing column.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "005_protocol_alerts_updated_at"
down_revision: Union[str, None] = "004_protocol_updated_at"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "protocol_alerts",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )


def downgrade() -> None:
    op.drop_column("protocol_alerts", "updated_at")
