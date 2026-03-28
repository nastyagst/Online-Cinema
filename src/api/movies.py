from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.db.database import get_async_session
from src.schemas.movie import MovieCreate, MovieRead
from src.crud.movie import create_movie, get_movies

router = APIRouter(prefix="/api/movies", tags=["Movies"])


@router.post("/", response_model=MovieRead, status_code=status.HTTP_201_CREATED)
async def add_movie(
    movie_in: MovieCreate, session: AsyncSession = Depends(get_async_session)
):
    new_movie = await create_movie(session, movie_in)
    return new_movie


@router.get("/", response_model=List[MovieRead])
async def read_movies(
    skip: int = 0, limit: int = 10, session: AsyncSession = Depends(get_async_session)
):
    movies = await get_movies(session, skip=skip, limit=limit)
    return movies
