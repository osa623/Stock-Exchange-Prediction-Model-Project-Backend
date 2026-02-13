"""
Watchlist service – business logic for watchlist (favorites).

firebase_uid is always the trusted value from the auth middleware.
"""

import re

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from common.logging import get_logger
from modules.users.repository import get_user_by_firebase_uid
from modules.watchlist.repository import (
    add_item as repo_add_item,
    get_item as repo_get_item,
    list_items as repo_list_items,
    delete_item as repo_delete_item,
)

logger = get_logger(__name__)

_SYMBOL_RE = re.compile(r"^[A-Z0-9.\-]{1,15}$")


def _resolve_user_id(db: Session, firebase_uid: str) -> int:
    user = get_user_by_firebase_uid(db, firebase_uid)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not registered.",
        )
    return user.id


def add_to_watchlist(
    db: Session,
    firebase_uid: str,
    *,
    symbol: str,
    display_name: str | None = None,
):
    user_id = _resolve_user_id(db, firebase_uid)

    existing = repo_get_item(db, user_id=user_id, symbol=symbol)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Symbol '{symbol}' is already in your watchlist.",
        )

    item = repo_add_item(db, user_id=user_id, symbol=symbol, display_name=display_name)
    db.commit()
    db.refresh(item)
    return item


def list_watchlist(db: Session, firebase_uid: str):
    user_id = _resolve_user_id(db, firebase_uid)
    return repo_list_items(db, user_id)


def remove_from_watchlist(db: Session, firebase_uid: str, symbol: str):
    symbol = symbol.strip().upper()
    if not _SYMBOL_RE.match(symbol):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid symbol format.",
        )

    user_id = _resolve_user_id(db, firebase_uid)
    item = repo_get_item(db, user_id=user_id, symbol=symbol)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Symbol '{symbol}' not found in your watchlist.",
        )
    repo_delete_item(db, item)
    db.commit()
