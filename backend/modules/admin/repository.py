"""
Admin repository – direct database operations for the Admin model.
"""

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from db.models import Admin, AdminRole


# ---------------------------------------------------------------------------
# Lookups
# ---------------------------------------------------------------------------

def get_admin_by_firebase_uid(db: Session, firebase_uid: str) -> Admin | None:
    return db.execute(
        select(Admin).where(Admin.firebase_uid == firebase_uid)
    ).scalar_one_or_none()


def get_admin_by_email(db: Session, email: str) -> Admin | None:
    return db.execute(
        select(Admin).where(Admin.email == email)
    ).scalar_one_or_none()


def get_admin_by_id(db: Session, admin_id: int) -> Admin | None:
    return db.execute(
        select(Admin).where(Admin.id == admin_id)
    ).scalar_one_or_none()


def admin_count(db: Session) -> int:
    """Return total number of admins (used to detect first-admin scenario)."""
    return db.execute(
        select(func.count(Admin.id))
    ).scalar_one() or 0


def list_admins(db: Session) -> list[Admin]:
    return list(db.execute(
        select(Admin).order_by(Admin.created_at.desc())
    ).scalars().all())


# ---------------------------------------------------------------------------
# Creation
# ---------------------------------------------------------------------------

def create_admin(
    db: Session,
    *,
    firebase_uid: str,
    first_name: str,
    last_name: str,
    email: str,
    phone_number: str | None = None,
    avatar_url: str | None = None,
    role: AdminRole = AdminRole.admin,
    invited_by_id: int | None = None,
) -> Admin:
    """Create an admin record."""
    admin = Admin(
        firebase_uid=firebase_uid,
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone_number=phone_number,
        avatar_url=avatar_url,
        role=role,
        invited_by_id=invited_by_id,
        is_active=1,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


# ---------------------------------------------------------------------------
# Updates
# ---------------------------------------------------------------------------

def update_admin_profile(
    db: Session,
    admin: Admin,
    *,
    first_name: str | None = None,
    last_name: str | None = None,
    phone_number: str | None = None,
    avatar_url: str | None = None,
) -> Admin:
    if first_name is not None:
        admin.first_name = first_name
    if last_name is not None:
        admin.last_name = last_name
    if phone_number is not None:
        admin.phone_number = phone_number
    if avatar_url is not None:
        admin.avatar_url = avatar_url
    db.commit()
    db.refresh(admin)
    return admin


def deactivate_admin(db: Session, admin: Admin) -> Admin:
    admin.is_active = 0
    db.commit()
    db.refresh(admin)
    return admin


def delete_admin(db: Session, admin: Admin) -> None:
    db.delete(admin)
    db.commit()
