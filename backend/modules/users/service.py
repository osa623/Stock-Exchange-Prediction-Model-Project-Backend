"""
User service – business logic for profile, onboarding, and PIN management.

All functions receive a SQLAlchemy Session from the caller (the router layer)
so there are no leaked sessions.  firebase_uid is always the trusted value
produced by the auth middleware.
"""

import re
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from common.security import hash_pin, verify_pin
from common.logging import get_logger
from db.models import (
    User,
    ExperienceLevel,
    PrimaryGoal,
    InvestorType,
    PortfolioSize,
    SecurityEventType,
)
from modules.users.repository import (
    get_user_by_firebase_uid,
    get_user_by_username,
    create_user_with_defaults,
    update_user_profile as repo_update_profile,
    upsert_onboarding as repo_upsert_onboarding,
    set_pin_hash as repo_set_pin_hash,
    increment_pin_failed_attempts,
    lock_pin,
    reset_pin_lockout,
    increment_lockout_count,
    reset_lockout_count,
    create_security_event,
    list_security_events as repo_list_security_events,
)

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_PIN_ATTEMPTS = 5

# Exponential backoff lockout durations (minutes) indexed by lockout_count
# Lockout 1: 1 min, 2: 5 min, 3: 15 min, 4: 60 min, 5+: 24 hours
_LOCKOUT_MINUTES = [1, 5, 15, 60, 1440]

_USERNAME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{2,39}$")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _validate_username(username: str) -> str:
    """Return sanitised username or raise 422."""
    username = username.strip()
    if not _USERNAME_RE.match(username):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Username must start with a letter, contain only letters, "
                "digits, or underscores, and be 3-40 characters long."
            ),
        )
    return username


def _check_username_available(db: Session, username: str, current_user: User | None = None) -> None:
    """Raise 409 if *username* is already taken by another user."""
    existing = get_user_by_username(db, username)
    if existing is not None and (current_user is None or existing.id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already taken.",
        )


# ---------------------------------------------------------------------------
# Service methods
# ---------------------------------------------------------------------------

def get_or_create_user(
    db: Session,
    firebase_uid: str,
    *,
    email: str | None = None,
    phone_number: str | None = None,
    first_name: str = "",
    last_name: str = "",
    username: str = "",
) -> User:
    """
    Return the existing user linked to *firebase_uid*, or create a new one
    with sensible defaults.  During initial creation the caller MUST supply
    first_name, last_name, and username; for a simple GET /me the existing
    user is returned directly.
    """
    user = get_user_by_firebase_uid(db, firebase_uid)
    if user is not None:
        return user

    # First-time registration – validate mandatory fields
    if not first_name or not last_name or not username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="first_name, last_name, and username are required for initial registration.",
        )

    username = _validate_username(username)
    _check_username_available(db, username)

    user = create_user_with_defaults(
        db,
        firebase_uid=firebase_uid,
        first_name=first_name,
        last_name=last_name,
        username=username,
        email=email,
        phone_number=phone_number,
    )
    logger.info("New user created", extra={"firebase_uid": firebase_uid, "event": "user_created"})
    return user


def update_profile(
    db: Session,
    firebase_uid: str,
    *,
    first_name: str | None = None,
    last_name: str | None = None,
    username: str | None = None,
    phone_number: str | None = None,
    avatar_url: str | None = None,
) -> User:
    """Partial update of user profile.  Only non-None fields are changed."""
    user = get_user_by_firebase_uid(db, firebase_uid)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if username is not None:
        username = _validate_username(username)
        _check_username_available(db, username, current_user=user)

    return repo_update_profile(
        db,
        user,
        first_name=first_name,
        last_name=last_name,
        username=username,
        phone_number=phone_number,
        avatar_url=avatar_url,
    )


def update_onboarding(
    db: Session,
    firebase_uid: str,
    *,
    experience_level: ExperienceLevel,
    primary_goal: PrimaryGoal,
    investor_type: InvestorType | None = None,
    portfolio_size: PortfolioSize | None = None,
) -> User:
    """Set or replace onboarding data."""
    user = get_user_by_firebase_uid(db, firebase_uid)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    repo_upsert_onboarding(
        db,
        user,
        experience_level=experience_level,
        primary_goal=primary_goal,
        investor_type=investor_type,
        portfolio_size=portfolio_size,
    )
    db.refresh(user)
    return user


def _lockout_minutes(lockout_count: int) -> int:
    """Return escalating lockout duration based on how many times user was locked."""
    idx = min(lockout_count, len(_LOCKOUT_MINUTES)) - 1
    return _LOCKOUT_MINUTES[max(idx, 0)]


def set_or_change_pin(
    db: Session,
    firebase_uid: str,
    pin: str,
    ip_address: str | None = None,
) -> None:
    """Hash and store a new 6-digit PIN. Resets lockout state."""
    user = get_user_by_firebase_uid(db, firebase_uid)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    event_type = (
        SecurityEventType.pin_changed if user.pin_hash is not None
        else SecurityEventType.pin_set
    )

    hashed = hash_pin(pin)  # raises ValueError for invalid format
    repo_set_pin_hash(db, user, hashed)
    # Reset escalation on new PIN
    reset_lockout_count(db, user)

    create_security_event(db, user, event_type, ip_address=ip_address, detail="PIN set/changed successfully.")
    logger.info("PIN set/changed", extra={"firebase_uid": firebase_uid, "event": "pin_changed"})


def check_pin(
    db: Session,
    firebase_uid: str,
    pin: str,
    ip_address: str | None = None,
) -> bool:
    """
    Verify *pin* against the stored hash with brute-force protection.

    Security features:
    - Exponential backoff lockout (1 min → 5 min → 15 min → 1 hr → 24 hr)
    - Automatic counter reset when lockout period expires
    - Security event logging for audit trail

    Returns True on success.
    Raises HTTPException on lockout, missing PIN, or incorrect PIN.
    """
    user = get_user_by_firebase_uid(db, firebase_uid)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if user.pin_hash is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PIN has not been set.",
        )

    now = datetime.now(timezone.utc)

    # ── Lockout check ─────────────────────────────────────────────────────
    if user.pin_locked_until is not None:
        if now < user.pin_locked_until:
            remaining = int((user.pin_locked_until - now).total_seconds())
            create_security_event(
                db, user, SecurityEventType.pin_verify_failed,
                ip_address=ip_address,
                detail=f"Attempt while locked. {remaining}s remaining.",
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"PIN is locked. Try again in {remaining} seconds.",
            )
        else:
            # Lockout has expired – reset failed attempts so user gets
            # a fresh set of MAX_PIN_ATTEMPTS, but keep lockout_count
            # so the NEXT lockout escalates further.
            reset_pin_lockout(db, user)
            create_security_event(
                db, user, SecurityEventType.pin_lockout_expired,
                ip_address=ip_address,
                detail="Lockout expired. Failed attempts reset.",
            )
            logger.info(
                "PIN lockout expired, attempts reset",
                extra={"firebase_uid": firebase_uid, "event": "pin_lockout_expired"},
            )

    # ── Verify ────────────────────────────────────────────────────────────
    if verify_pin(pin, user.pin_hash):
        # Successful – clear ALL lockout state including escalation counter
        if user.pin_failed_attempts > 0 or user.pin_lockout_count > 0:
            reset_lockout_count(db, user)
        create_security_event(
            db, user, SecurityEventType.pin_verify_success,
            ip_address=ip_address,
            detail="PIN verified successfully.",
        )
        return True

    # ── Failed attempt ────────────────────────────────────────────────────
    attempts = increment_pin_failed_attempts(db, user)

    if attempts >= MAX_PIN_ATTEMPTS:
        lockout_num = increment_lockout_count(db, user)
        lockout_mins = _lockout_minutes(lockout_num)
        lock_until = now + timedelta(minutes=lockout_mins)
        lock_pin(db, user, lock_until)

        create_security_event(
            db, user, SecurityEventType.pin_locked,
            ip_address=ip_address,
            detail=f"Locked for {lockout_mins} min (lockout #{lockout_num}).",
        )
        logger.warning(
            "PIN locked – exponential backoff",
            extra={
                "firebase_uid": firebase_uid,
                "lockout_count": lockout_num,
                "lockout_minutes": lockout_mins,
                "event": "pin_locked",
            },
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed attempts. PIN is locked for {lockout_mins} minute(s).",
        )

    remaining_attempts = MAX_PIN_ATTEMPTS - attempts
    create_security_event(
        db, user, SecurityEventType.pin_verify_failed,
        ip_address=ip_address,
        detail=f"Incorrect PIN. {remaining_attempts} attempt(s) remaining.",
    )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"Incorrect PIN. {remaining_attempts} attempt(s) remaining.",
    )


def get_security_events(
    db: Session,
    firebase_uid: str,
    limit: int = 50,
) -> list:
    """Return the most recent security events for the authenticated user."""
    user = get_user_by_firebase_uid(db, firebase_uid)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return repo_list_security_events(db, user, limit=limit)
