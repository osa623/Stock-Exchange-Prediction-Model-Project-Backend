"""
Portfolio router – all endpoints require Firebase authentication.

firebase_uid is ALWAYS derived from the verified token via ``get_current_uid``.
It is never accepted from the request body.
"""

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from db.session import get_db
from app.middleware.firebase_auth import get_current_uid
from app.schemas.portfolio import (
    PortfolioCreateRequest,
    PortfolioUpdateRequest,
    PortfolioResponse,
    PortfolioDetailResponse,
    PositionUpsertRequest,
    PositionResponse,
    ImportResponse,
)
from app.schemas.common import OkResponse
from modules.portfolio.service import (
    create_portfolio,
    list_my_portfolios,
    get_portfolio_detail,
    update_portfolio,
    delete_portfolio,
    upsert_position,
    delete_position,
    import_excel,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Portfolio CRUD
# ---------------------------------------------------------------------------

@router.post("", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
def create(
    body: PortfolioCreateRequest,
    db: Session = Depends(get_db),
    uid: str = Depends(get_current_uid),
):
    """Create a new portfolio."""
    portfolio = create_portfolio(
        db, uid, name=body.name, base_currency=body.base_currency,
    )
    return portfolio


@router.get("", response_model=list[PortfolioResponse])
def list_portfolios(
    db: Session = Depends(get_db),
    uid: str = Depends(get_current_uid),
):
    """List all portfolios for the authenticated user."""
    return list_my_portfolios(db, uid)


@router.get("/{portfolio_id}", response_model=PortfolioDetailResponse)
def get_detail(
    portfolio_id: int,
    db: Session = Depends(get_db),
    uid: str = Depends(get_current_uid),
):
    """Get a portfolio with all its positions."""
    return get_portfolio_detail(db, uid, portfolio_id)


@router.patch("/{portfolio_id}", response_model=PortfolioResponse)
def patch_portfolio(
    portfolio_id: int,
    body: PortfolioUpdateRequest,
    db: Session = Depends(get_db),
    uid: str = Depends(get_current_uid),
):
    """Rename a portfolio or update its base currency."""
    kwargs: dict = {}
    if body.name is not None:
        kwargs["name"] = body.name
    if body.base_currency is not None:
        kwargs["base_currency"] = body.base_currency
    return update_portfolio(db, uid, portfolio_id, **kwargs)


@router.delete("/{portfolio_id}", response_model=OkResponse)
def remove_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    uid: str = Depends(get_current_uid),
):
    """Delete a portfolio and all its positions."""
    delete_portfolio(db, uid, portfolio_id)
    return OkResponse()


# ---------------------------------------------------------------------------
# Position CRUD
# ---------------------------------------------------------------------------

@router.put("/{portfolio_id}/positions", response_model=PositionResponse)
def upsert(
    portfolio_id: int,
    body: PositionUpsertRequest,
    db: Session = Depends(get_db),
    uid: str = Depends(get_current_uid),
):
    """Add or update a single position in a portfolio."""
    return upsert_position(
        db,
        uid,
        portfolio_id,
        symbol=body.symbol,
        qty=body.qty,
        avg_price=body.avg_price,
        total_cost=body.total_cost,
        bes=body.bes,
        currency=body.currency,
    )


@router.delete("/{portfolio_id}/positions/{symbol}", response_model=OkResponse)
def remove_position(
    portfolio_id: int,
    symbol: str,
    db: Session = Depends(get_db),
    uid: str = Depends(get_current_uid),
):
    """Remove a position from a portfolio by symbol."""
    delete_position(db, uid, portfolio_id, symbol)
    return OkResponse()


# ---------------------------------------------------------------------------
# Excel Import
# ---------------------------------------------------------------------------

@router.post("/{portfolio_id}/import", response_model=ImportResponse, status_code=status.HTTP_201_CREATED)
def import_positions(
    portfolio_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    uid: str = Depends(get_current_uid),
):
    """Upload an .xlsx file to bulk-import positions into a portfolio."""
    return import_excel(db, uid, portfolio_id, file)
