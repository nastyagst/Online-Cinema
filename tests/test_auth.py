import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user import UserGroup, UserGroupEnum


@pytest.fixture
async def setup_default_group(db_session: AsyncSession):
    query = select(UserGroup).where(UserGroup.name == UserGroupEnum.USER)
    result = await db_session.execute(query)
    existing_group = result.scalar_one_or_none()

    if not existing_group:
        new_group = UserGroup(name=UserGroupEnum.USER)
        db_session.add(new_group)
        await db_session.commit()


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient, setup_default_group):
    user_data = {
        "email": "testuser@gmail.com",
        "password": "StrongPassword123!",
        "is_active": True,
    }

    response = await client.post("/api/auth/register", json=user_data)

    assert response.status_code in [200, 201]

    data = response.json()
    assert data["email"] == user_data["email"]
    assert "password" not in data


@pytest.mark.asyncio
async def test_login_user(client: AsyncClient, setup_default_group):
    user_email = "login_test@gmail.com"
    user_password = "SuperSecretPassword1!"

    await client.post(
        "/api/auth/register",
        json={
            "email": user_email,
            "password": user_password,
            "is_active": True,
        },
    )

    login_data = {"username": user_email, "password": user_password}

    response = await client.post("/api/auth/login", data=login_data)
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_user_wrong_password(client: AsyncClient, setup_default_group):
    login_data = {"username": "login_test@gmail.com", "password": "WrongPassword!"}

    response = await client.post("/api/auth/login", data=login_data)

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"
