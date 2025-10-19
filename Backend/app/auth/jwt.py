import secrets
import hashlib
import uuid
import datetime as dt
import jwt

from app.core.config import settings


def create_access_token(user_id: str, jti: str) -> str:
    """Create a JWT access token."""
    now = dt.datetime.now(dt.timezone.utc)
    payload = {
        "sub": user_id,
        "jti": jti,
        "iat": now,
        "nbf": now,
        "exp": now + dt.timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def new_refresh_token() -> tuple[str, str]:
    """Generate a new secure refresh token."""
    token = secrets.token_urlsafe(32)
    token_hash = hash_token(token)
    return token, token_hash


def create_jti() -> str:
    return str(uuid.uuid4())


def decode_token(token: str) -> dict:
    """Decode a JWT token and return its payload."""
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
