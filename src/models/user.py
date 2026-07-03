import enum
from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.database.db import Base


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    USER = "USER"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole, name="userrole", create_type=True), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)
    block_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    bookings = relationship("Booking", back_populates="user")

