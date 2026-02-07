from sqlalchemy.orm import Session
from db.models import User
from modules.users.repository import get_user_by_uid, create_user, update_email

def get_or_create_user(db: Session, firebase_uid: str, email: str | None = None) -> User:
    user = get_user_by_uid(db, firebase_uid)
    if user:
        return update_email(db, user, email)
    return create_user(db, firebase_uid, email)
