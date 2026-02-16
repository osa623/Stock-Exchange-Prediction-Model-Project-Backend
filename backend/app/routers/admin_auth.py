"""
Admin authentication / registration router.

Endpoints
---------
GET  /admin/auth/status   – check if self-registration is open
POST /admin/auth/register – self-register (only when 0 admins exist)
GET  /admin/auth/me       – get current admin profile
PATCH /admin/auth/me      – update current admin profile
GET  /admin/auth/admins   – list all admins  (admin-only)
POST /admin/auth/invite   – invite a new admin (admin-only)
DELETE /admin/auth/admins/{id} – remove an admin  (super_admin only)
PATCH  /admin/auth/admins/{id}/deactivate – deactivate admin (super_admin only)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.session import get_db
from app.middleware.firebase_auth import get_current_uid
from app.middleware.admin_auth import require_admin
from app.schemas.admin import (
    AdminRegisterRequest,
    AdminInviteRequest,
    AdminProfileUpdateRequest,
    AdminResponse,
    AdminListResponse,
    AdminRegistrationStatusResponse,
)
from modules.admin.service import (
    register_admin,
    invite_admin,
    get_admin_me,
    list_all_admins,
    deactivate_admin_account,
    remove_admin,
)
from modules.admin.repository import (
    admin_count,
    update_admin_profile,
    get_admin_by_firebase_uid,
)
from common.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


# ── Public (requires Firebase auth, but not admin) ─────────────────────────

@router.get("/status", response_model=AdminRegistrationStatusResponse)
def registration_status(db: Session = Depends(get_db)):
    """Check whether self-registration is open (0 admins in system)."""
    count = admin_count(db)
    return AdminRegistrationStatusResponse(
        registration_open=count == 0,
        admin_count=count,
    )


@router.post("/register", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
def register(
    body: AdminRegisterRequest,
    uid: str = Depends(get_current_uid),
    db: Session = Depends(get_db),
):
    """
    Self-register as the first admin (super_admin).
    Only succeeds when no admins exist yet.
    """
    admin = register_admin(
        db,
        firebase_uid=uid,
        first_name=body.first_name,
        last_name=body.last_name,
        email=body.email,
        phone_number=body.phone_number,
    )
    return AdminResponse.model_validate(admin)


@router.get("/me", response_model=AdminResponse)
def me(
    uid: str = Depends(get_current_uid),
    db: Session = Depends(get_db),
):
    """Get the current admin's profile (checks DB)."""
    admin = get_admin_me(db, uid)
    return AdminResponse.model_validate(admin)


@router.patch("/me", response_model=AdminResponse)
def update_me(
    body: AdminProfileUpdateRequest,
    uid: str = Depends(get_current_uid),
    db: Session = Depends(get_db),
):
    """Update fields on the current admin's profile."""
    admin = get_admin_by_firebase_uid(db, uid)
    if admin is None:
        raise HTTPException(status_code=404, detail="Admin not found.")
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        return AdminResponse.model_validate(admin)
    updated = update_admin_profile(db, admin, updates)
    return AdminResponse.model_validate(updated)


# ── Admin-only ─────────────────────────────────────────────────────────────

@router.get(
    "/admins",
    response_model=AdminListResponse,
    dependencies=[Depends(require_admin)],
)
def list_admins(db: Session = Depends(get_db)):
    """List all admin accounts."""
    admins = list_all_admins(db)
    return AdminListResponse(
        admins=[AdminResponse.model_validate(a) for a in admins],
        total=len(admins),
    )


@router.post(
    "/invite",
    response_model=AdminResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def invite(
    body: AdminInviteRequest,
    uid: str = Depends(get_current_uid),
    db: Session = Depends(get_db),
):
    """Invite a new admin (the invitee's Firebase account must already exist)."""
    admin = invite_admin(
        db,
        inviter_uid=uid,
        invitee_firebase_uid=body.firebase_uid,
        first_name=body.first_name,
        last_name=body.last_name,
        email=body.email,
        phone_number=body.phone_number,
        role=body.role.value,
    )
    return AdminResponse.model_validate(admin)


@router.patch(
    "/admins/{admin_id}/deactivate",
    response_model=dict,
    dependencies=[Depends(require_admin)],
)
def deactivate(
    admin_id: int,
    uid: str = Depends(get_current_uid),
    db: Session = Depends(get_db),
):
    """Deactivate an admin account. Super-admin only."""
    deactivate_admin_account(db, admin_id, uid)
    return {"detail": "Admin deactivated."}


@router.delete(
    "/admins/{admin_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_admin(
    admin_id: int,
    uid: str = Depends(get_current_uid),
    db: Session = Depends(get_db),
):
    """Permanently delete an admin. Super-admin only."""
    remove_admin(db, admin_id, uid)
