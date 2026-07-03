from pydantic import BaseModel, EmailStr
from src.models.user import UserRole


# ── Request Schemas ──────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = None
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ── Response Schemas ─────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: UserRole

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class MessageResponse(BaseModel):
    message: str
