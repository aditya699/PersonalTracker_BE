from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: str = Field(..., min_length=2)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserProfile(BaseModel):
    user_id: str
    email: str
    name: str
    created_at: datetime
    is_active: bool
