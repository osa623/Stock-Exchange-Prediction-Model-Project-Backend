"""
Admin router – endpoints for the admin dashboard.
All endpoints require admin authentication via require_admin dependency.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc

from db.session import get_db
from db.models import (
    User, Subscription, UserOnboarding, Portfolio, PortfolioPosition,
    WatchlistItem, SecurityEvent, SubscriptionStatus,
)
from app.middleware.admin_auth import require_admin
from common.logging import get_logger

router = APIRouter(dependencies=[Depends(require_admin)])
logger = get_logger(__name__)


# ── Dashboard Stats ────────────────────────────────────────────────────────

@router.get("/stats")
def admin_stats(db: Session = Depends(get_db)):
    """Return high-level platform statistics for the admin dashboard."""
    total_users = db.query(func.count(User.id)).scalar() or 0
    premium_users = (
        db.query(func.count(Subscription.id))
        .filter(Subscription.status == SubscriptionStatus.premium)
        .scalar() or 0
    )
    total_portfolios = db.query(func.count(Portfolio.id)).scalar() or 0
    total_positions = db.query(func.count(PortfolioPosition.id)).scalar() or 0
    total_watchlist = db.query(func.count(WatchlistItem.id)).scalar() or 0
    total_security_events = db.query(func.count(SecurityEvent.id)).scalar() or 0

    # Recent registrations (last 30 days)
    from datetime import datetime, timedelta, timezone
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    recent_signups = (
        db.query(func.count(User.id))
        .filter(User.created_at >= thirty_days_ago)
        .scalar() or 0
    )

    return {
        "total_users": total_users,
        "premium_users": premium_users,
        "free_users": total_users - premium_users,
        "total_portfolios": total_portfolios,
        "total_positions": total_positions,
        "total_watchlist_items": total_watchlist,
        "total_security_events": total_security_events,
        "recent_signups_30d": recent_signups,
    }


# ── User List ──────────────────────────────────────────────────────────────

@router.get("/users")
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: str = Query("", max_length=100),
    db: Session = Depends(get_db),
):
    """List all users with pagination and optional search."""
    query = db.query(User).options(
        joinedload(User.subscription),
        joinedload(User.onboarding),
    )

    if search:
        like_term = f"%{search}%"
        query = query.filter(
            (User.username.ilike(like_term))
            | (User.first_name.ilike(like_term))
            | (User.last_name.ilike(like_term))
            | (User.email.ilike(like_term))
            | (User.firebase_uid.ilike(like_term))
        )

    total = query.count()
    users = query.order_by(desc(User.created_at)).offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "users": [_user_summary(u) for u in users],
    }


# ── Single User Detail ────────────────────────────────────────────────────

@router.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get full detail for a single user."""
    user = (
        db.query(User)
        .options(joinedload(User.subscription), joinedload(User.onboarding))
        .filter(User.id == user_id)
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return _user_detail(user)


# ── Delete User ────────────────────────────────────────────────────────────

@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user and all associated data (cascade)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Delete associated portfolios (cascade will handle positions/imports)
    db.query(Portfolio).filter(Portfolio.user_id == user_id).delete()
    db.query(WatchlistItem).filter(WatchlistItem.user_id == user_id).delete()

    db.delete(user)
    db.commit()

    logger.info(f"Admin deleted user {user_id}", extra={"user_id": user_id, "event": "admin_user_deleted"})
    return {"status": "ok", "deleted_user_id": user_id}


# ── User Portfolios ───────────────────────────────────────────────────────

@router.get("/users/{user_id}/portfolios")
def get_user_portfolios(user_id: int, db: Session = Depends(get_db)):
    """Get all portfolios (with positions) for a user."""
    _ensure_user_exists(user_id, db)
    portfolios = (
        db.query(Portfolio)
        .options(joinedload(Portfolio.positions))
        .filter(Portfolio.user_id == user_id)
        .order_by(desc(Portfolio.created_at))
        .all()
    )
    return [_portfolio_response(p) for p in portfolios]


# ── User Watchlist ─────────────────────────────────────────────────────────

@router.get("/users/{user_id}/watchlist")
def get_user_watchlist(user_id: int, db: Session = Depends(get_db)):
    """Get all watchlist items for a user."""
    _ensure_user_exists(user_id, db)
    items = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.user_id == user_id)
        .order_by(desc(WatchlistItem.created_at))
        .all()
    )
    return [
        {
            "id": item.id,
            "symbol": item.symbol,
            "display_name": item.display_name,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        for item in items
    ]


# ── User Security Events ──────────────────────────────────────────────────

@router.get("/users/{user_id}/security-events")
def get_user_security_events(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Get security events for a user."""
    _ensure_user_exists(user_id, db)
    query = (
        db.query(SecurityEvent)
        .filter(SecurityEvent.user_id == user_id)
        .order_by(desc(SecurityEvent.created_at))
    )
    total = query.count()
    events = query.offset(skip).limit(limit).all()
    return {
        "total": total,
        "events": [
            {
                "id": e.id,
                "event_type": e.event_type.value if e.event_type else None,
                "ip_address": e.ip_address,
                "detail": e.detail,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ],
    }


# ── Delete Portfolio (admin) ───────────────────────────────────────────────

@router.delete("/portfolios/{portfolio_id}")
def delete_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    """Admin delete any portfolio."""
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    db.delete(portfolio)
    db.commit()
    return {"status": "ok", "deleted_portfolio_id": portfolio_id}


# ── Helpers ────────────────────────────────────────────────────────────────

def _ensure_user_exists(user_id: int, db: Session):
    exists = db.query(User.id).filter(User.id == user_id).first()
    if not exists:
        raise HTTPException(status_code=404, detail="User not found")


def _user_summary(user: User) -> dict:
    sub_status = "free"
    if user.subscription and user.subscription.status:
        sub_status = user.subscription.status.value

    return {
        "id": user.id,
        "firebase_uid": user.firebase_uid,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "email": user.email,
        "phone_number": user.phone_number,
        "avatar_url": user.avatar_url,
        "pin_is_set": user.pin_hash is not None,
        "subscription_status": sub_status,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


def _user_detail(user: User) -> dict:
    data = _user_summary(user)
    data["onboarding"] = None
    if user.onboarding:
        data["onboarding"] = {
            "experience_level": user.onboarding.experience_level.value if user.onboarding.experience_level else None,
            "primary_goal": user.onboarding.primary_goal.value if user.onboarding.primary_goal else None,
            "investor_type": user.onboarding.investor_type.value if user.onboarding.investor_type else None,
            "portfolio_size": user.onboarding.portfolio_size.value if user.onboarding.portfolio_size else None,
        }
    return data


def _portfolio_response(portfolio: Portfolio) -> dict:
    return {
        "id": portfolio.id,
        "name": portfolio.name,
        "base_currency": portfolio.base_currency,
        "source_type": portfolio.source_type.value if portfolio.source_type else None,
        "created_at": portfolio.created_at.isoformat() if portfolio.created_at else None,
        "updated_at": portfolio.updated_at.isoformat() if portfolio.updated_at else None,
        "positions": [
            {
                "id": pos.id,
                "symbol": pos.symbol,
                "qty": str(pos.qty),
                "avg_price": str(pos.avg_price),
                "total_cost": str(pos.total_cost) if pos.total_cost else None,
                "bes": str(pos.bes) if pos.bes else None,
                "currency": pos.currency,
            }
            for pos in (portfolio.positions or [])
        ],
    }
