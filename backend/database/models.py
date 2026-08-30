"""
Database models for NeuroDebug SaaS platform.

All models use UUID primary keys, timestamps, and soft delete support.
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    JSON,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from utils.config import Config

from database.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

# Cross-dialect JSON: Uses JSONB in PostgreSQL, JSON in SQLite (for unit tests)
JsonType = JSON().with_variant(JSONB, "postgresql")

__all__ = [
    "CandidatePatch",
    "DebugSession",
    "Project",
    "SubscriptionLimit",
    "SubscriptionPlan",
    "SubscriptionTier",
    "UsageLog",
    "User",
    "UserProfile",
    "VerificationReport",
    "VerificationStatus",
]


class SubscriptionTier(str, Enum):
    """Subscription tier enumeration."""

    GUEST = "guest"
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class VerificationStatus(str, Enum):
    """Verification status enumeration."""

    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    SANDBOX_ERROR = "SANDBOX_ERROR"
    NOT_VERIFIABLE = "NOT_VERIFIABLE"
    RUNNING = "RUNNING"
    NOT_RUN = "NOT_RUN"
    UNVERIFIED = "UNVERIFIED"
    FAILED_VERIFICATION = "FAILED_VERIFICATION"
    NO_FIX_FOUND = "NO_FIX_FOUND"
    INVALID_PATCH = "INVALID_PATCH"
    EXECUTION_TIMEOUT = "EXECUTION_TIMEOUT"
    TEST_FAILURE = "TEST_FAILURE"
    EXECUTION_ERROR = "EXECUTION_ERROR"
    VERIFICATION_UNAVAILABLE = "VERIFICATION_UNAVAILABLE"


# ──────────────────────────────────────────────────────────────────
# Subscription Models
# ──────────────────────────────────────────────────────────────────


class SubscriptionPlan(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Subscription plan definition model."""

    __tablename__ = "subscription_plans"

    name: Mapped[str] = mapped_column(String(50), nullable=False)
    tier: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    daily_request_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    max_projects: Mapped[int] = mapped_column(Integer, nullable=False)
    features: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict)
    price_monthly: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )  # In cents
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    limits: Mapped[list["SubscriptionLimit"]] = relationship(
        "SubscriptionLimit",
        back_populates="plan",
        cascade="all, delete-orphan",
    )
    users: Mapped[list["User"]] = relationship(
        "User", back_populates="subscription_plan", cascade="all, delete-orphan"
    )


class SubscriptionLimit(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Configurable limits for subscription plans."""

    __tablename__ = "subscription_limits"

    plan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("subscription_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    limit_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    limit_value: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    plan: Mapped["SubscriptionPlan"] = relationship(
        "SubscriptionPlan", back_populates="limits"
    )

    __table_args__ = (UniqueConstraint("plan_id", "limit_type", name="uq_plan_limit"),)


# ──────────────────────────────────────────────────────────────────
# User Models
# ──────────────────────────────────────────────────────────────────


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """User account model."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subscription_plan_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("subscription_plans.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    subscription_plan: Mapped["SubscriptionPlan"] = relationship(
        "SubscriptionPlan", back_populates="users"
    )
    profile: Mapped["UserProfile"] = relationship(
        "UserProfile", back_populates="user", cascade="all, delete-orphan"
    )
    projects: Mapped[list["Project"]] = relationship(
        "Project", back_populates="user", cascade="all, delete-orphan"
    )
    debug_sessions: Mapped[list["DebugSession"]] = relationship(
        "DebugSession", back_populates="user", cascade="all, delete-orphan"
    )
    usage_logs: Mapped[list["UsageLog"]] = relationship(
        "UsageLog", back_populates="user", cascade="all, delete-orphan"
    )


class UserProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """User profile model for settings and preferences."""

    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    theme: Mapped[str] = mapped_column(String(20), nullable=False, default="light")
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="UTC")
    editor_font_size: Mapped[int] = mapped_column(Integer, nullable=False, default=14)
    editor_theme: Mapped[str] = mapped_column(
        String(50), nullable=False, default="vs-dark"
    )
    notifications_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    email_notifications: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    api_keys: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict)
    preferences: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="profile")


# ──────────────────────────────────────────────────────────────────
# Project Models
# ──────────────────────────────────────────────────────────────────


class Project(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Project model for organizing debug sessions."""

    __tablename__ = "projects"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    session_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="projects")
    debug_sessions: Mapped[list["DebugSession"]] = relationship(
        "DebugSession", back_populates="project", cascade="all, delete-orphan"
    )


# ──────────────────────────────────────────────────────────────────
# Debug Session Models
# ──────────────────────────────────────────────────────────────────


class DebugSession(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Debug session model for tracking debugging requests."""

    __tablename__ = "debug_sessions"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    code: Mapped[str] = mapped_column(Text, nullable=False)
    error_type: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )
    confidence_score: Mapped[float | None] = mapped_column(Integer, nullable=True)
    pipeline_duration_ms: Mapped[float | None] = mapped_column(Integer, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="debug_sessions")
    project: Mapped["Project"] = relationship(
        "Project", back_populates="debug_sessions"
    )
    candidate_patches: Mapped[list["CandidatePatch"]] = relationship(
        "CandidatePatch", back_populates="debug_session", cascade="all, delete-orphan"
    )
    verification_reports: Mapped[list["VerificationReport"]] = relationship(
        "VerificationReport",
        back_populates="debug_session",
        cascade="all, delete-orphan",
    )

    __table_args__ = (UniqueConstraint("session_id", "code", name="uq_session_code"),)


# ──────────────────────────────────────────────────────────────────
# Candidate Patch Models
# ──────────────────────────────────────────────────────────────────


class CandidatePatch(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Candidate patch model for generated fixes."""

    __tablename__ = "candidate_patches"

    debug_session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("debug_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_code: Mapped[str] = mapped_column(Text, nullable=False)
    patched_code: Mapped[str] = mapped_column(Text, nullable=False)
    diff: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation_passed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    debug_session: Mapped["DebugSession"] = relationship(
        "DebugSession", back_populates="candidate_patches"
    )
    verification_reports: Mapped[list["VerificationReport"]] = relationship(
        "VerificationReport",
        back_populates="candidate_patch",
        cascade="all, delete-orphan",
    )


# ──────────────────────────────────────────────────────────────────
# Verification Report Models
# ──────────────────────────────────────────────────────────────────


class VerificationReport(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Verification report model for patch execution results."""

    __tablename__ = "verification_reports"

    debug_session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("debug_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    candidate_patch_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("candidate_patches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    verification_status: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )
    execution_summary: Mapped[str] = mapped_column(Text, nullable=False)
    runtime_seconds: Mapped[float] = mapped_column(Integer, nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict)

    # Relationships
    debug_session: Mapped["DebugSession"] = relationship(
        "DebugSession", back_populates="verification_reports"
    )
    candidate_patch: Mapped["CandidatePatch"] = relationship(
        "CandidatePatch", back_populates="verification_reports"
    )


# ──────────────────────────────────────────────────────────────────
# Usage Log Models
# ──────────────────────────────────────────────────────────────────


class UsageLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Usage log model for tracking API usage and analytics."""

    __tablename__ = "usage_logs"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    request_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    execution_time_ms: Mapped[float] = mapped_column(Integer, nullable=False)
    verification_status: Mapped[str | None] = mapped_column(
        String(20), nullable=True, index=True
    )
    patch_success: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    pipeline_runtime_ms: Mapped[float | None] = mapped_column(Integer, nullable=True)
    llm_runtime_ms: Mapped[float | None] = mapped_column(Integer, nullable=True)
    subscription_tier: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )
    daily_usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="usage_logs")

    __table_args__ = (
        UniqueConstraint(
            "session_id", "request_timestamp", name="uq_session_timestamp"
        ),
    )
