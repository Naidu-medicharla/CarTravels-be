from pydantic import BaseModel
from typing import List

class KPISchema(BaseModel):
    today_bookings: int
    today_revenue: str
    available_cars: int
    under_maintenance: int

class TodayScheduleSchema(BaseModel):
    id: str
    time: str
    title: str
    customer: str
    phone: str
    vehicle: str
    plate: str
    driver: str
    pickup: str
    destination: str
    status: str
    payment: str

class RecentBookingSchema(BaseModel):
    customer: str
    vehicle: str
    time: str
    status: str

class RevenueSummarySchema(BaseModel):
    today: str
    yesterday: str
    this_month: str

class DashboardDetailsResponse(BaseModel):
    kpis: KPISchema
    today_schedule: List[TodayScheduleSchema]
    recent_bookings: List[RecentBookingSchema]
    revenue_summary: RevenueSummarySchema
