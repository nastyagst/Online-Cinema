from sqlalchemy.ext.asyncio import AsyncSession

from src.models.movie import Certification, Genre, Director, Star


async def create_genre(session: AsyncSession, name: str) -> Genre:
    db_obj = Genre(name=name)
    session.add(db_obj)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj


async def create_certification(session: AsyncSession, name: str) -> Certification:
    db_obj = Certification(name=name)
    session.add(db_obj)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj


async def create_director(session: AsyncSession, name: str) -> Director:
    db_obj = Director(name=name)
    session.add(db_obj)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj


async def create_star(session: AsyncSession, name: str) -> Star:
    db_obj = Star(name=name)
    session.add(db_obj)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj
