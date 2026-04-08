from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta, datetime, timezone

from src.db.database import get_async_session
from src.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from src.models.user import User, UserGroup, UserGroupEnum, UserProfile, RefreshToken
from src.schemas.user import UserCreate, UserRead, Token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate, session: AsyncSession = Depends(get_async_session)
):
    query = select(User).where(User.email == user_in.email)
    result = await session.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    group_query = select(UserGroup).where(UserGroup.name == UserGroupEnum.USER)
    group_res = await session.execute(group_query)
    user_group = group_res.scalar_one_or_none()

    if not user_group:
        raise HTTPException(status_code=500, detail="Default user group not found")

    new_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        group_id=user_group.id,
        is_active=True,
    )
    session.add(new_user)
    await session.flush()

    new_profile = UserProfile(user_id=new_user.id)
    session.add(new_profile)
    await session.commit()

    final_query = await session.execute(
        select(User)
        .options(selectinload(User.group), selectinload(User.profile))
        .where(User.id == new_user.id)
    )
    return final_query.scalar_one()


@router.post("/login", response_model=Token)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_async_session),
):
    query = (
        select(User)
        .options(selectinload(User.group))
        .where(User.email == form_data.username)
    )
    result = await session.execute(query)
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    db_refresh_token = RefreshToken(
        user_id=user.id, token=refresh_token, expires_at=expires_at
    )
    session.add(db_refresh_token)
    await session.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
