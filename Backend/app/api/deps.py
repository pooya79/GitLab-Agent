from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.user_crud import get_user_by_identifier
from app.core.security import decode_token
from app.db.database import AsyncSessionLocal

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/user/login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async DB session dependency.
    Usage: async def endpoint(db: AsyncSession = Depends(get_db))
    """
    async with AsyncSessionLocal() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    db: SessionDep,
    token: str = Depends(oauth2_scheme),
):
    creds_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
    except Exception:
        raise creds_exc

    user = await get_user_by_identifier(db, payload.sub)
    if not user:
        raise creds_exc
    return user
