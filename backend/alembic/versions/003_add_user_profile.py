"""Add user_profiles table

Revision ID: 003
Revises: 002
Create Date: 2025-01-20 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_profiles",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column(
            "theme", sa.String(length=20), nullable=False, server_default="light"
        ),
        sa.Column(
            "language", sa.String(length=10), nullable=False, server_default="en"
        ),
        sa.Column(
            "timezone", sa.String(length=50), nullable=False, server_default="UTC"
        ),
        sa.Column(
            "editor_font_size", sa.Integer(), nullable=False, server_default="14"
        ),
        sa.Column(
            "editor_theme",
            sa.String(length=50),
            nullable=False,
            server_default="vs-dark",
        ),
        sa.Column(
            "notifications_enabled", sa.Boolean(), nullable=False, server_default="true"
        ),
        sa.Column(
            "email_notifications", sa.Boolean(), nullable=False, server_default="true"
        ),
        sa.Column("api_keys", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column(
            "preferences", postgresql.JSONB(), nullable=False, server_default="{}"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id"),
        sa.Index("ix_user_profiles_deleted_at", "deleted_at"),
        sa.Index("ix_user_profiles_user_id", "user_id"),
    )


def downgrade() -> None:
    op.drop_table("user_profiles")
