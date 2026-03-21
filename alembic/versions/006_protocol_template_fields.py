"""Add template management fields to fermentation_protocols (ADR-039)

Revision ID: 006_protocol_template_fields
Revises: 005_protocol_alerts_updated_at
Create Date: 2026-03-17

ADR-039 adds template lifecycle management to FermentationProtocol.
New columns:
  - is_template  BOOLEAN DEFAULT true  — true = master template, false = per-fermentation instance
  - state        VARCHAR(20) DEFAULT 'FINAL' — DRAFT | FINAL | DEPRECATED
  - template_id  INTEGER nullable — FK to parent template (NULL when is_template=true)
  - approved_by_user_id INTEGER nullable — who approved DRAFT → FINAL transition

Defaults are chosen so existing rows stay valid (they are all master templates
that are already in use → is_template=true, state=FINAL).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "006_protocol_template_fields"
down_revision: Union[str, None] = "005_protocol_alerts_updated_at"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # is_template: master template vs per-fermentation copy
    op.add_column(
        "fermentation_protocols",
        sa.Column(
            "is_template",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )

    # state: DRAFT → FINAL → DEPRECATED lifecycle
    op.add_column(
        "fermentation_protocols",
        sa.Column(
            "state",
            sa.String(20),
            nullable=False,
            server_default="FINAL",
        ),
    )

    # template_id: back-link to master template for instances
    op.add_column(
        "fermentation_protocols",
        sa.Column(
            "template_id",
            sa.Integer(),
            sa.ForeignKey("fermentation_protocols.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # approved_by_user_id: governance audit trail
    op.add_column(
        "fermentation_protocols",
        sa.Column(
            "approved_by_user_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    # Add CHECK constraint on state values
    op.create_check_constraint(
        "ck_protocol_state",
        "fermentation_protocols",
        "state IN ('DRAFT', 'FINAL', 'DEPRECATED')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_protocol_state", "fermentation_protocols", type_="check")
    op.drop_column("fermentation_protocols", "approved_by_user_id")
    op.drop_column("fermentation_protocols", "template_id")
    op.drop_column("fermentation_protocols", "state")
    op.drop_column("fermentation_protocols", "is_template")
