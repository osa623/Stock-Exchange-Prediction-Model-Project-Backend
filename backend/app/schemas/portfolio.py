"""
Pydantic schemas for portfolio endpoints.

Only user-input fields are accepted and returned.
Computed/derived fields (unrealized P&L, win rate, etc.) are never stored
and are NOT part of these schemas.
"""

from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SourceTypeEnum(str, Enum):
    manual = "manual"
    excel = "excel"
    mixed = "mixed"


class ImportStatusEnum(str, Enum):
    received = "received"
    parsed = "parsed"
    failed = "failed"


# ---------------------------------------------------------------------------
# Validators (reusable)
# ---------------------------------------------------------------------------

_SYMBOL_RE = re.compile(r"^[A-Z0-9.\-]{1,15}$")


def _validate_symbol(v: str) -> str:
    v = v.strip().upper()
    if not _SYMBOL_RE.match(v):
        raise ValueError(
            "Symbol must be 1-15 uppercase alphanumeric characters, dots, or hyphens."
        )
    return v


# ---------------------------------------------------------------------------
# Position schemas
# ---------------------------------------------------------------------------

class PositionUpsertRequest(BaseModel):
    """Add or update a single position in a portfolio."""

    symbol: str = Field(..., min_length=1, max_length=15)
    qty: Decimal = Field(..., ge=0, decimal_places=6)
    avg_price: Decimal = Field(..., ge=0, decimal_places=6)
    total_cost: Optional[Decimal] = Field(None, ge=0, decimal_places=6)
    bes: Optional[Decimal] = Field(None, ge=0, decimal_places=6)
    currency: Optional[str] = Field(None, max_length=10)

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        return _validate_symbol(v)


class PositionResponse(BaseModel):
    id: int
    portfolio_id: int
    symbol: str
    qty: Decimal
    avg_price: Decimal
    total_cost: Optional[Decimal] = None
    bes: Optional[Decimal] = None
    currency: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Portfolio schemas
# ---------------------------------------------------------------------------

class PortfolioCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    base_currency: Optional[str] = Field(None, max_length=10)


class PortfolioUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    base_currency: Optional[str] = Field(None, max_length=10)


class PortfolioResponse(BaseModel):
    id: int
    name: str
    base_currency: Optional[str] = None
    source_type: SourceTypeEnum
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PortfolioDetailResponse(PortfolioResponse):
    positions: list[PositionResponse] = []


# ---------------------------------------------------------------------------
# Import schemas
# ---------------------------------------------------------------------------

class ImportResponse(BaseModel):
    id: int
    portfolio_id: int
    original_filename: str
    status: ImportStatusEnum
    rows_total: int
    rows_parsed: int
    rows_failed: int
    error_summary: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
