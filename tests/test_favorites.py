import pytest
from httpx import AsyncClient


@pytest.fixture
async def created_movie(moderator_client: AsyncClient, setup_certification):
    movie_data = {
        "name": "Favorite Movie",
        "year": 2024,
        "time": 120,
        "imdb": 8.0,
        "votes": 1000,
        "description": "Test favorite",
        "price": 5.99,
        "certification_id": setup_certification.id,
        "genre_ids": [],
        "director_ids": [],
        "star_ids": [],
    }
    resp = await moderator_client.post("/api/movies/", json=movie_data)
    return resp.json()


@pytest.mark.asyncio
async def test_add_to_favorites(user_client: AsyncClient, created_movie: dict):
    response = await user_client.post(f"/api/favorites/{created_movie['id']}")
    assert response.status_code == 201
    assert response.json()["message"] == "Movie added to favorites"


@pytest.mark.asyncio
async def test_add_duplicate_favorite(user_client: AsyncClient, created_movie: dict):
    await user_client.post(f"/api/favorites/{created_movie['id']}")
    response = await user_client.post(f"/api/favorites/{created_movie['id']}")
    assert response.status_code == 400
    assert response.json()["detail"] == "Movie already in favorites"


@pytest.mark.asyncio
async def test_get_my_favorites(user_client: AsyncClient, created_movie: dict):
    await user_client.post(f"/api/favorites/{created_movie['id']}")
    response = await user_client.get("/api/favorites/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["movie"]["id"] == created_movie["id"]


@pytest.mark.asyncio
async def test_remove_from_favorites(user_client: AsyncClient, created_movie: dict):
    await user_client.post(f"/api/favorites/{created_movie['id']}")
    response = await user_client.delete(f"/api/favorites/{created_movie['id']}")
    assert response.status_code == 200
    assert response.json()["message"] == "Movie removed from favorites"
    get_resp = await user_client.get("/api/favorites/")
    assert len(get_resp.json()) == 0


@pytest.mark.asyncio
async def test_remove_nonexistent_favorite(user_client: AsyncClient):
    response = await user_client.delete("/api/favorites/99999")
    assert response.status_code == 404
