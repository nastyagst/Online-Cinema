from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.api.dependencies import get_current_moderator, get_current_user
from src.db.database import get_async_session
from src.models import User, Movie, OrderItem, Order
from src.models.movie import MovieReview
from src.models.order import OrderStatus
from src.schemas.movie import MovieCreate, MovieRead, MovieUpdate
from src.crud.movie import create_movie, get_movies, get_movie_by_id, delete_movie
from src.crud.movie import update_movie as crud_update_movie

router = APIRouter(prefix="/api/movies", tags=["Movies"])


@router.post(
    "/",
    response_model=MovieRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_moderator)],
)
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
    sort_by: str = Query(
        "id_asc",
        description="Sorting: year_desc, year_asc, imdb_desc, price_asc, price_desc, id_asc",
    ),
    session: AsyncSession = Depends(get_async_session),
):
    movies = await get_movies(
        session=session,
        skip=skip,
        limit=limit,
        search=search,
        genre_id=genre_id,
        year=year,
        sort_by=sort_by,
    )
    return movies


@router.get("/purchased")
async def get_purchased_movies(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Movie)
        .join(OrderItem, Movie.id == OrderItem.movie_id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.user_id == current_user.id, Order.status == OrderStatus.PAID)
        .distinct()
    )

    result = await session.execute(stmt)
    purchased_movies = result.scalars().all()

    return purchased_movies


@router.get("/{movie_id}")
async def read_movie(
        movie_id: int,
        session: AsyncSession = Depends(get_async_session)
):
    stmt = (
        select(
            Movie,
            func.avg(MovieReview.rating).label("avg_rating"),
            func.count(MovieReview.id).label("reviews_count")
        )
        .outerjoin(MovieReview, Movie.id == MovieReview.movie_id)
        .where(Movie.id == movie_id)
        .group_by(Movie.id)
    )

    result = await session.execute(stmt)
    data = result.one_or_none()

    if data is None:
        raise HTTPException(status_code=404, detail="Movie is not found")

    movie, avg_rating, reviews_count = data

    return {
        "id": movie.id,
        "name": movie.name,
        "description": movie.description,
        "year": movie.year,
        "price": movie.price,
        "rating": round(float(avg_rating), 1) if avg_rating else 0.0,
        "reviews_count": reviews_count
    }


@router.put(
    "/{movie_id}",
    response_model=MovieRead,
    dependencies=[Depends(get_current_moderator)],
)
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


@router.delete(
    "/{movie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_current_moderator)],
)
async def delete_movie_endpoint(
    movie_id: int, session: AsyncSession = Depends(get_async_session)
):
    movie = await get_movie_by_id(session, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie is not found")
    await delete_movie(session, movie)
