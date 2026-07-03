from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from src.models.notification import NotificationType, NotificationRecipientRole


class NotificationOut(BaseModel):
    id:             int
    recipient_role: NotificationRecipientRole
    type:           NotificationType
    title:          str
    message:        str
    reference_id:   Optional[str] = None
    is_read:        bool
    created_at:     datetime

    model_config = {"from_attributes": True}


class UnreadCountOut(BaseModel):
    unread_count: int
