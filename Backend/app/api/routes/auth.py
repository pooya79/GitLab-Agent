from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
import httpx
import uuid
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import datetime as dt

from app.api.deps import SessionDep, get_current_user
from app.auth.jwt import create_access_token, new_refresh_token, create_jti, hash_token
from app.auth.gitlab import GitlabAuthService
from app.schemas.auth import RefreshTokenIn, RefreshTokenOut, UserInfo, GitlabAuthUrl
from app.db.models import Users, RefreshSession, OAuthAccount
from app.services.cache_service import CacheService
from app.core.config import settings
from app.core.log import logger
import json

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/refresh", response_model=RefreshTokenOut)
async def refresh_token(rf_in: RefreshTokenIn, session: SessionDep):
    """
    Refresh access and refresh tokens using a valid refresh token.
    """
    # Validate the provided refresh token
    rf_token_hash = hash_token(rf_in.refresh_token)
    result = await session.execute(
        select(RefreshSession, Users)
        .join(Users, RefreshSession.user_id == Users.id)
        .where(
            RefreshSession.refresh_token_hash == rf_token_hash,
            RefreshSession.expires_at
            > dt.datetime.now(dt.timezone.utc).replace(tzinfo=None),
        )
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user_session, user = row

    for _ in range(3):
        try:
            # Delete old session
            await session.delete(user_session)

            # Generate new tokens
            new_rf_token, new_rf_token_hash = new_refresh_token()
            new_jti = create_jti()
            access_token = create_access_token(user_id=str(user.id), jti=new_jti)

            # Create new session
            new_session = RefreshSession(
                user_id=user.id,
                jti=new_jti,
                refresh_token_hash=new_rf_token_hash,
                expires_at=dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
                + dt.timedelta(days=settings.refresh_token_expire_days),
            )
            session.add(new_session)
            await session.commit()
        except IntegrityError:
            await session.rollback()
            continue

        return RefreshTokenOut(
            access_token=access_token,
            refresh_token=new_rf_token,
            expires_in=settings.access_token_expire_minutes * 60,
        )


@router.post("/logout")
async def logout(rf_in: RefreshTokenIn, session: SessionDep):
    """
    Log out the currently authenticated user.
    """
    # Invalidate the user's refresh token
    rf_token_hash = hash_token(rf_in.refresh_token)
    result = await session.execute(
        select(RefreshSession).where(
            RefreshSession.refresh_token_hash == rf_token_hash,
        )
    )
    user_session = result.scalars().first()
    if user_session:
        await session.delete(user_session)
        await session.commit()

    return {"detail": "Logged out successfully"}


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(current_user: Users = Depends(get_current_user)):
    """
    Get information about the currently authenticated user.
    """
    return UserInfo(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        avatar_url=current_user.avatar_url,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
    )


@router.get("/gitlab/login", response_model=GitlabAuthUrl)
async def gitlab_login(request: Request, session: SessionDep):
    """
    Redirect to GitLab for authentication.
    """
    redirect_uri = settings.host_url + "/api/v1/auth/gitlab/callback"
    gitlab_oauth = GitlabAuthService()
    state = gitlab_oauth.new_state()
    code_verifier, code_challenge = gitlab_oauth.new_pkce()

    authorization_url = gitlab_oauth.build_authorize_url(
        redirect_uri=redirect_uri,
        state=state,
        code_challenge=code_challenge,
        scope="api",
    )

    # Save state and code_verifier in cache for later verification
    cache_service = CacheService(session)
    cache_data = json.dumps(
        {"code_verifier": code_verifier, "redirect_uri": redirect_uri}
    )
    await cache_service.set(f"oauth_state:{state}", cache_data, ttl_seconds=600)

    return GitlabAuthUrl(url=authorization_url)


@router.get("/gitlab/callback")
async def gitlab_auth(code: str, state: str, session: SessionDep):
    """
    Handle the callback from GitLab after user authentication.
    """
    logger.info("GitLab callback received")

    if not code or not state:
        logger.error("Missing code or state in GitLab callback")
        raise HTTPException(status_code=400, detail="Missing code or state parameter")

    # Retrieve and validate state and code_verifier from cache
    cache_service = CacheService(session)
    cache_value = await cache_service.get(f"oauth_state:{state}")

    if not cache_value:
        logger.error("Invalid or expired state in GitLab callback")
        raise HTTPException(status_code=400, detail="Invalid or expired state")

    cache_data = json.loads(cache_value)
    code_verifier = cache_data["code_verifier"]
    redirect_uri = cache_data["redirect_uri"]

    # Delete the used cache entry
    await cache_service.delete(f"oauth_state:{state}")

    # Exchange code for token
    gitlab_oauth = GitlabAuthService()
    async with httpx.AsyncClient() as client:
        token_response = await gitlab_oauth.exchange_code_for_token(
            client=client,
            redirect_uri=redirect_uri,
            code=code,
            code_verifier=code_verifier,
        )

        # Get user info from GitLab
        access_token = token_response["access_token"]
        gitlab_user = await gitlab_oauth.get_userinfo(
            client=client, access_token=access_token
        )

    # Find or create user
    result = await session.execute(
        select(Users).where(Users.email == gitlab_user["email"])
    )
    user = result.scalars().first()

    if not user:
        # Create new user
        user = Users(
            email=gitlab_user["email"],
            username=gitlab_user["username"],
            name=gitlab_user.get("name"),
            avatar_url=gitlab_user.get("avatar_url"),
            is_active=True,
            is_superuser=False,
        )
        session.add(user)
        await session.flush()  # Get the user ID

    # Find or create OAuth account
    result = await session.execute(
        select(OAuthAccount).where(
            OAuthAccount.user_id == user.id, OAuthAccount.provider == "gitlab"
        )
    )
    oauth_account = result.scalars().first()

    if oauth_account:
        # Update existing OAuth account
        oauth_account.access_token = access_token
        oauth_account.refresh_token = token_response.get("refresh_token")
        oauth_account.token_type = token_response.get("token_type")
        oauth_account.scope = token_response.get("scope")
        oauth_account.expires_at = (
            dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
            + dt.timedelta(seconds=token_response.get("expires_in", 7200))
            if token_response.get("expires_in")
            else None
        )
        oauth_account.profile_json = gitlab_user
        oauth_account.last_refreshed_at = dt.datetime.now(dt.timezone.utc).replace(
            tzinfo=None
        )
    else:
        # Create new OAuth account
        oauth_account = OAuthAccount(
            user_id=user.id,
            provider="gitlab",
            provider_account_id=str(gitlab_user["id"]),
            access_token=access_token,
            refresh_token=token_response.get("refresh_token"),
            token_type=token_response.get("token_type"),
            scope=token_response.get("scope"),
            expires_at=dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
            + dt.timedelta(seconds=token_response.get("expires_in", 7200))
            if token_response.get("expires_in")
            else None,
            profile_json=gitlab_user,
            last_refreshed_at=dt.datetime.now(dt.timezone.utc).replace(tzinfo=None),
        )
        session.add(oauth_account)

    # Create a session id for the user
    session_id = uuid.uuid4().hex
    cache_service = CacheService(session)
    await cache_service.set(
        f"session_id:{session_id}", str(user.id), ttl_seconds=60 * 5
    )  # only 5 minutes

    # Redirect user to frontend with session id
    frontend_redirect_url = (
        f"{settings.frontend_url}/login/success?session_id={session_id}"
    )
    return RedirectResponse(url=frontend_redirect_url)


@router.get("/token/{session_id}", response_model=RefreshTokenOut)
async def get_access_token(session_id: str, session: SessionDep):
    """
    Fetch access and refresh tokens using session ID.
    """
    # Fetch user ID from cache using session ID
    cache_service = CacheService(session)
    user_id = await cache_service.get(f"session_id:{session_id}")

    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired session ID")

    user_id = int(user_id)

    # Create refresh session for our app
    new_rf_token, new_rf_token_hash = new_refresh_token()
    new_jti = create_jti()
    new_access_token = create_access_token(user_id=str(user_id), jti=new_jti)

    refresh_session = RefreshSession(
        user_id=user_id,
        jti=new_jti,
        refresh_token_hash=new_rf_token_hash,
        expires_at=dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
        + dt.timedelta(days=settings.refresh_token_expire_days),
    )
    session.add(refresh_session)

    await session.commit()

    # Delete the used cache entry
    await cache_service.delete(f"session_id:{session_id}")

    # Return tokens to the client
    return RefreshTokenOut(
        access_token=new_access_token,
        refresh_token=new_rf_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )
