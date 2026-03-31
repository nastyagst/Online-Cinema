from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.database import get_async_session
from src.schemas.movie import GenreRead, StarRead, DirectorRead, CertificationRead
from src.crud import metadata
from pydantic import BaseModel

router = APIRouter(prefix="/api/metadata", tags=["Metadata"])


class NameSchema(BaseModel):
    name: str


@router.post("/genres", response_model=GenreRead, status_code=status.HTTP_201_CREATED)
async def add_genre(
    data: NameSchema, session: AsyncSession = Depends(get_async_session)
):
    return await metadata.create_genre(session, data.name)


@router.post("/stars", response_model=StarRead, status_code=status.HTTP_201_CREATED)
async def add_star(
    data: NameSchema, session: AsyncSession = Depends(get_async_session)
):
    return await metadata.create_star(session, data.name)


@router.post(
    "/directors", response_model=DirectorRead, status_code=status.HTTP_201_CREATED
)
async def add_director(
    data: NameSchema, session: AsyncSession = Depends(get_async_session)
):
    return await metadata.create_director(session, data.name)


@router.post(
    "/certifications",
    response_model=CertificationRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_certification(
    data: NameSchema, session: AsyncSession = Depends(get_async_session)
):
    return await metadata.create_certification(session, data.name)
