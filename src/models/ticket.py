import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database.db import Base


class TicketStatus(str, enum.Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(150), nullable=False)
    phone_number = Column(String(20), nullable=False)
    subject = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    admin_reply = Column(Text, nullable=True)
    status = Column(Enum(TicketStatus, name="ticketstatus", create_type=True), default=TicketStatus.OPEN)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")
