from pydantic import BaseModel, constr
from typing import Optional
from datetime import datetime

class DriverBase(BaseModel):
    driver_name: str
    mobile_number: constr(min_length=10, max_length=15) # type: ignore

class DriverCreate(DriverBase):
    pass

class DriverOut(DriverBase):
    id: int
    driver_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DriverResponse(BaseModel):
    message: str
    driver_id: str
