from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.session import get_db
from app.middleware.firebase_auth import get_current_uid
from modules.users.service import get_or_create_user

router = APIRouter()

@router.get("/subscription")
def subscription_status(
    db: Session = Depends(get_db),
    uid: str = Depends(get_current_uid),
):
    user = get_or_create_user(db, uid)
    status = user.subscription.status if user.subscription else "free"
    return {"status": status}

# Phase 2: checkout-session + webhook + premium upgrade
