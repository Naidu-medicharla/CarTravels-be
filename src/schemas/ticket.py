from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from src.models.ticket import TicketStatus


class TicketCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone_number: str
    subject: str
    message: str


class AdminReplyRequest(BaseModel):
    admin_reply: str
    mark_resolved: bool = True


class TicketOut(BaseModel):
    ticket_id: int
    user_id: Optional[int] = None
    full_name: str
    email: str
    phone_number: str
    subject: str
    message: str
    admin_reply: Optional[str] = None
    status: TicketStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
