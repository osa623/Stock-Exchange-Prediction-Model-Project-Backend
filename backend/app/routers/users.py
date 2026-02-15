"""
User router – all endpoints require authentication.

firebase_uid is ALWAYS derived from the verified token via ``get_current_uid``.
It is never accepted from the request body.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from db.session import get_db
from app.middleware.firebase_auth import get_current_uid
from app.middleware.rate_limit import pin_rate_limiter
from app.schemas.users import (
    ProfileUpdateRequest,
    OnboardingUpdateRequest,
    PinSetRequest,
    PinVerifyRequest,
    RegisterRequest,
    UserMeResponse,
    OnboardingResponse,
    SecurityEventResponse,
    SubscriptionStatusEnum,
)
from modules.users.service import (
    get_or_create_user,
    update_profile,
    update_onboarding,
    set_or_change_pin,
    check_pin,
    get_security_events,
)
from modules.users.repository import get_user_by_firebase_uid
from common.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_client_ip(request: Request) -> str:
    """Extract client IP from request, considering proxy headers."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    if request.client:
        return request.client.host
    return "unknown"


async def _enforce_pin_rate_limit(request: Request, db: Session, uid: str) -> None:
    """
    Enforce per-IP rate limiting specifically for PIN endpoints.
    Records a security event if rate-limited.
    """
    client_ip = _get_client_ip(request)
    is_allowed, _ = await pin_rate_limiter.is_allowed(client_ip)
    if not is_allowed:
        # Record the rate-limit event if we can find the user
        from modules.users.repository import create_security_event, get_user_by_firebase_uid as _get_user
        from db.models import SecurityEventType
        user = _get_user(db, uid)
        if user is not None:
            create_security_event(
                db, user, SecurityEventType.pin_rate_limited,
                ip_address=client_ip,
                detail="PIN endpoint rate limit exceeded.",
            )
        logger.warning(
            "PIN rate limit exceeded",
            extra={"client_ip": client_ip, "firebase_uid": uid, "event": "pin_rate_limited"},
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many PIN requests. Please wait before trying again.",
            headers={"Retry-After": "300"},
        )

def _build_me_response(user) -> UserMeResponse:
    """Map a User ORM instance to the safe response schema."""
    sub_status = SubscriptionStatusEnum.free
    if user.subscription is not None:
        sub_status = SubscriptionStatusEnum(user.subscription.status.value)

    onboarding = None
    if user.onboarding is not None:
        onboarding = OnboardingResponse.model_validate(user.onboarding)

    return UserMeResponse(
        firebase_uid=user.firebase_uid,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        email=user.email,
        phone_number=user.phone_number,
        avatar_url=user.avatar_url,
        pin_is_set=user.pin_hash is not None,
        subscription_status=sub_status,
        onboarding=onboarding,
        created_at=user.created_at,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/me", response_model=UserMeResponse)
def get_me(
    db: Session = Depends(get_db),
    uid: str = Depends(get_current_uid),
):
    """Return current user profile. 404 if user has not registered yet."""
    user = get_user_by_firebase_uid(db, uid)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not registered. POST /users/me/register first.",
        )
    return _build_me_response(user)


@router.post("/me/register", response_model=UserMeResponse, status_code=status.HTTP_201_CREATED)
def register_me(
    body: RegisterRequest,
    db: Session = Depends(get_db),
    uid: str = Depends(get_current_uid),
):
    """First-time registration – creates User + Subscription + Onboarding rows."""
    user = get_or_create_user(
        db,
        uid,
        first_name=body.first_name,
        last_name=body.last_name,
        username=body.username,
        email=body.email,
        phone_number=body.phone_number,
    )
    return _build_me_response(user)


@router.patch("/me", response_model=UserMeResponse)
def patch_me(
    body: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    uid: str = Depends(get_current_uid),
):
    """Partial update of profile fields."""
    user = update_profile(
        db,
        uid,
        first_name=body.first_name,
        last_name=body.last_name,
        username=body.username,
        phone_number=body.phone_number,
        avatar_url=body.avatar_url,
    )
    return _build_me_response(user)


@router.put("/me/onboarding", response_model=UserMeResponse)
def put_onboarding(
    body: OnboardingUpdateRequest,
    db: Session = Depends(get_db),
    uid: str = Depends(get_current_uid),
):
    """Set or replace onboarding data."""
    user = update_onboarding(
        db,
        uid,
        experience_level=body.experience_level.value,
        primary_goal=body.primary_goal.value,
        investor_type=body.investor_type.value if body.investor_type else None,
        portfolio_size=body.portfolio_size.value if body.portfolio_size else None,
    )
    return _build_me_response(user)


@router.put("/me/pin", status_code=status.HTTP_204_NO_CONTENT)
async def put_pin(
    request: Request,
    body: PinSetRequest,
    db: Session = Depends(get_db),
    uid: str = Depends(get_current_uid),
):
    """Set or change the user's 6-digit PIN (rate-limited per IP)."""
    await _enforce_pin_rate_limit(request, db, uid)
    client_ip = _get_client_ip(request)
    set_or_change_pin(db, uid, body.pin, ip_address=client_ip)
    return None


@router.post("/me/pin/verify")
async def verify_pin_endpoint(
    request: Request,
    body: PinVerifyRequest,
    db: Session = Depends(get_db),
    uid: str = Depends(get_current_uid),
):
    """
    Verify the user's PIN (rate-limited per IP).
    Returns 200 on success, 401 on mismatch, 429 when locked or rate-limited.
    """
    await _enforce_pin_rate_limit(request, db, uid)
    client_ip = _get_client_ip(request)
    check_pin(db, uid, body.pin, ip_address=client_ip)
    return {"verified": True}


@router.get("/me/security-events", response_model=list[SecurityEventResponse])
def get_my_security_events(
    db: Session = Depends(get_db),
    uid: str = Depends(get_current_uid),
):
    """Return the most recent security events for the authenticated user."""
    return get_security_events(db, uid)
