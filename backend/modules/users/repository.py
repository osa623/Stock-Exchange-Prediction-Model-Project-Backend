"""
User repository – all direct database operations for users, onboarding,
subscriptions, and PIN security fields.
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import (
    User,
    UserOnboarding,
    Subscription,
    SubscriptionStatus,
    ExperienceLevel,
    PrimaryGoal,
    InvestorType,
    PortfolioSize,
)


# ---------------------------------------------------------------------------
# Lookups
# ---------------------------------------------------------------------------

def get_user_by_firebase_uid(db: Session, firebase_uid: str) -> User | None:
    return db.execute(
        select(User).where(User.firebase_uid == firebase_uid)
    ).scalar_one_or_none()


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.execute(
        select(User).where(User.username == username)
    ).scalar_one_or_none()


# ---------------------------------------------------------------------------
# Creation
# ---------------------------------------------------------------------------

def create_user_with_defaults(
    db: Session,
    *,
    firebase_uid: str,
    first_name: str,
    last_name: str,
    username: str,
    email: str | None = None,
    phone_number: str | None = None,
    avatar_url: str | None = None,
    experience_level: ExperienceLevel = ExperienceLevel.beginner,
    primary_goal: PrimaryGoal = PrimaryGoal.long_term_investing,
    investor_type: InvestorType | None = None,
    portfolio_size: PortfolioSize | None = None,
) -> User:
    """Create a User row, a default free Subscription, and an Onboarding row."""
    user = User(
        firebase_uid=firebase_uid,
        first_name=first_name,
        last_name=last_name,
        username=username,
        email=email,
        phone_number=phone_number,
        avatar_url=avatar_url,
    )
    db.add(user)
    db.flush()  # populate user.id

    sub = Subscription(
        user_id=user.id,
        status=SubscriptionStatus.free,
        plan_id=None,
    )
    db.add(sub)

    onboarding = UserOnboarding(
        user_id=user.id,
        experience_level=experience_level,
        primary_goal=primary_goal,
        investor_type=investor_type,
        portfolio_size=portfolio_size,
    )
    db.add(onboarding)

    db.commit()
    db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Profile updates
# ---------------------------------------------------------------------------

def update_user_profile(
    db: Session,
    user: User,
    *,
    first_name: str | None = None,
    last_name: str | None = None,
    username: str | None = None,
    email: str | None = None,
    phone_number: str | None = None,
    avatar_url: str | None = None,
) -> User:
    """Update only the supplied (non-None) profile fields."""
    if first_name is not None:
        user.first_name = first_name
    if last_name is not None:
        user.last_name = last_name
    if username is not None:
        user.username = username
    if email is not None:
        user.email = email
    if phone_number is not None:
        user.phone_number = phone_number
    if avatar_url is not None:
        user.avatar_url = avatar_url

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Onboarding
# ---------------------------------------------------------------------------

def upsert_onboarding(
    db: Session,
    user: User,
    *,
    experience_level: ExperienceLevel,
    primary_goal: PrimaryGoal,
    investor_type: InvestorType | None = None,
    portfolio_size: PortfolioSize | None = None,
) -> UserOnboarding:
    """Create or fully replace the user's onboarding data."""
    onboarding = user.onboarding
    if onboarding is None:
        onboarding = UserOnboarding(user_id=user.id)
        db.add(onboarding)

    onboarding.experience_level = experience_level
    onboarding.primary_goal = primary_goal
    onboarding.investor_type = investor_type
    onboarding.portfolio_size = portfolio_size

    db.commit()
    db.refresh(onboarding)
    return onboarding


# ---------------------------------------------------------------------------
# PIN management
# ---------------------------------------------------------------------------

def set_pin_hash(db: Session, user: User, pin_hash: str) -> None:
    """Store a new PIN hash and reset any lockout state."""
    user.pin_hash = pin_hash
    user.pin_set_at = datetime.now(timezone.utc)
    user.pin_failed_attempts = 0
    user.pin_locked_until = None
    db.add(user)
    db.commit()


def increment_pin_failed_attempts(db: Session, user: User) -> int:
    """Increment the failed-attempt counter and return the new value."""
    user.pin_failed_attempts = (user.pin_failed_attempts or 0) + 1
    db.add(user)
    db.commit()
    db.refresh(user)
    return user.pin_failed_attempts


def lock_pin(db: Session, user: User, until: datetime) -> None:
    """Lock PIN verification until the given timestamp."""
    user.pin_locked_until = until
    db.add(user)
    db.commit()


def reset_pin_lockout(db: Session, user: User) -> None:
    """Clear failed-attempt counter and lockout timestamp."""
    user.pin_failed_attempts = 0
    user.pin_locked_until = None
    db.add(user)
    db.commit()
