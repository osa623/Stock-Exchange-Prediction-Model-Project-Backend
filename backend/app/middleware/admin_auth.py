"""
Admin authentication middleware.
Checks that the authenticated Firebase UID belongs to an active admin
stored in the database.  Falls back to ADMIN_UIDS env var if configured.
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.middleware.firebase_auth import get_current_uid
from db.session import get_db
from modules.admin.repository import get_admin_by_firebase_uid
from common.config import settings
from common.logging import get_logger

logger = get_logger(__name__)


async def require_admin(
    uid: str = Depends(get_current_uid),
    db: Session = Depends(get_db),
) -> str:
    """
    Dependency that ensures the caller is an active admin.

    1. First checks the Admin table in the database.
    2. Falls back to ADMIN_UIDS env var for backwards compatibility.
    """
    # Primary check – database
    admin = get_admin_by_firebase_uid(db, uid)
    if admin is not None and admin.is_active:
        return uid

    # Fallback – env var (allows bootstrapping before first DB registration)
    admin_uids = [u.strip() for u in settings.ADMIN_UIDS.split(",") if u.strip()]
    if uid in admin_uids:
        return uid

    logger.warning(
        "Non-admin access attempt",
        extra={"uid": uid, "event": "admin_access_denied"},
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admin access required.",
    )
