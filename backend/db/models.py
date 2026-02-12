import enum
from datetime import datetime

from sqlalchemy import (
    String, Integer, DateTime, ForeignKey, JSON, Text, Index, func,
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.session import Base


# ---------------------------------------------------------------------------
# ENUM definitions
# ---------------------------------------------------------------------------

class ExperienceLevel(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class PrimaryGoal(str, enum.Enum):
    trading = "trading"
    long_term_investing = "long_term_investing"
    research_analysis = "research_analysis"


class InvestorType(str, enum.Enum):
    retail = "retail"
    student = "student"
    professional = "professional"


class PortfolioSize(str, enum.Enum):
    size_0_500k = "0_500k"
    size_500k_10m = "500k_10m"
    size_10m_plus = "10m_plus"


class SubscriptionStatus(str, enum.Enum):
    free = "free"
    premium = "premium"


# ---------------------------------------------------------------------------
# User model
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_username", "username", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    firebase_uid: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)

    # Profile fields
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    username: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(256), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # PIN security
    pin_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    pin_failed_attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    pin_locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pin_set_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    subscription: Mapped["Subscription"] = relationship(
        "Subscription", uselist=False, back_populates="user", cascade="all, delete-orphan",
    )
    onboarding: Mapped["UserOnboarding"] = relationship(
        "UserOnboarding", uselist=False, back_populates="user", cascade="all, delete-orphan",
    )


# ---------------------------------------------------------------------------
# UserOnboarding model
# ---------------------------------------------------------------------------

class UserOnboarding(Base):
    __tablename__ = "user_onboarding"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)

    experience_level: Mapped[ExperienceLevel] = mapped_column(
        SAEnum(ExperienceLevel, name="experience_level", create_constraint=True, native_enum=False, length=20),
        nullable=False,
    )
    primary_goal: Mapped[PrimaryGoal] = mapped_column(
        SAEnum(PrimaryGoal, name="primary_goal", create_constraint=True, native_enum=False, length=30),
        nullable=False,
    )
    investor_type: Mapped[InvestorType | None] = mapped_column(
        SAEnum(InvestorType, name="investor_type", create_constraint=True, native_enum=False, length=20),
        nullable=True,
    )
    portfolio_size: Mapped[PortfolioSize | None] = mapped_column(
        SAEnum(PortfolioSize, name="portfolio_size", create_constraint=True, native_enum=False, length=20),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="onboarding")


# ---------------------------------------------------------------------------
# Subscription model
# ---------------------------------------------------------------------------

class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)

    status: Mapped[SubscriptionStatus] = mapped_column(
        SAEnum(SubscriptionStatus, name="subscription_status", create_constraint=True, native_enum=False, length=20),
        default=SubscriptionStatus.free,
        server_default="free",
        nullable=False,
    )
    plan_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="subscription")


# ---------------------------------------------------------------------------
# Job model (unchanged)
# ---------------------------------------------------------------------------

class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    job_type: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="PENDING")

    payload: Mapped[dict] = mapped_column(JSON, default={})
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
