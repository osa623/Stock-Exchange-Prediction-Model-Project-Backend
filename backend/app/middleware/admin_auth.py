"""
Admin authentication middleware.
Checks that the authenticated Firebase UID is in the ADMIN_UIDS list.
"""

from fastapi import Depends, HTTPException, status
from app.middleware.firebase_auth import get_current_uid
from common.config import settings
from common.logging import get_logger

logger = get_logger(__name__)


async def require_admin(uid: str = Depends(get_current_uid)) -> str:
    """
    Dependency that ensures the caller is an admin.
    Configure allowed admin UIDs via the ADMIN_UIDS env variable
    (comma-separated list of Firebase UIDs).
    """
    admin_uids = [u.strip() for u in settings.ADMIN_UIDS.split(",") if u.strip()]
    if uid not in admin_uids:
        logger.warning(
            "Non-admin access attempt",
            extra={"uid": uid, "event": "admin_access_denied"},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return uid
