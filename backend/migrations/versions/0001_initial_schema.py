"""Initial schema with pgvector and all Phase 1 tables

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-09-20 17:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from backend.models.types import JSONType, ArrayType, VectorType

revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='researcher'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. research_projects table
    op.create_table(
        'research_projects',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('research_questions', JSONType, nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_research_projects_name'), 'research_projects', ['name'], unique=True)

    # 3. ingestion_jobs table
    op.create_table(
        'ingestion_jobs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='queued'),
        sa.Column('config', JSONType, nullable=False),
        sa.Column('records_found', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('records_stored', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_heartbeat_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_details', JSONType, nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['research_projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ingestion_jobs_project_id'), 'ingestion_jobs', ['project_id'], unique=False)

    # 4. source_records table
    op.create_table(
        'source_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('source_platform', sa.String(length=50), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('source_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('raw_content', sa.Text(), nullable=False),
        sa.Column('author_handle', sa.String(length=255), nullable=False),
        sa.Column('collection_method', sa.String(length=50), nullable=False),
        sa.Column('collection_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ingestion_job_id', sa.String(length=36), nullable=True),
        sa.Column('is_duplicate', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('dedup_hash', sa.String(length=64), nullable=False),
        sa.Column('metadata', JSONType, nullable=False),
        sa.Column('language', sa.String(length=20), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['ingestion_job_id'], ['ingestion_jobs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['research_projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'dedup_hash', name='uq_project_dedup_hash'),
    )
    op.create_index(op.f('ix_source_records_project_id'), 'source_records', ['project_id'], unique=False)
    op.create_index(op.f('ix_source_records_source_platform'), 'source_records', ['source_platform'], unique=False)
    op.create_index(op.f('ix_source_records_dedup_hash'), 'source_records', ['dedup_hash'], unique=False)

    # 5. model_runs table
    op.create_table(
        'model_runs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('prompt_version', sa.String(length=50), nullable=False),
        sa.Column('parameters', JSONType, nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='queued'),
        sa.Column('records_total', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('records_success', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('records_failed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_log', JSONType, nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['research_projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_model_runs_project_id'), 'model_runs', ['project_id'], unique=False)

    # 6. taxonomy_categories table
    op.create_table(
        'taxonomy_categories',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('definition', sa.Text(), nullable=False),
        sa.Column('user_segment', sa.String(length=100), nullable=True),
        sa.Column('common_memory_cues', JSONType, nullable=False),
        sa.Column('missing_information', sa.Text(), nullable=True),
        sa.Column('common_search_behavior', sa.Text(), nullable=True),
        sa.Column('failure_mechanism', sa.Text(), nullable=False),
        sa.Column('evidence_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unique_author_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('source_diversity', JSONType, nullable=False),
        sa.Column('representative_excerpts', ArrayType(), nullable=False),
        sa.Column('confidence_level', sa.String(length=20), nullable=False, server_default='high'),
        sa.Column('open_questions', ArrayType(), nullable=False),
        sa.Column('product_implications', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['research_projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_taxonomy_categories_project_id'), 'taxonomy_categories', ['project_id'], unique=False)

    # 7. opportunity_areas table
    op.create_table(
        'opportunity_areas',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('taxonomy_category_id', sa.String(length=36), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('evidence_frequency', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('evidence_diversity', JSONType, nullable=False),
        sa.Column('unique_author_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('user_impact_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('abandonment_rate', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('workaround_exists', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('strategic_relevance', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('problem_clarity', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('potential_reach', sa.String(length=100), nullable=True),
        sa.Column('validation_effort', sa.String(length=50), nullable=False, server_default='medium'),
        sa.Column('scoring_methodology', sa.Text(), nullable=True),
        sa.Column('analyst_notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='draft'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['research_projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['taxonomy_category_id'], ['taxonomy_categories.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_opportunity_areas_project_id'), 'opportunity_areas', ['project_id'], unique=False)

    # 8. evidence_records table
    op.create_table(
        'evidence_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('source_record_id', sa.String(length=36), nullable=False),
        sa.Column('model_run_id', sa.String(length=36), nullable=True),
        sa.Column('is_relevant', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('relevance_labels', ArrayType(), nullable=False),
        sa.Column('retrieval_scenario', sa.String(length=255), nullable=True),
        sa.Column('memory_cues', JSONType, nullable=False),
        sa.Column('missing_information', sa.Text(), nullable=True),
        sa.Column('search_behavior', sa.Text(), nullable=True),
        sa.Column('retrieval_outcome', sa.String(length=50), nullable=True),
        sa.Column('failure_points', ArrayType(), nullable=False),
        sa.Column('user_segment', sa.String(length=100), nullable=True),
        sa.Column('evidence_excerpt', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('needs_human_review', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('is_genuine_experience', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('embedding', VectorType(768), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['model_run_id'], ['model_runs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['source_record_id'], ['source_records.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_evidence_records_source_record_id'), 'evidence_records', ['source_record_id'], unique=False)
    op.create_index(op.f('ix_evidence_records_is_relevant'), 'evidence_records', ['is_relevant'], unique=False)
    op.create_index(op.f('ix_evidence_records_confidence_score'), 'evidence_records', ['confidence_score'], unique=False)
    op.create_index(op.f('ix_evidence_records_needs_human_review'), 'evidence_records', ['needs_human_review'], unique=False)

    # 9. human_reviews table
    op.create_table(
        'human_reviews',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('evidence_record_id', sa.String(length=36), nullable=False),
        sa.Column('reviewer_id', sa.String(length=255), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('corrections', JSONType, nullable=True),
        sa.Column('reviewer_notes', sa.Text(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['evidence_record_id'], ['evidence_records.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_human_reviews_evidence_record_id'), 'human_reviews', ['evidence_record_id'], unique=False)


def downgrade() -> None:
    op.drop_table('human_reviews')
    op.drop_table('evidence_records')
    op.drop_table('opportunity_areas')
    op.drop_table('taxonomy_categories')
    op.drop_table('model_runs')
    op.drop_table('source_records')
    op.drop_table('ingestion_jobs')
    op.drop_table('research_projects')
    op.drop_table('users')
