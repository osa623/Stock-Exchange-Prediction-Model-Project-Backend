"""
Report Router

Provides tiered access to analysis reports stored in MongoDB:
  GET /reports/public           — unauthenticated, summary only, strict limits
  GET /reports/public/{id}      — unauthenticated, single report summary
  GET /reports/tree             — folder structure (all tiers)
  GET /reports/list             — authenticated, detail fields
  GET /reports/{id}             — authenticated, report detail
  GET /reports/premium/list     — premium, full access
  GET /reports/premium/{id}     — premium, full detail + raw_data
  GET /reports/premium/{id}/export — premium, JSON export
  GET /reports/cache/stats      — admin-only, cache diagnostics
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Request
from sqlalchemy.orm import Session
import time

from db.session import get_db
from app.middleware.firebase_auth import get_current_uid, get_optional_uid
from app.middleware.rate_limit import RateLimiter
from modules.users.service import get_or_create_user
from modules.entitlements.service import is_premium
from modules.reports import service as report_svc
from app.schemas.reports import ReportListQuery
from common.cache import report_list_cache, report_detail_cache, folder_tree_cache
from common.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

# ── Public rate limiter: 20 req/min per IP (stricter than global) ────────
public_report_limiter = RateLimiter(max_requests=20, window_seconds=60)

# ── Abuse-tracking counters (in-memory, rotated hourly) ──────────────────
_abuse_window: dict[str, list[float]] = {}
ABUSE_THRESHOLD = 200       # requests per hour per IP
ABUSE_WINDOW_SECS = 3600


def _track_and_check_abuse(client_ip: str) -> bool:
    """
    Record a request and return True if the IP exceeds the hourly threshold.
    This is a lightweight in-memory monitor — not a hard block.
    """
    now = time.time()
    cutoff = now - ABUSE_WINDOW_SECS
    hits = _abuse_window.setdefault(client_ip, [])
    hits[:] = [t for t in hits if t > cutoff]
    hits.append(now)
    if len(hits) > ABUSE_THRESHOLD:
        logger.warning(
            f"Abuse detected: IP {client_ip} exceeded {ABUSE_THRESHOLD} report requests/hour",
            extra={"ip": client_ip, "count": len(hits), "event": "abuse_alert"},
        )
        return True
    return False


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"


def _validated_query(
    category: str | None,
    subcategory: str | None,
    symbol: str | None,
    search: str | None,
    page: int,
    page_size: int,
) -> ReportListQuery:
    """Run Pydantic validation on query params (catches injection)."""
    return ReportListQuery(
        category=category,
        subcategory=subcategory,
        symbol=symbol,
        search=search,
        page=page,
        page_size=page_size,
    )


# ═════════════════════════════════════════════════════════════════════════
# PUBLIC ENDPOINTS (no auth)
# ═════════════════════════════════════════════════════════════════════════


@router.get("/public")
async def list_reports_public(
    request: Request,
    category: str | None = Query(None, max_length=100),
    subcategory: str | None = Query(None, max_length=100),
    symbol: str | None = Query(None, max_length=10),
    search: str | None = Query(None, max_length=100),
    page: int = Query(1, ge=1, le=50),
    page_size: int = Query(10, ge=1, le=10),
):
    """
    Public report listing — no authentication required.

    - Summary fields only (title, category, symbol, summary, tags)
    - Max 10 items per page, max 50 total reachable
    - Stricter rate limit (20 req/min per IP)
    """
    client_ip = _get_client_ip(request)

    # Rate-limit check
    allowed, remaining = await public_report_limiter.is_allowed(client_ip)
    if not allowed:
        raise HTTPException(status_code=429, detail="Too many requests. Try again shortly.")

    # Abuse monitoring
    _track_and_check_abuse(client_ip)

    q = _validated_query(category, subcategory, symbol, search, page, page_size)
    return await report_svc.list_reports_public(
        category=q.category,
        subcategory=q.subcategory,
        symbol=q.symbol,
        search=q.search,
        page=q.page,
        page_size=q.page_size,
    )


@router.get("/public/{report_id}")
async def get_report_public(
    request: Request,
    report_id: str = Path(..., min_length=24, max_length=24),
):
    """Public single report — summary fields only."""
    client_ip = _get_client_ip(request)
    allowed, _ = await public_report_limiter.is_allowed(client_ip)
    if not allowed:
        raise HTTPException(status_code=429, detail="Too many requests.")

    _track_and_check_abuse(client_ip)

    doc = await report_svc.get_report_detail(report_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Report not found")
    if doc.get("access_level") not in ("public",):
        raise HTTPException(status_code=403, detail="This report requires authentication")

    # Strip detail fields for public view
    for key in ("data", "raw_data", "methodology", "metadata"):
        doc.pop(key, None)
    return doc


# ═════════════════════════════════════════════════════════════════════════
# FOLDER TREE (available to all, optionally auth)
# ═════════════════════════════════════════════════════════════════════════


@router.get("/tree")
async def get_folder_tree(
    request: Request,
    uid: str | None = Depends(get_optional_uid),
):
    """
    Returns the hierarchical folder structure of all reports
    mirroring the analysis module layout.
    """
    client_ip = _get_client_ip(request)
    if uid is None:
        allowed, _ = await public_report_limiter.is_allowed(client_ip)
        if not allowed:
            raise HTTPException(status_code=429, detail="Too many requests.")

    return await report_svc.get_folder_tree()


# ═════════════════════════════════════════════════════════════════════════
# REGISTERED-USER ENDPOINTS (auth required)
# ═════════════════════════════════════════════════════════════════════════


@router.get("/list")
async def list_reports_registered(
    category: str | None = Query(None, max_length=100),
    subcategory: str | None = Query(None, max_length=100),
    symbol: str | None = Query(None, max_length=10),
    search: str | None = Query(None, max_length=100),
    page: int = Query(1, ge=1, le=500),
    page_size: int = Query(20, ge=1, le=50),
    uid: str = Depends(get_current_uid),
):
    """
    Registered user report listing — more detail, higher limits.
    """
    logger.info("Report list requested", extra={"uid": uid, "event": "report_list"})
    q = _validated_query(category, subcategory, symbol, search, page, page_size)
    return await report_svc.list_reports_registered(
        category=q.category,
        subcategory=q.subcategory,
        symbol=q.symbol,
        search=q.search,
        page=q.page,
        page_size=q.page_size,
    )


@router.get("/detail/{report_id}")
async def get_report_detail(
    report_id: str = Path(..., min_length=24, max_length=24),
    uid: str = Depends(get_current_uid),
):
    """Single report detail for registered users."""
    doc = await report_svc.get_report_detail(report_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Report not found")
    if doc.get("access_level") == "premium":
        raise HTTPException(
            status_code=403,
            detail="Premium report — upgrade to access full content",
        )
    return doc


# ═════════════════════════════════════════════════════════════════════════
# PREMIUM ENDPOINTS (auth + premium subscription)
# ═════════════════════════════════════════════════════════════════════════


def _require_premium(uid: str, db: Session):
    """Reusable dependency: verify premium subscription."""
    user = get_or_create_user(db, uid)
    if not is_premium(user):
        raise HTTPException(
            status_code=403,
            detail="Premium subscription required for full report access",
        )
    return user


@router.get("/premium/list")
async def list_reports_premium(
    category: str | None = Query(None, max_length=100),
    subcategory: str | None = Query(None, max_length=100),
    symbol: str | None = Query(None, max_length=10),
    search: str | None = Query(None, max_length=100),
    page: int = Query(1, ge=1, le=1000),
    page_size: int = Query(20, ge=1, le=100),
    uid: str = Depends(get_current_uid),
    db: Session = Depends(get_db),
):
    """Premium report listing — all access levels, highest limits."""
    _require_premium(uid, db)
    q = _validated_query(category, subcategory, symbol, search, page, page_size)
    return await report_svc.list_reports_premium(
        category=q.category,
        subcategory=q.subcategory,
        symbol=q.symbol,
        search=q.search,
        page=q.page,
        page_size=q.page_size,
    )


@router.get("/premium/{report_id}")
async def get_report_premium(
    report_id: str = Path(..., min_length=24, max_length=24),
    uid: str = Depends(get_current_uid),
    db: Session = Depends(get_db),
):
    """Full report detail for premium users (includes raw_data, methodology)."""
    _require_premium(uid, db)
    doc = await report_svc.get_report_full(report_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Report not found")
    return doc


@router.get("/premium/{report_id}/export")
async def export_report(
    report_id: str = Path(..., min_length=24, max_length=24),
    uid: str = Depends(get_current_uid),
    db: Session = Depends(get_db),
):
    """
    Export full report as JSON (premium only).
    Could be extended to CSV/Excel in a future iteration.
    """
    _require_premium(uid, db)
    doc = await report_svc.export_report(report_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Report not found")
    return {
        "export_format": "json",
        "report": doc,
    }


# ═════════════════════════════════════════════════════════════════════════
# ADMIN — cache stats
# ═════════════════════════════════════════════════════════════════════════


@router.get("/cache/stats")
async def cache_stats(
    uid: str = Depends(get_current_uid),
    db: Session = Depends(get_db),
):
    """Admin-only: view cache hit/miss statistics."""
    from app.middleware.admin_auth import require_admin
    require_admin(uid, db)
    return {
        "report_list": report_list_cache.stats,
        "report_detail": report_detail_cache.stats,
        "folder_tree": folder_tree_cache.stats,
    }


@router.post("/cache/clear")
async def cache_clear(
    uid: str = Depends(get_current_uid),
    db: Session = Depends(get_db),
):
    """Admin-only: clear all report caches to force fresh data."""
    from app.middleware.admin_auth import require_admin
    require_admin(uid, db)
    await report_list_cache.clear()
    await report_detail_cache.clear()
    await folder_tree_cache.clear()
    logger.info("Report caches cleared by admin", extra={"uid": uid, "event": "cache_clear"})
    return {"status": "ok", "message": "All report caches cleared"}


@router.get("/status")
async def mongo_status():
    """Check MongoDB connection health (public endpoint for diagnostics)."""
    from db.mongo import is_mongo_available, check_mongo_health
    available = await is_mongo_available()
    return {
        "mongo_available": available,
        "message": "MongoDB connected" if available else "MongoDB unavailable — check MONGO_DB_URL credentials",
    }
