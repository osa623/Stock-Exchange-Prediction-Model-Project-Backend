"""
Pydantic schemas for user endpoints.

Sensitive fields (pin_hash, pin_failed_attempts, pin_locked_until) are NEVER
included in any response model.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, EmailStr, field_validator


# ---------------------------------------------------------------------------
# Enums (mirror db/models enums for request validation)
# ---------------------------------------------------------------------------

class ExperienceLevelEnum(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class PrimaryGoalEnum(str, Enum):
    trading = "trading"
    long_term_investing = "long_term_investing"
    research_analysis = "research_analysis"


class InvestorTypeEnum(str, Enum):
    retail = "retail"
    student = "student"
    professional = "professional"


class PortfolioSizeEnum(str, Enum):
    size_0_500k = "0_500k"
    size_500k_10m = "500k_10m"
    size_10m_plus = "10m_plus"


class SubscriptionStatusEnum(str, Enum):
    free = "free"
    premium = "premium"


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class ProfileUpdateRequest(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    username: Optional[str] = Field(None, min_length=3, max_length=40)
    phone_number: Optional[str] = Field(None, max_length=20)
    avatar_url: Optional[str] = Field(None, max_length=512)


class OnboardingUpdateRequest(BaseModel):
    experience_level: ExperienceLevelEnum
    primary_goal: PrimaryGoalEnum
    investor_type: Optional[InvestorTypeEnum] = None
    portfolio_size: Optional[PortfolioSizeEnum] = None


class PinSetRequest(BaseModel):
    pin: str = Field(..., min_length=4, max_length=4)

    @field_validator("pin")
    @classmethod
    def pin_must_be_digits(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("PIN must be exactly 4 digits")
        return v


class PinVerifyRequest(BaseModel):
    pin: str = Field(..., min_length=4, max_length=4)

    @field_validator("pin")
    @classmethod
    def pin_must_be_digits(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("PIN must be exactly 4 digits")
        return v


class RegisterRequest(BaseModel):
    """Used when the user's Postgres row does not exist yet (first login)."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    username: str = Field(..., min_length=3, max_length=40)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=20)


# ---------------------------------------------------------------------------
# Response schemas (no sensitive fields)
# ---------------------------------------------------------------------------

class OnboardingResponse(BaseModel):
    experience_level: ExperienceLevelEnum
    primary_goal: PrimaryGoalEnum
    investor_type: Optional[InvestorTypeEnum] = None
    portfolio_size: Optional[PortfolioSizeEnum] = None

    model_config = {"from_attributes": True}


class UserMeResponse(BaseModel):
    firebase_uid: str
    first_name: str
    last_name: str
    username: str
    email: Optional[str] = None
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None

    pin_is_set: bool
    subscription_status: SubscriptionStatusEnum

    onboarding: Optional[OnboardingResponse] = None
    created_at: datetime

    model_config = {"from_attributes": True}

