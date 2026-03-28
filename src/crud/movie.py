from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.models.movie import Movie, Genre, Director, Star
from src.schemas.movie import MovieCreate


async def create_movie(session: AsyncSession, movie_in: MovieCreate) -> Movie:
    movie_data = movie_in.model_dump(exclude={"genre_ids", "director_ids", "star_ids"})
    new_movie = Movie(**movie_data)

    if movie_in.genre_ids:
        genres_stmt = select(Genre).where(Genre.id.in_(movie_in.genre_ids))
        genres_result = await session.execute(genres_stmt)
        new_movie.genres = list(genres_result.scalars().all())

    if movie_in.director_ids:
        directors_stmt = select(Director).where(Director.id.in_(movie_in.director_ids))
        directors_result = await session.execute(directors_stmt)
        new_movie.directors = list(directors_result.scalars().all())

    if movie_in.star_ids:
        star_stmt = select(Star).where(Star.id.in_(movie_in.star_ids))
        stars_result = await session.execute(star_stmt)
        new_movie.stars = list(stars_result.scalars().all())

    session.add(new_movie)
    await session.commit()

    stmt = (
        select(Movie)
        .options(
            joinedload(Movie.certification),
            joinedload(Movie.genres),
            joinedload(Movie.directors),
            joinedload(Movie.stars),
        )
        .where(Movie.id == new_movie.id)
    )
    result = await session.execute(stmt)
    return result.unique().scalar_one()


async def get_movies(
    session: AsyncSession, skip: int = 0, limit: int = 10
) -> list[Movie]:
    stmt = (
        select(Movie)
        .options(
            joinedload(Movie.certification),
            joinedload(Movie.genres),
            joinedload(Movie.directors),
            joinedload(Movie.stars),
        )
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.unique().scalars().all())
