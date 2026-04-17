import os
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from sqlalchemy.pool import NullPool

from src.core.security import get_password_hash
from src.models.user import UserGroup, UserGroupEnum, User
from src.db.database import Base, get_async_session
from src.main import app
from src.models.movie import Certification

load_dotenv()
MAIN_DATABASE_URL = os.getenv("DATABASE_URL")

if "localhost" not in MAIN_DATABASE_URL:
    MAIN_DATABASE_URL = MAIN_DATABASE_URL.replace("@db:", "@localhost:").replace("@postgres:", "@localhost:")

TEST_DATABASE_URL = MAIN_DATABASE_URL.rsplit("/", 1)[0] + "/online_cinema_test"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
TestingSessionLocal = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session")
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(setup_database):
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())

    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_async_session] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def setup_default_group(db_session: AsyncSession):
    query = select(UserGroup).where(UserGroup.name == UserGroupEnum.USER)
    result = await db_session.execute(query)
    existing_group = result.scalar_one_or_none()

    if not existing_group:
        new_group = UserGroup(name=UserGroupEnum.USER)
        db_session.add(new_group)
        await db_session.commit()


@pytest_asyncio.fixture
async def setup_moderator_group(db_session: AsyncSession):
    query = select(UserGroup).where(UserGroup.name == UserGroupEnum.MODERATOR)
    result = await db_session.execute(query)
    existing_group = result.scalar_one_or_none()

    if not existing_group:
        new_group = UserGroup(name=UserGroupEnum.MODERATOR)
        db_session.add(new_group)
        await db_session.commit()


@pytest_asyncio.fixture
async def user_client(client: AsyncClient, setup_default_group):
    user_data = {
        "email": "user@test.com",
        "password": "UserPass123!",
        "is_active": True,
    }

    await client.post("/api/auth/register", json=user_data)

    login_response = await client.post(
        "/api/auth/login",
        data={"username": user_data["email"], "password": user_data["password"]},
    )
    token = login_response.json()["access_token"]

    client.headers = client.headers.copy()
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest_asyncio.fixture
async def moderator_client(client: AsyncClient, setup_moderator_group, db_session: AsyncSession):
    query = select(UserGroup.id).where(UserGroup.name == UserGroupEnum.MODERATOR)
    mod_group_id = await db_session.scalar(query)

    mod_email = "moderator@test.com"
    mod_password = "ModPassword123!"

    user_query = select(User).where(User.email == mod_email)
    existing_mod = await db_session.scalar(user_query)

    if not existing_mod:
        new_mod = User(
            email=mod_email,
            hashed_password=get_password_hash(mod_password),
            group_id=mod_group_id,
            is_active=True,
        )
        db_session.add(new_mod)
        await db_session.commit()

    login_response = await client.post("/api/auth/login", data={"username": mod_email, "password": mod_password})
    token = login_response.json()["access_token"]

    client.headers = client.headers.copy()
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest_asyncio.fixture
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
