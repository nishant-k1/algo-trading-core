"""Auth-related request/response schemas."""

from pydantic import BaseModel


class TokenResponse(BaseModel):
    """JWT token for client."""

    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    """Simple login (single user): optional password for future use."""

    password: str | None = None


class RegisterRequest(BaseModel):
    """Register new user."""

    email: str
    password: str


class ChangePasswordRequest(BaseModel):
    """Change password for current user."""

    current_password: str
    new_password: str
