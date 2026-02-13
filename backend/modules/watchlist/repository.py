"""
Watchlist repository – direct database operations for watchlist items.
"""

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import WatchlistItem


def add_item(db: Session, *, user_id: int, symbol: str, display_name: str | None = None) -> WatchlistItem:
    item = WatchlistItem(user_id=user_id, symbol=symbol, display_name=display_name)
    db.add(item)
    db.flush()
    return item


def get_item(db: Session, *, user_id: int, symbol: str) -> WatchlistItem | None:
    return db.execute(
        select(WatchlistItem).where(
            WatchlistItem.user_id == user_id,
            WatchlistItem.symbol == symbol,
        )
    ).scalar_one_or_none()


def list_items(db: Session, user_id: int) -> Sequence[WatchlistItem]:
    return db.execute(
        select(WatchlistItem)
        .where(WatchlistItem.user_id == user_id)
        .order_by(WatchlistItem.created_at.desc())
    ).scalars().all()


def delete_item(db: Session, item: WatchlistItem) -> None:
    db.delete(item)
    db.flush()
