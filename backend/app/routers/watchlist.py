"""
Watchlist router – all endpoints require Firebase authentication.

firebase_uid is ALWAYS derived from the verified token via ``get_current_uid``.
It is never accepted from the request body.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.session import get_db
from app.middleware.firebase_auth import get_current_uid
from app.schemas.watchlist import WatchlistAddRequest, WatchlistItemResponse
from app.schemas.common import OkResponse
from modules.watchlist.service import (
    add_to_watchlist,
    list_watchlist,
    remove_from_watchlist,
)

router = APIRouter()


@router.post("", response_model=WatchlistItemResponse, status_code=status.HTTP_201_CREATED)
def add(
    body: WatchlistAddRequest,
    db: Session = Depends(get_db),
    uid: str = Depends(get_current_uid),
):
    """Add a symbol to the authenticated user's watchlist."""
    return add_to_watchlist(db, uid, symbol=body.symbol, display_name=body.display_name)


@router.get("", response_model=list[WatchlistItemResponse])
def list_items(
    db: Session = Depends(get_db),
    uid: str = Depends(get_current_uid),
):
    """List all watchlist items for the authenticated user."""
    return list_watchlist(db, uid)


@router.delete("/{symbol}", response_model=OkResponse)
def remove(
    symbol: str,
    db: Session = Depends(get_db),
    uid: str = Depends(get_current_uid),
):
    """Remove a symbol from the authenticated user's watchlist."""
    remove_from_watchlist(db, uid, symbol)
    return OkResponse()
