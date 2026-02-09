from pydantic import BaseModel, Field, EmailStr

class OnboardingData(BaseModel):
    investor_type: str | None = None
    experience: str | None = None
    goals: list[str] = Field(default_factory=list)

class UpsertProfileRequest(BaseModel):
    email: EmailStr | None = None  # Validates email format
    onboarding: OnboardingData | None = None 

class UserResponse(BaseModel):
    firebase_uid: str
    email: str | None
    subscription_status: str

