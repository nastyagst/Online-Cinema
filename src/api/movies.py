from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.db.database import get_async_session
from src.schemas.movie import MovieCreate, MovieRead, MovieUpdate
from src.crud.movie import create_movie, get_movies, get_movie_by_id, delete_movie
from src.crud.movie import update_movie as crud_update_movie

router = APIRouter(prefix="/api/movies", tags=["Movies"])


@router.post("/", response_model=MovieRead, status_code=status.HTTP_201_CREATED)
async def add_movie(
    movie_in: MovieCreate, session: AsyncSession = Depends(get_async_session)
):
    new_movie = await create_movie(session, movie_in)
    return new_movie


@router.get("/", response_model=List[MovieRead])
async def read_movies(
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = Query(None, description="Search by title"),
    genre_id: Optional[int] = Query(None, description="Filter by genre ID"),
    year: Optional[int] = Query(None, description="Filter by release year"),
    sort_by: str = Query("id_asc", description="Sorting: year_desc, year_asc, imdb_desc, price_asc, price_desc, id_asc"),
    session: AsyncSession = Depends(get_async_session)
):
    movies = await get_movies(
        session=session,
        skip=skip,
        limit=limit,
        search=search,
        genre_id=genre_id,
        year=year,
        sort_by=sort_by
    )
    return movies


@router.get("/{movie_id}", response_model=MovieRead)
async def read_movie(movie_id: int, session: AsyncSession = Depends(get_async_session)):
    movie = await get_movie_by_id(session, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie is not found")
    return movie


@router.put("/{movie_id}", response_model=MovieRead)
async def update_movie_endpoint(
    movie_id: int,
    movie_in: MovieUpdate,
    session: AsyncSession = Depends(get_async_session),
):
    movie = await get_movie_by_id(session, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie is not found")
    updated_movie = await crud_update_movie(session, movie, movie_in)
    return updated_movie


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie_endpoint(
    movie_id: int, session: AsyncSession = Depends(get_async_session)
):
    movie = await get_movie_by_id(session, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie is not found")
    await delete_movie(session, movie)
