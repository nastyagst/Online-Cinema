from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import joinedload

from src.db.database import get_async_session
from src.models.movie import Movie, FavoriteMovie
from src.models.user import User
from src.api.dependencies import get_current_user
from src.schemas.movie import FavoriteMovieRead

router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.post("/{movie_id}", status_code=status.HTTP_201_CREATED)
async def add_to_favorites(
    movie_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    movie = await session.get(Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    stmt = select(FavoriteMovie).where(
        FavoriteMovie.user_id == current_user.id, FavoriteMovie.movie_id == movie_id
    )
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Movie already in favorites")

    new_favorite = FavoriteMovie(user_id=current_user.id, movie_id=movie_id)
    session.add(new_favorite)
    await session.commit()

    return {"message": "Movie added to favorites"}


@router.delete("/{movie.id}")
async def remove_from_favorites(
    movie_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    stmt = delete(FavoriteMovie).where(
        FavoriteMovie.user_id == current_user.id, FavoriteMovie.movie_id == movie_id
    )
    result = await session.execute(stmt)

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Movie not found in favorites")

    await session.commit()
    return {"message": "Movie removed from favorites"}


@router.get("/", response_model=list[FavoriteMovieRead])
async def get_my_favorites(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(FavoriteMovie)
        .options(joinedload(FavoriteMovie.movie))
        .where(FavoriteMovie.user_id == current_user.id)
    )
    result = await session.execute(stmt)
    favorites = result.scalars().all()

    return favorites
