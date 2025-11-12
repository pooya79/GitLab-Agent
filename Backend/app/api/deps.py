import datetime as dt
import httpx
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import gitlab

from app.db.database import AsyncSessionLocal
from app.auth.jwt import decode_token
from app.db.models import Users, RefreshSession, OAuthAccount
from app.auth.gitlab import GitlabAuthService
from app.core.config import settings
from app.core.log import logger


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
        ).replace(tzinfo=None):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or revoked",
            )
    except Exception as e:
        logger.info(f"Error decoding token: {e}")
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


async def get_gitlab_client(
    session: SessionDep,
    current_user: Users = Depends(get_current_user),
) -> gitlab.Gitlab:
    """
    Dependency to get the GitLab client for the current user.
    Usage: async def endpoint(gitlab_client: gitlab.Gitlab = Depends(get_gitlab_client))
    """
    result = await session.execute(
        select(OAuthAccount).where(
            OAuthAccount.user_id == current_user.id,
            OAuthAccount.provider == "gitlab",
        )
    )
    oauth_account = result.scalar_one_or_none()
    if oauth_account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GitLab OAuth account not found",
        )

    # Check if the token is expired
    if oauth_account.expires_at and oauth_account.expires_at <= dt.datetime.now(
        dt.timezone.utc
    ).replace(tzinfo=None):
        # Refresh the token logic should be implemented here
        async with httpx.AsyncClient() as client:
            try:
                gitlab_oauth = GitlabAuthService()
                token_response = await gitlab_oauth.refresh_token(
                    client=client,
                    refresh_token=oauth_account.refresh_token,
                )
                oauth_account.access_token = token_response["access_token"]
                oauth_account.refresh_token = token_response.get(
                    "refresh_token", oauth_account.refresh_token
                )
                oauth_account.token_type = token_response.get(
                    "token_type", oauth_account.token_type
                )
                oauth_account.scope = token_response.get("scope", oauth_account.scope)
                expires_in = token_response.get("expires_in")
                if expires_in:
                    oauth_account.expires_at = dt.datetime.now(dt.timezone.utc).replace(
                        tzinfo=None
                    ) + dt.timedelta(seconds=expires_in)
                oauth_account.last_refreshed_at = dt.datetime.now(
                    dt.timezone.utc
                ).replace(tzinfo=None)
                await session.commit()
            except Exception:
                await session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to refresh GitLab OAuth token",
                )

    return gitlab.Gitlab(settings.gitlab.base, oauth_token=oauth_account.access_token)
