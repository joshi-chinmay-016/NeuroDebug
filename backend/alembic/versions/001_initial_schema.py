"""Initial schema creation

Revision ID: 001
Revises:
Create Date: 2025-01-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create subscription_plans table
    op.create_table(
        'subscription_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('tier', sa.String(length=20), nullable=False),
        sa.Column('daily_request_limit', sa.Integer(), nullable=False),
        sa.Column('max_projects', sa.Integer(), nullable=True),
        sa.Column('features', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('price_monthly', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('name'),
        sa.Index('ix_subscription_plans_deleted_at', 'deleted_at'),
        sa.Index('ix_subscription_plans_is_active', 'is_active'),
        sa.Index('ix_subscription_plans_tier', 'tier')
    )

    # Create subscription_limits table
    op.create_table(
        'subscription_limits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('plan_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('limit_type', sa.String(length=50), nullable=False),
        sa.Column('limit_value', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['plan_id'], ['subscription_plans.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('plan_id', 'limit_type', name='uq_plan_limit'),
        sa.Index('ix_subscription_limits_plan_id', 'plan_id'),
        sa.Index('ix_subscription_limits_limit_type', 'limit_type')
    )

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('display_name', sa.String(length=100), nullable=True),
        sa.Column('subscription_plan_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['subscription_plan_id'], ['subscription_plans.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('email'),
        sa.Index('ix_users_deleted_at', 'deleted_at'),
        sa.Index('ix_users_email', 'email'),
        sa.Index('ix_users_subscription_plan_id', 'subscription_plan_id')
    )

    # Create projects table
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.Index('ix_projects_deleted_at', 'deleted_at'),
        sa.Index('ix_projects_session_id', 'session_id'),
        sa.Index('ix_projects_user_id', 'user_id')
    )

    # Create debug_sessions table
    op.create_table(
        'debug_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('code', sa.Text(), nullable=False),
        sa.Column('error_type', sa.String(length=100), nullable=True),
        sa.Column('confidence_score', sa.Integer(), nullable=True),
        sa.Column('pipeline_duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('session_id', 'code', name='uq_session_code'),
        sa.Index('ix_debug_sessions_deleted_at', 'deleted_at'),
        sa.Index('ix_debug_sessions_error_type', 'error_type'),
        sa.Index('ix_debug_sessions_project_id', 'project_id'),
        sa.Index('ix_debug_sessions_session_id', 'session_id'),
        sa.Index('ix_debug_sessions_user_id', 'user_id')
    )

    # Create candidate_patches table
    op.create_table(
        'candidate_patches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('debug_session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('original_code', sa.Text(), nullable=False),
        sa.Column('patched_code', sa.Text(), nullable=False),
        sa.Column('diff', sa.Text(), nullable=True),
        sa.Column('validation_passed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('llm_model', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['debug_session_id'], ['debug_sessions.id'], ondelete='CASCADE'),
        sa.Index('ix_candidate_patches_debug_session_id', 'debug_session_id'),
        sa.Index('ix_candidate_patches_deleted_at', 'deleted_at')
    )

    # Create verification_reports table
    op.create_table(
        'verification_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('debug_session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('candidate_patch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('verification_status', sa.String(length=20), nullable=False),
        sa.Column('execution_summary', sa.Text(), nullable=False),
        sa.Column('runtime_seconds', sa.Integer(), nullable=False),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('evidence', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['candidate_patch_id'], ['candidate_patches.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['debug_session_id'], ['debug_sessions.id'], ondelete='CASCADE'),
        sa.Index('ix_verification_reports_candidate_patch_id', 'candidate_patch_id'),
        sa.Index('ix_verification_reports_debug_session_id', 'debug_session_id'),
        sa.Index('ix_verification_reports_deleted_at', 'deleted_at'),
        sa.Index('ix_verification_reports_verification_status', 'verification_status')
    )

    # Create usage_logs table
    op.create_table(
        'usage_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=False),
        sa.Column('request_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('execution_time_ms', sa.Integer(), nullable=False),
        sa.Column('verification_status', sa.String(length=20), nullable=True),
        sa.Column('patch_success', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('pipeline_runtime_ms', sa.Integer(), nullable=True),
        sa.Column('llm_runtime_ms', sa.Integer(), nullable=True),
        sa.Column('subscription_tier', sa.String(length=20), nullable=False),
        sa.Column('daily_usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('session_id', 'request_timestamp', name='uq_session_timestamp'),
        sa.Index('ix_usage_logs_request_timestamp', 'request_timestamp'),
        sa.Index('ix_usage_logs_session_id', 'session_id'),
        sa.Index('ix_usage_logs_subscription_tier', 'subscription_tier'),
        sa.Index('ix_usage_logs_user_id', 'user_id'),
        sa.Index('ix_usage_logs_verification_status', 'verification_status')
    )


def downgrade() -> None:
    op.drop_table('usage_logs')
    op.drop_table('verification_reports')
    op.drop_table('candidate_patches')
    op.drop_table('debug_sessions')
    op.drop_table('projects')
    op.drop_table('users')
    op.drop_table('subscription_limits')
    op.drop_table('subscription_plans')
