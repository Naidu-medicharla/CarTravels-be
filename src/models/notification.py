import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database.db import Base


class NotificationType(str, enum.Enum):
    NEW_BOOKING            = "NEW_BOOKING"
    CANCEL_REQUEST         = "CANCEL_REQUEST"
    NEW_TICKET             = "NEW_TICKET"
    DRIVER_ASSIGNED        = "DRIVER_ASSIGNED"
    CANCELLATION_APPROVED  = "CANCELLATION_APPROVED"
    CANCELLATION_REJECTED  = "CANCELLATION_REJECTED"
    TICKET_REPLY           = "TICKET_REPLY"
    BOOKING_CONFIRMED      = "BOOKING_CONFIRMED"
    BOOKING_MILESTONE      = "BOOKING_MILESTONE"


class NotificationRecipientRole(str, enum.Enum):
    USER  = "USER"
    ADMIN = "ADMIN"


class Notification(Base):
    __tablename__ = "notifications"

    id             = Column(Integer, primary_key=True, index=True, autoincrement=True)
    recipient_id   = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_role = Column(Enum(NotificationRecipientRole, name="notificationrecipientrole", create_type=True), nullable=False)
    type           = Column(Enum(NotificationType, name="notificationtype", create_type=True), nullable=False)
    title          = Column(String(200), nullable=False)
    message        = Column(String(500), nullable=False)
    reference_id   = Column(String(100), nullable=True)
    is_read        = Column(Boolean, default=False, nullable=False)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())

    recipient = relationship("User")
