from sqlalchemy.orm import Session
from db.models import User, Subscription

def get_user_by_uid(db: Session, firebase_uid: str) -> User | None:
    return db.query(User).filter(User.firebase_uid == firebase_uid).first()

def create_user(db: Session, firebase_uid: str, email: str | None = None) -> User:
    user = User(firebase_uid=firebase_uid, email=email)
    db.add(user)
    db.flush()  # get user.id

    sub = Subscription(user_id=user.id, status="free", plan_id=None)
    db.add(sub)

    db.commit()
    db.refresh(user)
    return user

def update_email(db: Session, user: User, email: str | None) -> User:
    if email is not None:
        user.email = email
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
