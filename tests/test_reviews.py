import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import UserGroup, UserGroupEnum, User
from src.core.security import get_password_hash
from sqlalchemy import select


@pytest.fixture
async def created_movie(moderator_client: AsyncClient, setup_certification):
    movie_data = {
        "name": "Review Movie",
        "year": 2024,
        "time": 120,
        "imdb": 7.0,
        "votes": 500,
        "description": "Test review",
        "price": 4.99,
        "certification_id": setup_certification.id,
        "genre_ids": [],
        "director_ids": [],
        "star_ids": [],
    }
    resp = await moderator_client.post("/api/movies/", json=movie_data)
    return resp.json()


@pytest.mark.asyncio
async def test_create_review(user_client: AsyncClient, created_movie: dict):
    payload = {"rating": 9, "text": "Great movie!"}
    response = await user_client.post(f"/api/movies/{created_movie['id']}/reviews/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["rating"] == 9
    assert data["text"] == "Great movie!"


@pytest.mark.asyncio
async def test_create_duplicate_review(user_client: AsyncClient, created_movie: dict):
    payload = {"rating": 8, "text": "Good"}
    await user_client.post(f"/api/movies/{created_movie['id']}/reviews/", json=payload)
    response = await user_client.post(f"/api/movies/{created_movie['id']}/reviews/", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "You already reviewed this movie"


@pytest.mark.asyncio
async def test_get_movie_reviews(user_client: AsyncClient, created_movie: dict):
    payload = {"rating": 10, "text": "Masterpiece"}
    await user_client.post(f"/api/movies/{created_movie['id']}/reviews/", json=payload)

    response = await user_client.get(f"/api/movies/{created_movie['id']}/reviews/")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["rating"] == 10
    assert "user_id" in data[0]
    assert isinstance(data[0]["user_id"], int)


@pytest.mark.asyncio
async def test_delete_my_review(user_client: AsyncClient, created_movie: dict):
    payload = {"rating": 5, "text": "Average"}
    create_resp = await user_client.post(f"/api/movies/{created_movie['id']}/reviews/", json=payload)
    review_id = create_resp.json()["id"]
    del_resp = await user_client.delete(f"/api/movies/{created_movie['id']}/reviews/{review_id}")
    assert del_resp.status_code == 204
    get_resp = await user_client.get(f"/api/movies/{created_movie['id']}/reviews/")
    assert len(get_resp.json()) == 0


@pytest.mark.asyncio
async def test_delete_other_user_review(
    moderator_client: AsyncClient,
    db_session: AsyncSession,
    created_movie: dict,
    setup_default_group,
):
    payload = {"rating": 2, "text": "Bad"}
    create_resp = await moderator_client.post(f"/api/movies/{created_movie['id']}/reviews/", json=payload)
    review_id = create_resp.json()["id"]

    query = select(UserGroup.id).where(UserGroup.name == UserGroupEnum.USER)
    user_group_id = await db_session.scalar(query)

    import uuid

    hacker_email = f"hacker_{uuid.uuid4().hex[:6]}@test.com"
    hacker_pass = "Hack123!"
    hacker = User(
        email=hacker_email,
        hashed_password=get_password_hash(hacker_pass),
        group_id=user_group_id,
        is_active=True,
    )
    db_session.add(hacker)
    await db_session.commit()

    moderator_client.headers.clear()
    login_resp = await moderator_client.post(
        "/api/auth/login", data={"username": hacker_email, "password": hacker_pass}
    )
    hacker_token = login_resp.json()["access_token"]

    moderator_client.headers = {"Authorization": f"Bearer {hacker_token}"}
    del_resp = await moderator_client.delete(f"/api/movies/{created_movie['id']}/reviews/{review_id}")

    assert del_resp.status_code == 403
    assert del_resp.json()["detail"] == "You can only delete your own reviews"
