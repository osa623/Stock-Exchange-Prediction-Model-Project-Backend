"""
Portfolio repository – all direct database operations for portfolios,
positions, and import records.
"""

from decimal import Decimal
from typing import Sequence

from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from db.models import (
    Portfolio,
    PortfolioPosition,
    PortfolioImport,
    PortfolioSourceType,
    ImportStatus,
)


# ---------------------------------------------------------------------------
# Portfolio CRUD
# ---------------------------------------------------------------------------

def create_portfolio(
    db: Session,
    *,
    user_id: int,
    name: str,
    base_currency: str | None = None,
    source_type: PortfolioSourceType = PortfolioSourceType.manual,
) -> Portfolio:
    portfolio = Portfolio(
        user_id=user_id,
        name=name,
        base_currency=base_currency,
        source_type=source_type,
    )
    db.add(portfolio)
    db.flush()
    return portfolio


def get_portfolio_by_id(db: Session, portfolio_id: int) -> Portfolio | None:
    return db.execute(
        select(Portfolio).where(Portfolio.id == portfolio_id)
    ).scalar_one_or_none()


def list_portfolios_for_user(db: Session, user_id: int) -> Sequence[Portfolio]:
    return db.execute(
        select(Portfolio)
        .where(Portfolio.user_id == user_id)
        .order_by(Portfolio.created_at.desc())
    ).scalars().all()


def update_portfolio(
    db: Session,
    portfolio: Portfolio,
    *,
    name: str | None = None,
    base_currency: str | None = ...,  # type: ignore[assignment]
    source_type: PortfolioSourceType | None = None,
) -> Portfolio:
    if name is not None:
        portfolio.name = name
    if base_currency is not ...:
        portfolio.base_currency = base_currency
    if source_type is not None:
        portfolio.source_type = source_type
    db.flush()
    return portfolio


def delete_portfolio(db: Session, portfolio: Portfolio) -> None:
    db.delete(portfolio)
    db.flush()


# ---------------------------------------------------------------------------
# Position CRUD
# ---------------------------------------------------------------------------

def upsert_position(
    db: Session,
    *,
    portfolio_id: int,
    symbol: str,
    qty: Decimal,
    avg_price: Decimal,
    total_cost: Decimal | None = None,
    bes: Decimal | None = None,
    currency: str | None = None,
) -> PortfolioPosition:
    """Insert or update a position (keyed on portfolio_id + symbol)."""
    existing = db.execute(
        select(PortfolioPosition).where(
            PortfolioPosition.portfolio_id == portfolio_id,
            PortfolioPosition.symbol == symbol,
        )
    ).scalar_one_or_none()

    if existing is not None:
        existing.qty = qty
        existing.avg_price = avg_price
        existing.total_cost = total_cost
        existing.bes = bes
        existing.currency = currency
        db.flush()
        return existing

    position = PortfolioPosition(
        portfolio_id=portfolio_id,
        symbol=symbol,
        qty=qty,
        avg_price=avg_price,
        total_cost=total_cost,
        bes=bes,
        currency=currency,
    )
    db.add(position)
    db.flush()
    return position


def get_position_by_symbol(
    db: Session, portfolio_id: int, symbol: str,
) -> PortfolioPosition | None:
    return db.execute(
        select(PortfolioPosition).where(
            PortfolioPosition.portfolio_id == portfolio_id,
            PortfolioPosition.symbol == symbol,
        )
    ).scalar_one_or_none()


def delete_position(db: Session, position: PortfolioPosition) -> None:
    db.delete(position)
    db.flush()


def list_positions(db: Session, portfolio_id: int) -> Sequence[PortfolioPosition]:
    return db.execute(
        select(PortfolioPosition)
        .where(PortfolioPosition.portfolio_id == portfolio_id)
        .order_by(PortfolioPosition.symbol)
    ).scalars().all()


# ---------------------------------------------------------------------------
# Import records
# ---------------------------------------------------------------------------

def create_import_record(
    db: Session,
    *,
    portfolio_id: int,
    user_id: int,
    original_filename: str,
    file_url: str | None = None,
    status: ImportStatus = ImportStatus.received,
    rows_total: int = 0,
    rows_parsed: int = 0,
    rows_failed: int = 0,
    error_summary: str | None = None,
) -> PortfolioImport:
    record = PortfolioImport(
        portfolio_id=portfolio_id,
        user_id=user_id,
        original_filename=original_filename,
        file_url=file_url,
        status=status,
        rows_total=rows_total,
        rows_parsed=rows_parsed,
        rows_failed=rows_failed,
        error_summary=error_summary,
    )
    db.add(record)
    db.flush()
    return record


def update_import_record(
    db: Session,
    record: PortfolioImport,
    *,
    status: ImportStatus | None = None,
    rows_total: int | None = None,
    rows_parsed: int | None = None,
    rows_failed: int | None = None,
    error_summary: str | None = ...,  # type: ignore[assignment]
) -> PortfolioImport:
    if status is not None:
        record.status = status
    if rows_total is not None:
        record.rows_total = rows_total
    if rows_parsed is not None:
        record.rows_parsed = rows_parsed
    if rows_failed is not None:
        record.rows_failed = rows_failed
    if error_summary is not ...:
        record.error_summary = error_summary
    db.flush()
    return record
