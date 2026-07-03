from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.models.user import User, UserRole
from src.schemas.auth import RegisterRequest, LoginRequest
from src.core.security import hash_password, verify_password, create_access_token


def register_user(db: Session, payload: RegisterRequest) -> User:
    """
    Register a new user.
    - Role is always set to USER (never accepted from client).
    - Email must be unique.
    """
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered."
        )

    new_user = User(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role=UserRole.USER,   # always USER on self-registration
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def login_user(db: Session, payload: LoginRequest) -> dict:
    """
    Authenticate user and return JWT + user details.
    Works for both ADMIN and USER roles via a single endpoint.
    """
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is blocked. Reason: {user.block_reason or 'No reason provided.'}"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact support."
        )

    token = create_access_token({
        "user_id": user.id,
        "email": user.email,
        "role": user.role.value,
        "name": user.name,
    })

    return {"token": token, "user": user}
