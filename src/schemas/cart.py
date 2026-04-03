from pydantic import BaseModel, Field
from src.schemas.movie import MovieRead


class CartItemCreate(BaseModel):
    movie_id: int


class CartItemRead(BaseModel):
    id: int
    movie: MovieRead

    class Config:
        from_attributes = True


class CartRead(BaseModel):
    id: int
    user_id: int
    items: list[CartItemRead]

    class Config:
        from_attributes = True
