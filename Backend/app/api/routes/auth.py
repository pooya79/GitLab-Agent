from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import datetime as dt

from app.api.deps import SessionDep, get_current_user
from app.auth.jwt import create_access_token, new_refresh_token, create_jti
from app.schemas.auth import RefreshTokenIn, RefreshTokenOut, hash_token, UserInfo
from app.db.models import Users, UserSessions
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/refresh", response_model=RefreshTokenOut)
async def refresh_token(rf_in: RefreshTokenIn, session: SessionDep):
    """
    Refresh access and refresh tokens using a valid refresh token.
    """
    # Validate the provided refresh token
    rf_token_hash = hash_token(rf_in.refresh_token)
    result = await session.execute(
        select(UserSessions, Users)
        .join(Users, UserSessions.user_id == Users.id)
        .where(
            UserSessions.refresh_token_hash == rf_token_hash,
            UserSessions.expires_at > dt.datetime.now(dt.timezone.utc),
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
            new_session = UserSessions(
                user_id=user.id,
                jti=new_jti,
                refresh_token_hash=new_rf_token_hash,
                expires_at=dt.datetime.now(dt.timezone.utc)
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
        select(UserSessions).where(
            UserSessions.refresh_token_hash == rf_token_hash,
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
