from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.core.security import decode_access_token
from src.models.user import User

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Extracts and validates the JWT from the Authorization header.
    Returns the authenticated User ORM object.
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == payload.get("user_id")).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated.",
        )
        
    if user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is blocked. Reason: {user.block_reason or 'No reason provided.'}"
        )

    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Guard: only allows ADMIN role to proceed.
    Raises 403 Forbidden for any other role.
    """
    if current_user.role.value != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admins only.",
        )
    return current_user

bearer_scheme_optional = HTTPBearer(auto_error=False)

def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme_optional),
    db: Session = Depends(get_db),
) -> User | None:
    if not credentials:
        return None
    try:
        return get_current_user(credentials, db)
    except HTTPException:
        return None
