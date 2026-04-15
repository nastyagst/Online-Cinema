import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.movie import Certification


@pytest.fixture
async def setup_certification(db_session: AsyncSession):
    from sqlalchemy import select

    query = select(Certification).where(Certification.name == "PG-13")
    result = await db_session.execute(query)
    cert = result.scalar_one_or_none()

    if not cert:
        cert = Certification(name="PG-13")
        db_session.add(cert)
        await db_session.commit()
        await db_session.refresh(cert)

    return cert


@pytest.fixture
async def created_movie(moderator_client: AsyncClient, setup_certification):
    movie_data = {
        "name": "Cart Test Movie",
        "year": 2024,
        "time": 120,
        "imdb": 8.5,
        "votes": 5000,
        "description": "A movie to test the cart functionality.",
        "price": 14.99,
        "certification_id": setup_certification.id,
        "genre_ids": [],
        "director_ids": [],
        "star_ids": [],
    }
    response = await moderator_client.post("/api/movies/", json=movie_data)
    return response.json()


@pytest.mark.asyncio
async def test_get_empty_cart(user_client: AsyncClient):
    response = await user_client.get("/api/cart/")

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []


@pytest.mark.asyncio
async def test_add_to_cart(user_client: AsyncClient, created_movie: dict):
    payload = {"movie_id": created_movie["id"]}

    response = await user_client.post("/api/cart/add", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["movie"]["id"] == created_movie["id"]


@pytest.mark.asyncio
async def test_add_duplicate_to_cart(user_client: AsyncClient, created_movie: dict):
    payload = {"movie_id": created_movie["id"]}

    await user_client.post("/api/cart/add", json=payload)

    response = await user_client.post("/api/cart/add", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "This movie is already in your cart."


@pytest.mark.asyncio
async def test_remove_from_cart(user_client: AsyncClient, created_movie: dict):
    payload = {"movie_id": created_movie["id"]}
    add_resp = await user_client.post("/api/cart/add", json=payload)

    item_id = add_resp.json()["items"][0]["id"]

    del_resp = await user_client.delete(f"/api/cart/items/{item_id}")
    assert del_resp.status_code == 204

    get_resp = await user_client.get("/api/cart/")
    assert len(get_resp.json()["items"]) == 0


@pytest.mark.asyncio
async def test_remove_nonexistent_item(user_client: AsyncClient):
    response = await user_client.delete("/api/cart/items/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "The movie was not found in your cart."
