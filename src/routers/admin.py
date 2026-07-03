from fastapi import APIRouter, Depends, status, Form
from typing import Optional
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.core.dependencies import require_admin
from src.models.user import User
from src.schemas.admin import CreateAdminRequest, AdminUserOut
from src.services.admin_service import create_admin_user

router = APIRouter()


@router.post(
    "/create-admin",
    response_model=AdminUserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Admin user (Admin only)",
)
def create_admin(
    name:     str           = Form(...),
    email:    str           = Form(...),
    phone:    Optional[str] = Form(None),
    password: str           = Form(...),
    db: Session = Depends(get_db),
    _: User   = Depends(require_admin),
):
    """
    **POST /admin/create-admin** — multipart/form-data

    Requires a valid ADMIN JWT token in Authorization header.
    Creates a new user with `role = ADMIN`.
    """
    payload   = CreateAdminRequest(name=name, email=email, phone=phone, password=password)
    new_admin = create_admin_user(db, payload)
    return new_admin

from fastapi import HTTPException
from src.schemas.admin import BlockUserRequest, UserDetailOut
from typing import List

@router.post(
    "/users/{email}/block",
    response_model=UserDetailOut,
    summary="Block a User (Admin only)",
)
def block_user(
    email: str,
    payload: BlockUserRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.is_blocked = True
    user.block_reason = payload.reason
    db.commit()
    db.refresh(user)
    return user

from sqlalchemy.orm import joinedload

@router.get(
    "/users/details",
    response_model=List[UserDetailOut],
    summary="Get all Users details (Admin only)",
)
def get_all_users_details(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return db.query(User).options(joinedload(User.bookings)).all()
