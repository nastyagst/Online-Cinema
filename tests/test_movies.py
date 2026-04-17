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
def movie_data(setup_certification):
    return {
        "name": "The Matrix",
        "year": 1999,
        "time": 136,
        "imdb": 8.7,
        "votes": 1900000,
        "meta_score": 73.0,
        "gross": 460000000.0,
        "description": "A computer hacker learns from mysterious rebels about the true nature of his reality.",
        "price": 9.99,
        "certification_id": setup_certification.id,
        "genre_ids": [],
        "director_ids": [],
        "star_ids": [],
    }


@pytest.mark.asyncio
async def test_add_movie_as_moderator(moderator_client: AsyncClient, movie_data: dict):
    response = await moderator_client.post("/api/movies/", json=movie_data)

    if response.status_code != 201:
        print(f"\nERROR: {response.json()}\n")

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == movie_data["name"]
    assert "id" in data


@pytest.mark.asyncio
async def test_add_movie_as_user_forbidden(user_client: AsyncClient, movie_data: dict):
    response = await user_client.post("/api/movies/", json=movie_data)
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_read_movies(client: AsyncClient, moderator_client: AsyncClient, movie_data: dict):
    await moderator_client.post("/api/movies/", json=movie_data)

    response = await client.get("/api/movies/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.asyncio
async def test_read_single_movie(client: AsyncClient, moderator_client: AsyncClient, movie_data: dict):
    create_resp = await moderator_client.post("/api/movies/", json=movie_data)
    movie_id = create_resp.json()["id"]

    response = await client.get(f"/api/movies/{movie_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == movie_id


@pytest.mark.asyncio
async def test_update_movie(moderator_client: AsyncClient, movie_data: dict):
    create_resp = await moderator_client.post("/api/movies/", json=movie_data)
    movie_id = create_resp.json()["id"]

    update_data = movie_data.copy()
    update_data["name"] = "The Matrix Reloaded"
    update_data["year"] = 2003

    response = await moderator_client.put(f"/api/movies/{movie_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["name"] == "The Matrix Reloaded"


@pytest.mark.asyncio
async def test_delete_movie(moderator_client: AsyncClient, movie_data: dict):
    create_resp = await moderator_client.post("/api/movies/", json=movie_data)
    movie_id = create_resp.json()["id"]

    delete_resp = await moderator_client.delete(f"/api/movies/{movie_id}")
    assert delete_resp.status_code == 204

    get_resp = await moderator_client.get(f"/api/movies/{movie_id}")
    assert get_resp.status_code == 404
