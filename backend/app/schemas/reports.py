"""
Report Schemas

Pydantic models for report API request validation and response serialization.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import re


# ── Request / Query Validation ───────────────────────────────────────────

# Allowed access‐level values
VALID_ACCESS_LEVELS = {"public", "registered", "premium"}

# Safe string pattern — blocks Mongo operator injection ($, {, })
SAFE_STRING_RE = re.compile(r"^[A-Za-z0-9 _\-\.\/]+$")


class ReportListQuery(BaseModel):
    """Validated query params for report listing."""

    category: Optional[str] = Field(
        None, max_length=100, description="Filter by category"
    )
    subcategory: Optional[str] = Field(
        None, max_length=100, description="Filter by subcategory"
    )
    symbol: Optional[str] = Field(
        None, max_length=10, description="Filter by stock symbol"
    )
    search: Optional[str] = Field(
        None, max_length=100, description="Text search across title, symbol, tags"
    )
    page: int = Field(1, ge=1, le=1000, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")

    @field_validator("category", "subcategory", "symbol", "search", mode="before")
    @classmethod
    def sanitize_string(cls, v):
        if v is None:
            return v
        v = str(v).strip()
        if not v:
            return None
        # Block Mongo operator injection
        if v.startswith("$") or "{" in v or "}" in v:
            raise ValueError("Invalid characters in query parameter")
        return v


# ── Response Models ──────────────────────────────────────────────────────


class ReportSummary(BaseModel):
    """Public / list-level report representation."""

    id: str
    category: str
    subcategory: Optional[str] = None
    title: str
    symbol: Optional[str] = None
    access_level: str = "public"
    summary: Optional[str] = None
    tags: list[str] = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReportDetail(ReportSummary):
    """Registered-user level — includes report data."""

    data: dict = {}
    updated_at: Optional[datetime] = None


class ReportFull(ReportDetail):
    """Premium level — includes everything + exportable raw data."""

    raw_data: Optional[dict] = None
    methodology: Optional[str] = None
    metadata: Optional[dict] = None


class ReportListResponse(BaseModel):
    """Paginated report list response."""

    reports: list[ReportSummary] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0


class FolderNode(BaseModel):
    """Single node in the folder tree."""

    name: str
    path: str
    children: list["FolderNode"] = []
    report_count: int = 0


class FolderTreeResponse(BaseModel):
    """Full folder tree response."""

    tree: list[FolderNode] = []
    total_reports: int = 0


class CacheStatsResponse(BaseModel):
    """Admin-only cache diagnostics."""

    report_list: dict
    report_detail: dict
    folder_tree: dict
