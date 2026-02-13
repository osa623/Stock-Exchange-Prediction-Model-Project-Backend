"""
Portfolio service – business logic for portfolio management, position CRUD,
and Excel import.

firebase_uid is always the trusted value from the auth middleware.
"""

import io
import re
from decimal import Decimal, InvalidOperation

from fastapi import HTTPException, status, UploadFile
from sqlalchemy.orm import Session

from common.logging import get_logger
from db.models import (
    PortfolioSourceType,
    ImportStatus,
)
from modules.users.repository import get_user_by_firebase_uid
from modules.portfolio.repository import (
    create_portfolio as repo_create_portfolio,
    get_portfolio_by_id,
    list_portfolios_for_user,
    update_portfolio as repo_update_portfolio,
    delete_portfolio as repo_delete_portfolio,
    upsert_position as repo_upsert_position,
    get_position_by_symbol,
    delete_position as repo_delete_position,
    create_import_record,
    update_import_record,
)

logger = get_logger(__name__)

_SYMBOL_RE = re.compile(r"^[A-Z0-9.\-]{1,15}$")

# Header aliases for Excel import mapping
_HEADER_MAP: dict[str, str] = {
    "symbol": "symbol",
    "ticker": "symbol",
    "qty": "qty",
    "quantity": "qty",
    "avg": "avg_price",
    "avg_price": "avg_price",
    "avg price": "avg_price",
    "total": "total_cost",
    "total_cost": "total_cost",
    "total cost": "total_cost",
    "bes": "bes",
    "currency": "currency",
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resolve_user_id(db: Session, firebase_uid: str) -> int:
    """Return internal user PK or 404."""
    user = get_user_by_firebase_uid(db, firebase_uid)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not registered.",
        )
    return user.id


def _get_owned_portfolio(db: Session, portfolio_id: int, user_id: int):
    """Fetch portfolio and enforce ownership."""
    portfolio = get_portfolio_by_id(db, portfolio_id)
    if portfolio is None or portfolio.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found.",
        )
    return portfolio


# ---------------------------------------------------------------------------
# Portfolio CRUD
# ---------------------------------------------------------------------------

def create_portfolio(
    db: Session,
    firebase_uid: str,
    *,
    name: str,
    base_currency: str | None = None,
):
    user_id = _resolve_user_id(db, firebase_uid)
    portfolio = repo_create_portfolio(
        db, user_id=user_id, name=name, base_currency=base_currency,
    )
    db.commit()
    db.refresh(portfolio)
    return portfolio


def list_my_portfolios(db: Session, firebase_uid: str):
    user_id = _resolve_user_id(db, firebase_uid)
    return list_portfolios_for_user(db, user_id)


def get_portfolio_detail(db: Session, firebase_uid: str, portfolio_id: int):
    user_id = _resolve_user_id(db, firebase_uid)
    return _get_owned_portfolio(db, portfolio_id, user_id)


def update_portfolio(
    db: Session,
    firebase_uid: str,
    portfolio_id: int,
    *,
    name: str | None = None,
    base_currency: str | None = ...,  # type: ignore[assignment]
):
    user_id = _resolve_user_id(db, firebase_uid)
    portfolio = _get_owned_portfolio(db, portfolio_id, user_id)
    portfolio = repo_update_portfolio(
        db, portfolio, name=name, base_currency=base_currency,
    )
    db.commit()
    db.refresh(portfolio)
    return portfolio


def delete_portfolio(db: Session, firebase_uid: str, portfolio_id: int):
    user_id = _resolve_user_id(db, firebase_uid)
    portfolio = _get_owned_portfolio(db, portfolio_id, user_id)
    repo_delete_portfolio(db, portfolio)
    db.commit()


# ---------------------------------------------------------------------------
# Position CRUD
# ---------------------------------------------------------------------------

def upsert_position(
    db: Session,
    firebase_uid: str,
    portfolio_id: int,
    *,
    symbol: str,
    qty: Decimal,
    avg_price: Decimal,
    total_cost: Decimal | None = None,
    bes: Decimal | None = None,
    currency: str | None = None,
):
    user_id = _resolve_user_id(db, firebase_uid)
    portfolio = _get_owned_portfolio(db, portfolio_id, user_id)

    position = repo_upsert_position(
        db,
        portfolio_id=portfolio.id,
        symbol=symbol,
        qty=qty,
        avg_price=avg_price,
        total_cost=total_cost,
        bes=bes,
        currency=currency,
    )
    db.commit()
    db.refresh(position)
    return position


def delete_position(
    db: Session, firebase_uid: str, portfolio_id: int, symbol: str,
):
    symbol = symbol.strip().upper()
    if not _SYMBOL_RE.match(symbol):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid symbol format.",
        )

    user_id = _resolve_user_id(db, firebase_uid)
    portfolio = _get_owned_portfolio(db, portfolio_id, user_id)

    position = get_position_by_symbol(db, portfolio.id, symbol)
    if position is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Position '{symbol}' not found in portfolio.",
        )

    repo_delete_position(db, position)
    db.commit()


# ---------------------------------------------------------------------------
# Excel Import
# ---------------------------------------------------------------------------

def import_excel(
    db: Session,
    firebase_uid: str,
    portfolio_id: int,
    file: UploadFile,
):
    """
    Parse an uploaded .xlsx file, upsert positions, and record the import.
    Returns the PortfolioImport ORM object.
    """
    user_id = _resolve_user_id(db, firebase_uid)
    portfolio = _get_owned_portfolio(db, portfolio_id, user_id)

    # Validate file type
    filename = file.filename or "unknown.xlsx"
    if not filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only .xlsx files are accepted.",
        )

    # Read file content
    try:
        content = file.file.read()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read uploaded file.",
        )

    # Create import record (status = received)
    import_record = create_import_record(
        db,
        portfolio_id=portfolio.id,
        user_id=user_id,
        original_filename=filename,
        status=ImportStatus.received,
    )
    db.flush()

    # Parse workbook
    try:
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        ws = wb.active
        if ws is None:
            raise ValueError("Workbook has no active sheet.")

        rows = list(ws.iter_rows(values_only=True))
        if len(rows) < 2:
            raise ValueError("File must contain a header row and at least one data row.")

        # Map headers
        raw_headers = [str(h).strip().lower() if h else "" for h in rows[0]]
        col_map: dict[str, int] = {}  # field_name -> column index
        for idx, raw in enumerate(raw_headers):
            mapped = _HEADER_MAP.get(raw)
            if mapped and mapped not in col_map:
                col_map[mapped] = idx

        if "symbol" not in col_map or "qty" not in col_map or "avg_price" not in col_map:
            raise ValueError(
                "Missing required columns. File must contain: symbol (or ticker), "
                "qty (or quantity), and avg_price (or avg/avg price)."
            )

        data_rows = rows[1:]
        rows_total = len(data_rows)
        rows_parsed = 0
        rows_failed = 0
        errors: list[str] = []

        for row_num, row in enumerate(data_rows, start=2):
            try:
                symbol_val = row[col_map["symbol"]]
                if symbol_val is None:
                    raise ValueError("symbol is empty")
                symbol_str = str(symbol_val).strip().upper()
                if not _SYMBOL_RE.match(symbol_str):
                    raise ValueError(f"invalid symbol: {symbol_str}")

                qty_val = row[col_map["qty"]]
                qty = Decimal(str(qty_val))
                if qty < 0:
                    raise ValueError("qty must be >= 0")

                avg_val = row[col_map["avg_price"]]
                avg_price = Decimal(str(avg_val))
                if avg_price < 0:
                    raise ValueError("avg_price must be >= 0")

                total_cost = None
                if "total_cost" in col_map:
                    tc_val = row[col_map["total_cost"]]
                    if tc_val is not None:
                        total_cost = Decimal(str(tc_val))

                bes = None
                if "bes" in col_map:
                    bes_val = row[col_map["bes"]]
                    if bes_val is not None:
                        bes = Decimal(str(bes_val))

                currency = None
                if "currency" in col_map:
                    cur_val = row[col_map["currency"]]
                    if cur_val is not None:
                        currency = str(cur_val).strip()[:10]

                repo_upsert_position(
                    db,
                    portfolio_id=portfolio.id,
                    symbol=symbol_str,
                    qty=qty,
                    avg_price=avg_price,
                    total_cost=total_cost,
                    bes=bes,
                    currency=currency,
                )
                rows_parsed += 1

            except (ValueError, InvalidOperation, TypeError, IndexError) as e:
                rows_failed += 1
                errors.append(f"Row {row_num}: {e}")

        wb.close()

        # Update source_type to mixed/excel
        if portfolio.source_type == PortfolioSourceType.manual:
            repo_update_portfolio(db, portfolio, source_type=PortfolioSourceType.excel)
        elif portfolio.source_type != PortfolioSourceType.excel:
            repo_update_portfolio(db, portfolio, source_type=PortfolioSourceType.mixed)

        final_status = ImportStatus.parsed if rows_failed == 0 else ImportStatus.failed
        error_summary = "\n".join(errors[:50]) if errors else None

        update_import_record(
            db,
            import_record,
            status=final_status,
            rows_total=rows_total,
            rows_parsed=rows_parsed,
            rows_failed=rows_failed,
            error_summary=error_summary,
        )

        db.commit()
        db.refresh(import_record)
        return import_record

    except HTTPException:
        raise
    except ValueError as ve:
        update_import_record(
            db, import_record,
            status=ImportStatus.failed,
            error_summary=str(ve),
        )
        db.commit()
        db.refresh(import_record)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )
    except Exception as exc:
        logger.exception("Excel import failed unexpectedly")
        update_import_record(
            db, import_record,
            status=ImportStatus.failed,
            error_summary=f"Internal error: {type(exc).__name__}",
        )
        db.commit()
        db.refresh(import_record)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process the uploaded file.",
        )
