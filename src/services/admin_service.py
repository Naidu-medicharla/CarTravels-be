from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.models.user import User, UserRole
from src.schemas.admin import CreateAdminRequest
from src.core.security import hash_password


def create_admin_user(db: Session, payload: CreateAdminRequest) -> User:
    """
    Creates a new ADMIN user.
    Only callable internally — router guards this with require_admin dependency.
    """
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered."
        )

    new_admin = User(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role=UserRole.ADMIN,   # forced to ADMIN regardless of input
        is_active=True,
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    return new_admin
