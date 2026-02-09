from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.session import get_db
from app.middleware.firebase_auth import get_current_uid
from modules.users.service import get_or_create_user
from app.schemas.users import UpsertProfileRequest, UserResponse

router = APIRouter()

@router.get("/me", response_model=UserResponse)
def get_me(
    db: Session = Depends(get_db),
    uid: str = Depends(get_current_uid),
):
    user = get_or_create_user(db, uid)
    status = user.subscription.status if user.subscription else "free"
    return UserResponse(firebase_uid=user.firebase_uid, email=user.email, subscription_status=status)

@router.post("/me", response_model=UserResponse)
def upsert_me(
    body: UpsertProfileRequest,
    db: Session = Depends(get_db),
    uid: str = Depends(get_current_uid),
):
    user = get_or_create_user(db, uid, email=body.email)
    status = user.subscription.status if user.subscription else "free"
    return UserResponse(firebase_uid=user.firebase_uid, email=user.email, subscription_status=status)
