from typing import Optional
from sqlalchemy import select, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from src.models.movie import Movie, Genre, Director, Star
from src.schemas.movie import MovieCreate, MovieUpdate


async def get_movies(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    genre_id: Optional[int] = None,
    year: Optional[int] = None,
    sort_by: str = "id_asc",
):
    stmt = select(Movie).options(
        joinedload(Movie.certification),
        joinedload(Movie.genres),
        joinedload(Movie.directors),
        joinedload(Movie.stars),
    )
    if search:
        stmt = stmt.where(Movie.name.ilike(f"%{search}%"))
    if year:
        stmt = stmt.where(Movie.year == year)
    if genre_id:
        stmt = stmt.where(Movie.genres.any(Genre.id == genre_id))

    if sort_by == "year_desc":
        stmt = stmt.order_by(desc(Movie.year))
    elif sort_by == "year_asc":
        stmt = stmt.order_by(asc(Movie.year))
    elif sort_by == "imdb_desc":
        stmt = stmt.order_by(desc(Movie.imdb))
    elif sort_by == "imdb_asc":
        stmt = stmt.order_by(asc(Movie.imdb))
    elif sort_by == "price_desc":
        stmt = stmt.order_by(desc(Movie.price))
    elif sort_by == "price_asc":
        stmt = stmt.order_by(asc(Movie.price))
    else:
        stmt = stmt.order_by(asc(Movie.id))

    stmt = stmt.offset(skip).limit(limit)
    result = await session.execute(stmt)
    return result.unique().scalars().all()


async def get_movie_by_id(session: AsyncSession, movie_id: int) -> Optional[Movie]:
    stmt = (
        select(Movie)
        .options(
            joinedload(Movie.certification),
            joinedload(Movie.genres),
            joinedload(Movie.directors),
            joinedload(Movie.stars),
        )
        .where(Movie.id == movie_id)
    )
    result = await session.execute(stmt)
    return result.unique().scalar_one_or_none()


async def create_movie(session: AsyncSession, movie_in: MovieCreate) -> Movie:
    movie_data = movie_in.model_dump(exclude={"genre_ids", "director_ids", "star_ids"})
    db_movie = Movie(**movie_data)

    if movie_in.genre_ids:
        genres_stmt = select(Genre).where(Genre.id.in_(movie_in.genre_ids))
        genres_result = await session.execute(genres_stmt)
        db_movie.genres = list(genres_result.scalars().all())

    if movie_in.director_ids:
        directors_stmt = select(Director).where(Director.id.in_(movie_in.director_ids))
        directors_result = await session.execute(directors_stmt)
        db_movie.directors = list(directors_result.scalars().all())

    if movie_in.star_ids:
        stars_stmt = select(Star).where(Star.id.in_(movie_in.star_ids))
        stars_result = await session.execute(stars_stmt)
        db_movie.stars = list(stars_result.scalars().all())

    session.add(db_movie)
    await session.commit()
    await session.refresh(db_movie)
    return await get_movie_by_id(session, db_movie.id)


async def update_movie(
    session: AsyncSession, db_movie: Movie, movie_in: MovieUpdate
) -> Movie:
    update_data = movie_in.model_dump(
        exclude_unset=True, exclude={"genre_ids", "director_ids", "star_ids"}
    )
    for field, value in update_data.items():
        setattr(db_movie, field, value)

    if movie_in.genre_ids is not None:
        genres_stmt = select(Genre).where(Genre.id.in_(movie_in.genre_ids))
        genres_result = await session.execute(genres_stmt)
        db_movie.genres = list(genres_result.scalars().all())

    if movie_in.director_ids is not None:
        directors_stmt = select(Director).where(Director.id.in_(movie_in.director_ids))
        directors_result = await session.execute(directors_stmt)
        db_movie.directors = list(directors_result.scalars().all())

    if movie_in.star_ids is not None:
        stars_stmt = select(Star).where(Star.id.in_(movie_in.star_ids))
        stars_result = await session.execute(stars_stmt)
        db_movie.stars = list(stars_result.scalars().all())

    session.add(db_movie)
    await session.commit()
    await session.refresh(db_movie)
    return await get_movie_by_id(session, db_movie.id)


async def delete_movie(session: AsyncSession, db_movie: Movie) -> None:
    await session.delete(db_movie)
    await session.commit()
