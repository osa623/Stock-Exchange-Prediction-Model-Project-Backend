"""
Pydantic schemas for admin registration and management endpoints.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field, EmailStr, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class AdminRoleEnum(str, Enum):
    super_admin = "super_admin"
    admin = "admin"


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class AdminRegisterRequest(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone_number: Optional[str] = Field(None, max_length=20)


class AdminInviteRequest(BaseModel):
    firebase_uid: str = Field(..., min_length=1, max_length=255)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone_number: Optional[str] = Field(None, max_length=20)
    role: AdminRoleEnum = AdminRoleEnum.admin


class AdminProfileUpdateRequest(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    avatar_url: Optional[str] = Field(None, max_length=512)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class AdminResponse(BaseModel):
    id: int
    firebase_uid: str
    first_name: str
    last_name: str
    email: str
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None
    role: AdminRoleEnum
    is_active: bool
    invited_by_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_validator("is_active", mode="before")
    @classmethod
    def coerce_is_active(cls, v):
        return bool(v)

    class Config:
        from_attributes = True


class AdminListResponse(BaseModel):
    admins: List[AdminResponse]
    total: int


class AdminRegistrationStatusResponse(BaseModel):
    """Whether self-registration is open (no admins exist yet)."""
    registration_open: bool
    admin_count: int
