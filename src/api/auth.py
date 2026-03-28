from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_async_session
from src.core.security import REFRESH_TOKEN_EXPIRE_DAYS
from datetime import timedelta, datetime, timezone
from src.models.user import User, UserGroup, UserGroupEnum, UserProfile, RefreshToken
from src.schemas.user import UserCreate, UserRead, UserLogin, Token
from src.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
)

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
            detail="The user with this email already exists in the system.",
        )
    group_query = select(UserGroup).where(UserGroup.name == UserGroupEnum.USER)
    group_result = await session.execute(group_query)
    group = group_result.scalar_one_or_none()

    if not group:
        group = UserGroup(name=UserGroupEnum.USER)
        session.add(group)
        await session.commit()
        await session.refresh(group)

    hashed_pass = get_password_hash(user_in.password)

    new_user = User(email=user_in.email, hashed_password=hashed_pass, group_id=group.id)
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    new_profile = UserProfile(user_id=new_user.id)
    session.add(new_profile)
    await session.refresh(new_user)
    await session.refresh(new_profile)
    new_user.profile = new_profile
    # TODO: ActivationToken, send an email via celery
    return new_user


@router.post("/login", response_model=Token)
async def login_user(
    user_in: UserLogin, session: AsyncSession = Depends(get_async_session)
):
    query = select(User).where(User.email == user_in.email)
    result = await session.execute(query)
    user = result.scalar_one_or_none()

    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
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
