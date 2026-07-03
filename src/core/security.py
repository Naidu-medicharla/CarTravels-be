import bcrypt
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from src.core.config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_MINUTES


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a hashed password."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(data: dict) -> str:
    """
    Create a JWT access token.
    data should contain: user_id, email, role
    """
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload.update({"exp": expire})
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Decode and validate a JWT token. Returns payload or None if invalid."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None
