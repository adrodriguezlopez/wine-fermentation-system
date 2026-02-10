"""ADR-035: Create Protocol tables

Revision ID: 001_create_protocol_tables
Revises: None
Create Date: 2026-02-09

Creates 4 new tables for Protocol Engine:
- fermentation_protocols: Master protocol templates
- protocol_steps: Individual protocol steps
- protocol_executions: Protocol adherence tracking
- step_completions: Audit log for step execution

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
    op.create_table(
        'fermentation_protocols',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('winery_id', sa.Integer(), nullable=False),
        sa.Column('varietal', sa.String(length=100), nullable=False),
        sa.Column('vintage_year', sa.Integer(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['winery_id'], ['wineries.id'], name='fk_protocols_winery'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_protocols_user'),
        sa.UniqueConstraint('winery_id', 'varietal', 'vintage_year', 'version', 
                          name='uq_protocol_winery_varietal_version'),
        sa.CheckConstraint('version > 0', name='ck_protocol_version_positive'),
    )
    
    # Create index for winery queries
    op.create_index('ix_protocols_winery_id', 'fermentation_protocols', ['winery_id'])
    op.create_index('ix_protocols_is_active', 'fermentation_protocols', ['is_active'])
    op.create_index('ix_protocols_varietal', 'fermentation_protocols', ['varietal'])
    
    # Create protocol_steps table
    op.create_table(
        'protocol_steps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('protocol_id', sa.Integer(), nullable=False),
        sa.Column('step_order', sa.Integer(), nullable=False),
        sa.Column('step_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('target_min', sa.Float(), nullable=True),
        sa.Column('target_max', sa.Float(), nullable=True),
        sa.Column('target_value', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('duration_hours', sa.Integer(), nullable=True),
        sa.Column('is_critical', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('can_skip', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['protocol_id'], ['fermentation_protocols.id'], 
                              ondelete='CASCADE', name='fk_steps_protocol'),
        sa.UniqueConstraint('protocol_id', 'step_order', name='uq_protocol_step_order'),
        sa.CheckConstraint('step_order > 0', name='ck_step_order_positive'),
        sa.CheckConstraint('target_min <= target_max OR target_min IS NULL', 
                          name='ck_step_target_range'),
    )
    
    # Create index for protocol queries
    op.create_index('ix_steps_protocol_id', 'protocol_steps', ['protocol_id'])
    op.create_index('ix_steps_step_type', 'protocol_steps', ['step_type'])
    
    # Create protocol_executions table
    op.create_table(
        'protocol_executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fermentation_id', sa.Integer(), nullable=False),
        sa.Column('protocol_id', sa.Integer(), nullable=False),
        sa.Column('winery_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('current_step_order', sa.Integer(), nullable=True),
        sa.Column('total_steps', sa.Integer(), nullable=False),
        sa.Column('steps_completed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('steps_skipped', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('compliance_score', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['fermentation_id'], ['fermentations.id'], 
                              ondelete='CASCADE', name='fk_executions_fermentation'),
        sa.ForeignKeyConstraint(['protocol_id'], ['fermentation_protocols.id'], 
                              name='fk_executions_protocol'),
        sa.ForeignKeyConstraint(['winery_id'], ['wineries.id'], name='fk_executions_winery'),
        sa.UniqueConstraint('fermentation_id', name='uq_execution_fermentation'),
        sa.CheckConstraint('current_step_order IS NULL OR current_step_order > 0', 
                          name='ck_execution_step_order_positive'),
        sa.CheckConstraint('steps_completed >= 0', name='ck_execution_completed_positive'),
        sa.CheckConstraint('steps_skipped >= 0', name='ck_execution_skipped_positive'),
    )
    
    # Create indexes for execution queries
    op.create_index('ix_executions_fermentation_id', 'protocol_executions', ['fermentation_id'])
    op.create_index('ix_executions_protocol_id', 'protocol_executions', ['protocol_id'])
    op.create_index('ix_executions_winery_id', 'protocol_executions', ['winery_id'])
    op.create_index('ix_executions_status', 'protocol_executions', ['status'])
    
    # Create step_completions table
    op.create_table(
        'step_completions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('execution_id', sa.Integer(), nullable=False),
        sa.Column('step_id', sa.Integer(), nullable=False),
        sa.Column('completed_by', sa.Integer(), nullable=False),
        sa.Column('is_skipped', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('skip_reason', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['execution_id'], ['protocol_executions.id'], 
                              ondelete='CASCADE', name='fk_completions_execution'),
        sa.ForeignKeyConstraint(['step_id'], ['protocol_steps.id'], 
                              name='fk_completions_step'),
        sa.ForeignKeyConstraint(['completed_by'], ['users.id'], 
                              name='fk_completions_user'),
        sa.UniqueConstraint('execution_id', 'step_id', name='uq_completion_execution_step'),
        sa.CheckConstraint('is_skipped IN (0, 1)', name='ck_completion_skipped_bool'),
    )
    
    # Create indexes for completion queries
    op.create_index('ix_completions_execution_id', 'step_completions', ['execution_id'])
    op.create_index('ix_completions_step_id', 'step_completions', ['step_id'])
    op.create_index('ix_completions_created_at', 'step_completions', ['created_at'])


def downgrade() -> None:
    # Drop tables in reverse order of creation (respect foreign keys)
    op.drop_table('step_completions')
    op.drop_table('protocol_executions')
    op.drop_table('protocol_steps')
    op.drop_table('fermentation_protocols')
