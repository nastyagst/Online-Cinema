import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user import UserGroup, UserGroupEnum


@pytest.fixture
async def setup_default_group(db_session: AsyncSession):
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
