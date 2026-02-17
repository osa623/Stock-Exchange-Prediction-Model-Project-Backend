import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    String, Integer, DateTime, ForeignKey, JSON, Text, Index, func,
    Enum as SAEnum, Numeric, UniqueConstraint,
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
    pin_lockout_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)

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
    security_events: Mapped[list["SecurityEvent"]] = relationship(
        "SecurityEvent", back_populates="user", cascade="all, delete-orphan",
        order_by="SecurityEvent.created_at.desc()", lazy="dynamic",
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


# ---------------------------------------------------------------------------
# Portfolio enums
# ---------------------------------------------------------------------------

class PortfolioSourceType(str, enum.Enum):
    manual = "manual"
    excel = "excel"
    mixed = "mixed"


class ImportStatus(str, enum.Enum):
    received = "received"
    parsed = "parsed"
    failed = "failed"


# ---------------------------------------------------------------------------
# Portfolio model
# ---------------------------------------------------------------------------

class Portfolio(Base):
    __tablename__ = "portfolios"
    __table_args__ = (
        Index("ix_portfolios_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    base_currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    source_type: Mapped[PortfolioSourceType] = mapped_column(
        SAEnum(PortfolioSourceType, name="portfolio_source_type", create_constraint=True, native_enum=False, length=10),
        default=PortfolioSourceType.manual,
        server_default="manual",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    positions: Mapped[list["PortfolioPosition"]] = relationship(
        "PortfolioPosition", back_populates="portfolio", cascade="all, delete-orphan", lazy="selectin",
    )
    imports: Mapped[list["PortfolioImport"]] = relationship(
        "PortfolioImport", back_populates="portfolio", cascade="all, delete-orphan", lazy="selectin",
    )


# ---------------------------------------------------------------------------
# PortfolioPosition model
# ---------------------------------------------------------------------------

class PortfolioPosition(Base):
    __tablename__ = "portfolio_positions"
    __table_args__ = (
        UniqueConstraint("portfolio_id", "symbol", name="uq_portfolio_position_symbol"),
        Index("ix_portfolio_positions_portfolio_id", "portfolio_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)

    symbol: Mapped[str] = mapped_column(String(15), nullable=False)
    qty: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    avg_price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    total_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    bes: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="positions")


# ---------------------------------------------------------------------------
# PortfolioImport model
# ---------------------------------------------------------------------------

class PortfolioImport(Base):
    __tablename__ = "portfolio_imports"
    __table_args__ = (
        Index("ix_portfolio_imports_portfolio_id", "portfolio_id"),
        Index("ix_portfolio_imports_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    file_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)

    status: Mapped[ImportStatus] = mapped_column(
        SAEnum(ImportStatus, name="import_status", create_constraint=True, native_enum=False, length=10),
        default=ImportStatus.received,
        server_default="received",
        nullable=False,
    )
    rows_total: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    rows_parsed: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    rows_failed: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="imports")


# ---------------------------------------------------------------------------
# WatchlistItem model
# ---------------------------------------------------------------------------

class WatchlistItem(Base):
    __tablename__ = "watchlist_items"
    __table_args__ = (
        UniqueConstraint("user_id", "symbol", name="uq_watchlist_user_symbol"),
        Index("ix_watchlist_items_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    symbol: Mapped[str] = mapped_column(String(15), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# ---------------------------------------------------------------------------
# SecurityEvent model
# ---------------------------------------------------------------------------

class SecurityEventType(str, enum.Enum):
    pin_set = "pin_set"
    pin_changed = "pin_changed"
    pin_verify_success = "pin_verify_success"
    pin_verify_failed = "pin_verify_failed"
    pin_locked = "pin_locked"
    pin_lockout_expired = "pin_lockout_expired"
    pin_rate_limited = "pin_rate_limited"


class SecurityEvent(Base):
    __tablename__ = "security_events"
    __table_args__ = (
        Index("ix_security_events_user_id", "user_id"),
        Index("ix_security_events_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    event_type: Mapped[SecurityEventType] = mapped_column(
        SAEnum(SecurityEventType, name="security_event_type", create_constraint=True, native_enum=False, length=30),
        nullable=False,
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    detail: Mapped[str | None] = mapped_column(String(512), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="security_events")


# ---------------------------------------------------------------------------
# Admin Role enum
# ---------------------------------------------------------------------------

class AdminRole(str, enum.Enum):
    super_admin = "super_admin"
    admin = "admin"


# ---------------------------------------------------------------------------
# Admin model
# ---------------------------------------------------------------------------

class Admin(Base):
    __tablename__ = "admins"
    __table_args__ = (
        Index("ix_admins_email", "email", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    firebase_uid: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    role: Mapped[AdminRole] = mapped_column(
        SAEnum(AdminRole, name="admin_role", create_constraint=True, native_enum=False, length=20),
        default=AdminRole.admin,
        server_default="admin",
        nullable=False,
    )
    is_active: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)

    # Who invited this admin (null for the first super_admin)
    invited_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("admins.id", ondelete="SET NULL"), nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

