import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy import select
from src.models.user import User, UserGroup, UserGroupEnum
from src.core.security import get_password_hash


async def create_test_user(db_session, email, password, group_name):
    query = select(UserGroup.id).where(UserGroup.name == group_name)
    group_id = await db_session.scalar(query)
    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        group_id=group_id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    return user


async def get_token(client, email, password):
    resp = await client.post(
        "/api/auth/login", data={"username": email, "password": password}
    )
    return resp.json()["access_token"]


@pytest.fixture
async def setup_data(
    client: AsyncClient,
    db_session,
    setup_default_group,
    setup_moderator_group,
    setup_certification,
):
    mod_email, user_email, password = (
        f"m_{uuid.uuid4().hex[:4]}@t.com",
        f"u_{uuid.uuid4().hex[:4]}@t.com",
        "Pass123!",
    )
    await create_test_user(db_session, mod_email, password, UserGroupEnum.MODERATOR)
    await create_test_user(db_session, user_email, password, UserGroupEnum.USER)

    mod_token = await get_token(client, mod_email, password)
    user_token = await get_token(client, user_email, password)

    movie_data = {
        "name": "Order Movie",
        "year": 2024,
        "time": 100,
        "imdb": 8.0,
        "votes": 100,
        "description": "Test",
        "price": 10.0,
        "certification_id": setup_certification.id,
        "genre_ids": [],
        "director_ids": [],
        "star_ids": [],
    }
    m_resp = await client.post(
        "/api/movies/",
        json=movie_data,
        headers={"Authorization": f"Bearer {mod_token}"},
    )
    movie = m_resp.json()

    await client.post(
        "/api/cart/add",
        json={"movie_id": movie["id"]},
        headers={"Authorization": f"Bearer {user_token}"},
    )

    return {"user_token": user_token, "mod_token": mod_token, "movie": movie}


@pytest.mark.asyncio
async def test_place_order(client: AsyncClient, setup_data: dict):
    resp = await client.post(
        "/api/orders/", headers={"Authorization": f"Bearer {setup_data['user_token']}"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"


@pytest.mark.asyncio
async def test_place_order_empty_cart(
    client: AsyncClient, db_session, setup_default_group
):
    email, password = f"empty_{uuid.uuid4().hex[:4]}@t.com", "Pass123!"
    await create_test_user(db_session, email, password, UserGroupEnum.USER)
    token = await get_token(client, email, password)

    resp = await client.post(
        "/api/orders/", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_get_my_orders(client: AsyncClient, setup_data: dict):
    token = {"Authorization": f"Bearer {setup_data['user_token']}"}
    await client.post("/api/orders/", headers=token)
    resp = await client.get("/api/orders/my_orders", headers=token)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_get_all_orders_moderator(client: AsyncClient, setup_data: dict):
    await client.post(
        "/api/orders/", headers={"Authorization": f"Bearer {setup_data['user_token']}"}
    )
    resp = await client.get(
        "/api/orders/all",
        headers={"Authorization": f"Bearer {setup_data['mod_token']}"},
    )
    assert resp.status_code == 200
