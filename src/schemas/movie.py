from __future__ import annotations
import uuid
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class GenreRead(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class StarRead(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class DirectorRead(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class CertificationRead(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class MovieBase(BaseModel):
    name: str
    year: int
    time: int
    imdb: float
    votes: int
    meta_score: Optional[float] = None
    gross: Optional[float] = None
    description: str
    price: Optional[float] = None


class MovieCreate(MovieBase):
    certification_id: int
    genre_ids: Optional[List[int]] = None
    director_ids: Optional[List[int]] = None
    star_ids: Optional[List[int]] = None


class MovieRead(MovieBase):
    id: int
    uuid: uuid.UUID

    certification: CertificationRead
    genres: Optional[List[GenreRead]] = None
    directors: Optional[List[DirectorRead]] = None
    stars: Optional[List[StarRead]] = None

    model_config = ConfigDict(from_attributes=True)


class MovieUpdate(BaseModel):
    name: Optional[str] = None
    year: Optional[int] = None
    time: Optional[int] = None
    imdb: Optional[float] = None
    votes: Optional[int] = None
    meta_score: Optional[float] = None
    gross: Optional[float] = None
    description: Optional[str] = None
    price: Optional[float] = None
    certification_id: Optional[int] = None
    genre_ids: Optional[List[int]] = None
    director_ids: Optional[List[int]] = None
    star_ids: Optional[List[int]] = None
