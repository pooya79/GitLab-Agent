import datetime as dt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.auth.jwt import decode_token
from app.db.models import Users, RefreshSession


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async DB session dependency.
    Usage: async def endpoint(db: AsyncSession = Depends(get_db))
    """
    async with AsyncSessionLocal() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_db)]

security = HTTPBearer(auto_error=True)


async def get_current_user(
    session: SessionDep,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Dependency to get the current user based on the provided JWT token.
    Usage: async def endpoint(current_user: Users = Depends(get_current_user))
    """
    token = credentials.credentials
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )

        jti: str = payload.get("jti")
        if not jti:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing token identifier",
            )

        # Verify jti exists and is not revoked
        result = await session.execute(
            select(RefreshSession).where(RefreshSession.jti == jti)
        )
        session_entry = result.scalar_one_or_none()
        if not session_entry or session_entry.expires_at <= dt.datetime.now(
            dt.timezone.utc
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or revoked",
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    result = await session.execute(select(Users).where(Users.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user
