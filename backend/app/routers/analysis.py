from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.session import get_db
from app.middleware.firebase_auth import get_current_uid
from modules.users.service import get_or_create_user
from modules.entitlements.service import can_access
from modules.analysis.fundamental.runner import get_basic_stock_data, get_full_fundamental_data

router = APIRouter()

@router.get("/stocks/{symbol}")
def stock_details(
    symbol: str,
    db: Session = Depends(get_db),
    uid: str = Depends(get_current_uid),
):
    user = get_or_create_user(db, uid)

    # Free access path
    if can_access(user, "stocks:details") and not can_access(user, "stocks:valuation"):
        basic = get_basic_stock_data(symbol)
        return {
            **basic,
            "note": "Upgrade to premium to view full valuations/ratios/cashflow"
        }

    # Premium access path
    if can_access(user, "stocks:valuation"):
        return get_full_fundamental_data(symbol)

    raise HTTPException(status_code=403, detail="Not allowed")
