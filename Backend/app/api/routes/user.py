from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.db.models import User
from app.api.deps import SessionDep, get_current_user
from app.api.user_crud import get_user_by_identifier
from app.schemas.user import UserRead, UserUpdate
from app.schemas.token import Token
from app.core.security import verify_password, create_access_token, hash_password

router = APIRouter(prefix="/user", tags=["user"])


@router.post("/login", response_model=Token)
async def login_for_token(
    session: SessionDep,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    identifier = form_data.username

    user = await get_user_by_identifier(
        session,
        identifier=identifier,
    )
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(user.username, user.email)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserRead)
async def read_me(current_user=Depends(get_current_user)):
    return current_user


@router.put("/edit", response_model=UserRead)
async def edit_profile(
    user_update: UserUpdate,
    session: SessionDep,
    current_user: User = Depends(get_current_user),
):
    if user_update.email:
        current_user.email = user_update.email

    if user_update.username:
        current_user.username = user_update.username

    if user_update.password:
        current_user.hashed_password = hash_password(user_update.password)

    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    return current_user
