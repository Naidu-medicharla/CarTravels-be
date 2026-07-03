from pydantic import BaseModel, EmailStr
from src.models.user import UserRole


class CreateAdminRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = None
    password: str


class AdminUserOut(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    is_active: bool

    model_config = {"from_attributes": True}

class BlockUserRequest(BaseModel):
    reason: str

class UserDetailOut(BaseModel):
    id: int
    name: str
    email: str
    phone: str | None = None
    role: UserRole
    is_active: bool
    is_blocked: bool
    block_reason: str | None = None
    bookings: list['BookingOut'] = []

    model_config = {"from_attributes": True}

from src.schemas.booking import BookingOut
UserDetailOut.model_rebuild()
