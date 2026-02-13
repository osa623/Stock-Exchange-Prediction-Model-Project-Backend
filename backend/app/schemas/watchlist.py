"""
Pydantic schemas for watchlist (favorites) endpoints.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


_SYMBOL_RE = re.compile(r"^[A-Z0-9.\-]{1,15}$")


class WatchlistAddRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=15)
    display_name: Optional[str] = Field(None, max_length=120)

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        v = v.strip().upper()
        if not _SYMBOL_RE.match(v):
            raise ValueError(
                "Symbol must be 1-15 uppercase alphanumeric characters, dots, or hyphens."
            )
        return v


class WatchlistItemResponse(BaseModel):
    id: int
    symbol: str
    display_name: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
