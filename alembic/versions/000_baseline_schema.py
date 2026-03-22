"""Baseline schema: all non-protocol foundation tables

Revision ID: 000_baseline_schema
Revises: None
Create Date: 2026-03-21

Creates every foundational table needed by the wine fermentation system.
Protocol-specific tables are handled by the subsequent migrations (001-006).

Tables created here:
  Multi-tenancy root:
    - wineries
    - users
  Fruit origin / traceability (ADR-001):
    - vineyards
    - vineyard_blocks
    - harvest_lots
  Fermentation core:
    - fermentations
    - fermentation_notes
    - fermentation_lot_sources
    - samples  (single-table inheritance, all sample subtypes share this table)
  Analysis engine (UUIDs throughout):
    - recommendation_template
    - analysis
    - anomaly
    - recommendation

NOT included here (covered by migrations 001-006):
    - fermentation_protocols, protocol_steps, protocol_executions,
      step_completions, protocol_alerts, protocol_advisory
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

# revision identifiers, used by Alembic.
revision: str = "000_baseline_schema"
down_revision: Union[str, None] = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:

    # =========================================================================
    # 1. wineries  —  top-level tenant root
    # =========================================================================
    op.create_table(
        'wineries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('location', sa.String(100), nullable=True),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_wineries__name'),
        sa.UniqueConstraint('code', name='uq_wineries__code'),
    )
    op.create_index('ix_wineries_code', 'wineries', ['code'])
    op.create_index('ix_wineries_name', 'wineries', ['name'])

    # =========================================================================
    # 2. users  —  winemakers / staff, scoped to a winery
    # =========================================================================
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('winery_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='viewer'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['winery_id'], ['wineries.id'], name='fk_users_winery'),
        sa.UniqueConstraint('username', name='uq_users_username'),
        sa.UniqueConstraint('email', name='uq_users_email'),
    )
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_email', 'users', ['email'])

    # =========================================================================
    # 3. vineyards  —  top-level geographic locations (ADR-001)
    # =========================================================================
    op.create_table(
        'vineyards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('winery_id', sa.BigInteger(), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('notes', sa.String(255), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['winery_id'], ['wineries.id'], name='fk_vineyards_winery'),
        sa.UniqueConstraint('code', 'winery_id', name='uq_vineyards__code__winery_id'),
    )
    op.create_index('ix_vineyards_winery_id', 'vineyards', ['winery_id'])

    # =========================================================================
    # 4. vineyard_blocks  —  parcels with technical specifications (ADR-001)
    # =========================================================================
    op.create_table(
        'vineyard_blocks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vineyard_id', sa.BigInteger(), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('soil_type', sa.String(50), nullable=True),
        sa.Column('slope_pct', sa.Numeric(5, 2), nullable=True),
        sa.Column('aspect_deg', sa.Numeric(5, 2), nullable=True),
        sa.Column('area_ha', sa.Numeric(8, 3), nullable=True),
        sa.Column('elevation_m', sa.Numeric(8, 2), nullable=True),
        sa.Column('latitude', sa.Numeric(9, 6), nullable=True),
        sa.Column('longitude', sa.Numeric(9, 6), nullable=True),
        sa.Column('notes', sa.String(255), nullable=True),
        sa.Column('irrigation', sa.Boolean(), nullable=True),
        sa.Column('organic_certified', sa.Boolean(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['vineyard_id'], ['vineyards.id'], name='fk_vineyard_blocks_vineyard'),
        sa.UniqueConstraint('code', 'vineyard_id', name='uq_vineyard_blocks__code__vineyard_id'),
    )
    op.create_index('ix_vineyard_blocks_vineyard_id', 'vineyard_blocks', ['vineyard_id'])

    # =========================================================================
    # 5. harvest_lots  —  specific harvest events with full traceability (ADR-001)
    # =========================================================================
    op.create_table(
        'harvest_lots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('winery_id', sa.BigInteger(), nullable=False),
        sa.Column('block_id', sa.BigInteger(), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('harvest_date', sa.Date(), nullable=False),
        sa.Column('weight_kg', sa.Numeric(10, 2), nullable=False),
        sa.Column('brix_at_harvest', sa.Numeric(5, 2), nullable=True),
        sa.Column('brix_method', sa.String(50), nullable=True),
        sa.Column('brix_measured_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('grape_variety', sa.String(100), nullable=True),
        sa.Column('clone', sa.String(50), nullable=True),
        sa.Column('rootstock', sa.String(50), nullable=True),
        sa.Column('pick_method', sa.String(20), nullable=True),
        sa.Column('pick_start_time', sa.String(50), nullable=True),
        sa.Column('pick_end_time', sa.String(50), nullable=True),
        sa.Column('bins_count', sa.Integer(), nullable=True),
        sa.Column('field_temp_c', sa.Numeric(5, 2), nullable=True),
        sa.Column('notes', sa.String(255), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['winery_id'], ['wineries.id'], name='fk_harvest_lots_winery'),
        sa.ForeignKeyConstraint(['block_id'], ['vineyard_blocks.id'], name='fk_harvest_lots_block'),
        sa.UniqueConstraint('code', 'winery_id', name='uq_harvest_lots__code__winery_id'),
    )
    op.create_index('ix_harvest_lots_winery_id', 'harvest_lots', ['winery_id'])
    op.create_index('ix_harvest_lots_block_id', 'harvest_lots', ['block_id'])
    op.create_index('ix_harvest_lots_harvest_date', 'harvest_lots', ['harvest_date'])
    op.create_index('ix_harvest_lots_code', 'harvest_lots', ['code'])

    # =========================================================================
    # 6. fermentations  —  core production batches
    # =========================================================================
    op.create_table(
        'fermentations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fermented_by_user_id', sa.Integer(), nullable=False),
        sa.Column('winery_id', sa.Integer(), nullable=False),
        sa.Column('vintage_year', sa.Integer(), nullable=False),
        sa.Column('yeast_strain', sa.String(100), nullable=False),
        sa.Column('vessel_code', sa.String(50), nullable=True),
        sa.Column('input_mass_kg', sa.Float(), nullable=False),
        sa.Column('initial_sugar_brix', sa.Float(), nullable=False),
        sa.Column('initial_density', sa.Float(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='ACTIVE'),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('data_source', sa.String(20), nullable=False, server_default='system'),
        sa.Column('imported_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['fermented_by_user_id'], ['users.id'], name='fk_fermentations_user'),
        sa.ForeignKeyConstraint(['winery_id'], ['wineries.id'], name='fk_fermentations_winery'),
        sa.UniqueConstraint('winery_id', 'vessel_code', name='uq_fermentations__winery_id__vessel_code'),
    )
    op.create_index('ix_fermentations_fermented_by_user_id', 'fermentations', ['fermented_by_user_id'])
    op.create_index('ix_fermentations_winery_id', 'fermentations', ['winery_id'])
    op.create_index('ix_fermentations_data_source', 'fermentations', ['data_source'])

    # =========================================================================
    # 7. fermentation_notes  —  winemaker log entries
    # =========================================================================
    op.create_table(
        'fermentation_notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fermentation_id', sa.Integer(), nullable=False),
        sa.Column('created_by_user_id', sa.Integer(), nullable=False),
        sa.Column('note_text', sa.Text(), nullable=False),
        sa.Column('action_taken', sa.String(255), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['fermentation_id'], ['fermentations.id'],
                                name='fk_fermentation_notes_fermentation'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'],
                                name='fk_fermentation_notes_user'),
    )
    op.create_index('ix_fermentation_notes_fermentation_id', 'fermentation_notes', ['fermentation_id'])

    # =========================================================================
    # 8. fermentation_lot_sources  —  fermentation ↔ harvest lot blend tracking
    # =========================================================================
    op.create_table(
        'fermentation_lot_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fermentation_id', sa.Integer(), nullable=False),
        sa.Column('harvest_lot_id', sa.Integer(), nullable=False),
        sa.Column('mass_used_kg', sa.Float(), nullable=False),
        sa.Column('notes', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['fermentation_id'], ['fermentations.id'],
                                name='fk_fermentation_lot_sources_fermentation'),
        sa.ForeignKeyConstraint(['harvest_lot_id'], ['harvest_lots.id'],
                                name='fk_fermentation_lot_sources_harvest_lot'),
        sa.UniqueConstraint('fermentation_id', 'harvest_lot_id',
                            name='uq_fermentation_lot_source_fermentation_harvest'),
        sa.CheckConstraint('mass_used_kg > 0', name='ck_fermentation_lot_source_mass_positive'),
    )
    op.create_index('idx_fermentation_lot_source_fermentation',
                    'fermentation_lot_sources', ['fermentation_id'])
    op.create_index('idx_fermentation_lot_source_harvest_lot',
                    'fermentation_lot_sources', ['harvest_lot_id'])

    # =========================================================================
    # 9. samples  —  single-table inheritance for all measurement types
    # =========================================================================
    op.create_table(
        'samples',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sample_type', sa.String(50), nullable=False),
        sa.Column('fermentation_id', sa.Integer(), nullable=False),
        sa.Column('recorded_at', sa.DateTime(), nullable=False),
        sa.Column('recorded_by_user_id', sa.Integer(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('data_source', sa.String(20), nullable=False, server_default='system'),
        sa.Column('imported_at', sa.DateTime(), nullable=True),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('units', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['fermentation_id'], ['fermentations.id'],
                                name='fk_samples_fermentation'),
    )
    op.create_index('ix_samples_sample_type', 'samples', ['sample_type'])
    op.create_index('ix_samples_fermentation_id', 'samples', ['fermentation_id'])
    op.create_index('ix_samples_recorded_at', 'samples', ['recorded_at'])
    op.create_index('ix_samples_data_source', 'samples', ['data_source'])

    # =========================================================================
    # 10. recommendation_template  —  catalog of reusable recommendation patterns
    # =========================================================================
    op.create_table(
        'recommendation_template',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(100), nullable=True),
        sa.Column('title', sa.String(200), nullable=True),
        sa.Column('description', sa.String(1000), nullable=True),
        sa.Column('recommendation_text', sa.String(1000), nullable=True),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('applicable_anomaly_types', ARRAY(sa.String()), nullable=True),
        sa.Column('priority_default', sa.Integer(), nullable=True),
        sa.Column('effectiveness_score', sa.Integer(), nullable=True),
        sa.Column('times_applied', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uq_recommendation_template_code'),
    )
    op.create_index('ix_recommendation_template_code', 'recommendation_template', ['code'], unique=True)
    op.create_index('ix_recommendation_template_category', 'recommendation_template', ['category'])
    op.create_index('ix_recommendation_template_is_active', 'recommendation_template', ['is_active'])

    # =========================================================================
    # 11. analysis  —  aggregate root for fermentation analysis (UUID PK)
    # =========================================================================
    op.create_table(
        'analysis',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('fermentation_id', UUID(as_uuid=True), nullable=False),
        sa.Column('winery_id', UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('analyzed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('comparison_result', JSONB(), nullable=False),
        sa.Column('confidence_level', JSONB(), nullable=False),
        sa.Column('historical_samples_count', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_analysis_winery_id', 'analysis', ['winery_id'])
    op.create_index('ix_analysis_fermentation_id', 'analysis', ['fermentation_id'])
    op.create_index('ix_analysis_status', 'analysis', ['status'])
    op.create_index('ix_analysis_analyzed_at', 'analysis', ['analyzed_at'])
    op.create_index('ix_analysis_winery_fermentation', 'analysis', ['winery_id', 'fermentation_id'])
    op.create_index('ix_analysis_winery_status', 'analysis', ['winery_id', 'status'])

    # =========================================================================
    # 12. anomaly  —  detected problems within an analysis (UUID PK)
    # =========================================================================
    op.create_table(
        'anomaly',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('analysis_id', UUID(as_uuid=True), nullable=False),
        sa.Column('sample_id', UUID(as_uuid=True), nullable=False),
        sa.Column('anomaly_type', sa.String(100), nullable=False),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('description', sa.String(500), nullable=False),
        sa.Column('deviation_score', JSONB(), nullable=False),
        sa.Column('is_resolved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['analysis_id'], ['analysis.id'],
                                ondelete='CASCADE', name='fk_anomaly_analysis'),
    )
    op.create_index('ix_anomaly_analysis_id', 'anomaly', ['analysis_id'])
    op.create_index('ix_anomaly_sample_id', 'anomaly', ['sample_id'])
    op.create_index('ix_anomaly_type', 'anomaly', ['anomaly_type'])
    op.create_index('ix_anomaly_severity', 'anomaly', ['severity'])
    op.create_index('ix_anomaly_is_resolved', 'anomaly', ['is_resolved'])
    op.create_index('ix_anomaly_detected_at', 'anomaly', ['detected_at'])
    op.create_index('ix_anomaly_type_severity', 'anomaly', ['anomaly_type', 'severity'])

    # =========================================================================
    # 13. recommendation  —  suggested actions for detected anomalies (UUID PK)
    # =========================================================================
    op.create_table(
        'recommendation',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('analysis_id', UUID(as_uuid=True), nullable=False),
        sa.Column('anomaly_id', UUID(as_uuid=True), nullable=True),
        sa.Column('recommendation_template_id', UUID(as_uuid=True), nullable=False),
        sa.Column('recommendation_text', sa.String(1000), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('supporting_evidence_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('estimated_effectiveness', sa.Integer(), nullable=True),
        sa.Column('is_applied', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('applied_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['analysis_id'], ['analysis.id'],
                                ondelete='CASCADE', name='fk_recommendation_analysis'),
        sa.ForeignKeyConstraint(['anomaly_id'], ['anomaly.id'],
                                ondelete='SET NULL', name='fk_recommendation_anomaly'),
        sa.ForeignKeyConstraint(['recommendation_template_id'], ['recommendation_template.id'],
                                name='fk_recommendation_template'),
    )
    op.create_index('ix_recommendation_analysis_id', 'recommendation', ['analysis_id'])
    op.create_index('ix_recommendation_anomaly_id', 'recommendation', ['anomaly_id'])
    op.create_index('ix_recommendation_template_id', 'recommendation', ['recommendation_template_id'])
    op.create_index('ix_recommendation_priority', 'recommendation', ['priority'])
    op.create_index('ix_recommendation_is_applied', 'recommendation', ['is_applied'])


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_table('recommendation')
    op.drop_table('anomaly')
    op.drop_table('analysis')
    op.drop_table('recommendation_template')
    op.drop_table('samples')
    op.drop_table('fermentation_lot_sources')
    op.drop_table('fermentation_notes')
    op.drop_table('fermentations')
    op.drop_table('harvest_lots')
    op.drop_table('vineyard_blocks')
    op.drop_table('vineyards')
    op.drop_table('users')
    op.drop_table('wineries')
