from fastapi import APIRouter, Depends
from app.middleware.firebase_auth import get_current_uid

router = APIRouter()

@router.get("/whoami")
def whoami(uid: str = Depends(get_current_uid)):
    return {"uid": uid}
