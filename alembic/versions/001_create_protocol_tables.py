"""ADR-035: Create Protocol tables (Feb 10, 2026)

Revision ID: 001_create_protocol_tables
Revises: None
Create Date: 2026-02-09

Creates 4 new tables for Protocol Engine:
- fermentation_protocols: Master protocol templates
- protocol_steps: Individual protocol steps  
- protocol_executions: Protocol adherence tracking
- step_completions: Audit log for step execution

Schema matches domain entities exactly (SQLAlchemy models in src/modules/fermentation/src/domain/entities/)

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "001_create_protocol_tables"
down_revision: Union[str, None] = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # Create fermentation_protocols table
    # Master protocol template for a varietal at a winery
    op.create_table(
        'fermentation_protocols',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('winery_id', sa.Integer(), nullable=False),
        sa.Column('varietal_code', sa.String(length=10), nullable=False),  # "PN", "CS", "CH"
        sa.Column('varietal_name', sa.String(length=100), nullable=False),  # "Pinot Noir"
        sa.Column('version', sa.String(length=10), nullable=False),  # "1.0", "2.1"
        sa.Column('protocol_name', sa.String(length=200), nullable=False),  # "PN-2021-Standard"
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(length=10), nullable=False),  # "RED" or "WHITE"
        sa.Column('expected_duration_days', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_by_user_id', sa.Integer(), nullable=False),  # No FK, just integer
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['winery_id'], ['wineries.id'], name='fk_protocols_winery'),
        sa.UniqueConstraint('winery_id', 'varietal_code', 'version', 
                          name='uq_protocol_winery_varietal_version'),
        sa.CheckConstraint('expected_duration_days > 0', name='ck_protocol_duration_positive'),
    )
    
    # Create indexes for common queries
    op.create_index('ix_protocols_winery_active', 'fermentation_protocols', ['winery_id', 'is_active'])
    op.create_index('ix_protocols_varietal', 'fermentation_protocols', ['winery_id', 'varietal_code'])
    
    # Create protocol_steps table
    # Individual steps within a protocol (ordered)
    op.create_table(
        'protocol_steps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('protocol_id', sa.Integer(), nullable=False),
        sa.Column('step_order', sa.Integer(), nullable=False),  # 1, 2, 3, ...
        sa.Column('step_type', sa.String(length=50), nullable=False),  # Category: INITIALIZATION, MONITORING, etc.
        sa.Column('description', sa.Text(), nullable=False),  # Specific step details
        sa.Column('expected_day', sa.Integer(), nullable=False),  # 0=crush day, 1=next day
        sa.Column('tolerance_hours', sa.Integer(), nullable=False, server_default='12'),  # ±N hours
        sa.Column('duration_minutes', sa.Integer(), nullable=False, server_default='0'),  # How long task takes
        sa.Column('is_critical', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('criticality_score', sa.Float(), nullable=False, server_default='1.0'),  # 0-100
        sa.Column('depends_on_step_id', sa.Integer(), nullable=True),  # For step dependencies
        sa.Column('can_repeat_daily', sa.Boolean(), nullable=False, server_default='0'),  # Can do 2x/day?
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['protocol_id'], ['fermentation_protocols.id'], 
                              ondelete='CASCADE', name='fk_steps_protocol'),
        sa.ForeignKeyConstraint(['depends_on_step_id'], ['protocol_steps.id'], 
                              name='fk_steps_dependency'),
        sa.UniqueConstraint('protocol_id', 'step_order', name='uq_protocol_steps_order'),
        sa.CheckConstraint('expected_day >= 0', name='ck_step_expected_day_positive'),
        sa.CheckConstraint('tolerance_hours >= 0', name='ck_step_tolerance_positive'),
        sa.CheckConstraint('duration_minutes >= 0', name='ck_step_duration_positive'),
        sa.CheckConstraint('criticality_score BETWEEN 0 AND 100', name='ck_step_criticality_range'),
    )
    
    # Create indexes for step queries
    op.create_index('ix_steps_protocol_id', 'protocol_steps', ['protocol_id'])
    
    # Create protocol_executions table
    # Execution tracking for a specific fermentation following a protocol
    op.create_table(
        'protocol_executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fermentation_id', sa.Integer(), nullable=False),
        sa.Column('protocol_id', sa.Integer(), nullable=False),
        sa.Column('winery_id', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='NOT_STARTED'),
        sa.Column('compliance_score', sa.Float(), nullable=False, server_default='0.0'),  # 0-100%
        sa.Column('completed_steps', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('skipped_critical_steps', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['fermentation_id'], ['fermentations.id'], 
                              name='fk_executions_fermentation'),
        sa.ForeignKeyConstraint(['protocol_id'], ['fermentation_protocols.id'], 
                              name='fk_executions_protocol'),
        sa.ForeignKeyConstraint(['winery_id'], ['wineries.id'], name='fk_executions_winery'),
        sa.UniqueConstraint('fermentation_id', name='uq_execution_fermentation'),
        sa.CheckConstraint('compliance_score BETWEEN 0 AND 100', name='ck_execution_compliance_range'),
    )
    
    # Create indexes for execution queries
    op.create_index('ix_executions_fermentation', 'protocol_executions', ['fermentation_id'])
    op.create_index('ix_executions_status', 'protocol_executions', ['winery_id', 'status'])
    
    # Create step_completions table
    # Audit trail - record of when/how each step was completed
    op.create_table(
        'step_completions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('execution_id', sa.Integer(), nullable=False),
        sa.Column('step_id', sa.Integer(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_on_schedule', sa.Boolean(), nullable=True),
        sa.Column('days_late', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('was_skipped', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('skip_reason', sa.String(length=50), nullable=True),  # EQUIPMENT_FAILURE, etc.
        sa.Column('skip_notes', sa.Text(), nullable=True),
        sa.Column('verified_by_user_id', sa.Integer(), nullable=True),  # No FK, just integer
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['execution_id'], ['protocol_executions.id'], 
                              ondelete='CASCADE', name='fk_completions_execution'),
        sa.ForeignKeyConstraint(['step_id'], ['protocol_steps.id'], 
                              name='fk_completions_step'),
        sa.UniqueConstraint('execution_id', 'step_id', name='uq_completion_execution_step'),
        sa.CheckConstraint(
            '(was_skipped = 1 AND skip_reason IS NOT NULL) OR was_skipped = 0',
            name='ck_completion_skip_reason_required'
        ),
    )
    
    # Create indexes for completion queries
    op.create_index('ix_completions_execution', 'step_completions', ['execution_id'])
    op.create_index('ix_completions_completed_at', 'step_completions', ['completed_at'])


def downgrade() -> None:
    # Drop tables in reverse order of creation (respect foreign keys)
    op.drop_index('ix_completions_completed_at', table_name='step_completions')
    op.drop_index('ix_completions_execution', table_name='step_completions')
    op.drop_table('step_completions')
    
    op.drop_index('ix_executions_status', table_name='protocol_executions')
    op.drop_index('ix_executions_fermentation', table_name='protocol_executions')
    op.drop_table('protocol_executions')
    
    op.drop_index('ix_steps_protocol_id', table_name='protocol_steps')
    op.drop_table('protocol_steps')
    
    op.drop_index('ix_protocols_varietal', table_name='fermentation_protocols')
    op.drop_index('ix_protocols_winery_active', table_name='fermentation_protocols')
    op.drop_table('fermentation_protocols')
