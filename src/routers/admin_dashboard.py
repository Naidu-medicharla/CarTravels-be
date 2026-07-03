from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.core.dependencies import require_admin
from src.models.user import User
from src.schemas.dashboard import DashboardDetailsResponse
from src.services.dashboard_service import get_dashboard_details

router = APIRouter()

@router.get(
    "/details",
    response_model=DashboardDetailsResponse,
    summary="Get Dashboard Details (Admin)",
)
def dashboard_details(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    Get aggregated data for the admin dashboard:
    KPIs, today's schedule, recent bookings, and revenue summary.
    """
    return get_dashboard_details(db)
