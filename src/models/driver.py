from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.sql import func
from src.database.db import Base
import random
import string

def generate_driver_id():
    """Generate a formatted driver ID, e.g., DRV-A1B2C3"""
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"DRV-{random_str}"

class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    driver_id = Column(String(20), unique=True, index=True, nullable=False, default=generate_driver_id)
    driver_name = Column(String(150), nullable=False)
    mobile_number = Column(String(20), unique=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
