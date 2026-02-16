"""
Admin service – business logic for admin registration and management.

Registration flow:
  1. If no admins exist yet  → the caller becomes the first super_admin.
  2. If admins exist         → only an existing admin can invite a new admin.
                               The inviter's Firebase UID must already be in the DB.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from common.logging import get_logger
from db.models import AdminRole
from modules.admin.repository import (
    get_admin_by_firebase_uid,
    get_admin_by_email,
    get_admin_by_id,
    admin_count,
    create_admin as repo_create_admin,
    list_admins as repo_list_admins,
    update_admin_profile as repo_update_profile,
    deactivate_admin as repo_deactivate,
    delete_admin as repo_delete,
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register_admin(
    db: Session,
    firebase_uid: str,
    *,
    first_name: str,
    last_name: str,
    email: str,
    phone_number: str | None = None,
):
    """
    Register a new admin.  First admin becomes super_admin automatically.
    Subsequent registrations require an existing admin to approve (handled
    via the `invite_admin` flow).  This endpoint is only open when there
    are zero admins in the database.
    """
    # Check if already registered
    existing = get_admin_by_firebase_uid(db, firebase_uid)
    if existing is not None:
        return existing  # idempotent

    # Check email uniqueness
    if get_admin_by_email(db, email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An admin with this email already exists.",
        )

    total = admin_count(db)

    if total > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin registration is closed. Ask an existing admin to invite you.",
        )

    # First admin → super_admin
    admin = repo_create_admin(
        db,
        firebase_uid=firebase_uid,
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone_number=phone_number,
        role=AdminRole.super_admin,
        invited_by_id=None,
    )
    logger.info(
        f"First super_admin registered: {email}",
        extra={"admin_id": admin.id, "event": "super_admin_registered"},
    )
    return admin


# ---------------------------------------------------------------------------
# Invitation (existing admin invites another)
# ---------------------------------------------------------------------------

def invite_admin(
    db: Session,
    inviter_uid: str,
    *,
    invitee_firebase_uid: str,
    first_name: str,
    last_name: str,
    email: str,
    phone_number: str | None = None,
    role: str = "admin",
):
    """An existing admin creates a new admin account for an invitee."""
    inviter = get_admin_by_firebase_uid(db, inviter_uid)
    if inviter is None or not inviter.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inviter is not a valid active admin.",
        )

    # Only super_admin can create other super_admins
    target_role = AdminRole(role)
    if target_role == AdminRole.super_admin and inviter.role != AdminRole.super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only a super_admin can create another super_admin.",
        )

    # Duplicate checks
    if get_admin_by_firebase_uid(db, invitee_firebase_uid):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This Firebase account is already registered as an admin.",
        )
    if get_admin_by_email(db, email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An admin with this email already exists.",
        )

    admin = repo_create_admin(
        db,
        firebase_uid=invitee_firebase_uid,
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone_number=phone_number,
        role=target_role,
        invited_by_id=inviter.id,
    )
    logger.info(
        f"Admin invited: {email} by admin {inviter.id}",
        extra={"admin_id": admin.id, "inviter_id": inviter.id, "event": "admin_invited"},
    )
    return admin


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

def get_admin_me(db: Session, firebase_uid: str):
    """Return the admin record for the given Firebase UID, or 404."""
    admin = get_admin_by_firebase_uid(db, firebase_uid)
    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not registered.",
        )
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is deactivated.",
        )
    return admin


def list_all_admins(db: Session):
    return repo_list_admins(db)


# ---------------------------------------------------------------------------
# Management
# ---------------------------------------------------------------------------

def deactivate_admin_account(db: Session, admin_id: int, requester_uid: str):
    """Deactivate an admin.  Only super_admin can do this."""
    requester = get_admin_by_firebase_uid(db, requester_uid)
    if requester is None or requester.role != AdminRole.super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only a super_admin can deactivate an admin.",
        )
    target = get_admin_by_id(db, admin_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Admin not found.")
    if target.id == requester.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself.",
        )
    return repo_deactivate(db, target)


def remove_admin(db: Session, admin_id: int, requester_uid: str):
    """Permanently delete an admin.  Only super_admin can do this."""
    requester = get_admin_by_firebase_uid(db, requester_uid)
    if requester is None or requester.role != AdminRole.super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only a super_admin can remove an admin.",
        )
    target = get_admin_by_id(db, admin_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Admin not found.")
    if target.id == requester.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove yourself.",
        )
    repo_delete(db, target)


def check_is_admin(db: Session, firebase_uid: str) -> bool:
    """Return True if the UID belongs to an active admin."""
    admin = get_admin_by_firebase_uid(db, firebase_uid)
    return admin is not None and admin.is_active
