"""ADR-035: Add missing updated_at column to protocol tables

Revision ID: 004_protocol_updated_at
Revises: 003_protocol_advisory
Create Date: 2026-03-16

Migration 001 created protocol_steps, protocol_executions, and step_completions
without an `updated_at` column.  All three entities inherit from BaseEntity which
defines `updated_at`, so the ORM includes it in every INSERT/UPDATE.  This
migration adds the missing column with a sensible default (NOW()) so the DB
schema matches the SQLAlchemy entity definitions.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = "004_protocol_updated_at"
down_revision: Union[str, None] = "003_protocol_advisory"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # Add updated_at to protocol_steps
    op.add_column(
        "protocol_steps",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    # Add updated_at to protocol_executions
    op.add_column(
        "protocol_executions",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    # Add updated_at to step_completions
    op.add_column(
        "step_completions",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )


def downgrade() -> None:
    op.drop_column("step_completions", "updated_at")
    op.drop_column("protocol_executions", "updated_at")
    op.drop_column("protocol_steps", "updated_at")
