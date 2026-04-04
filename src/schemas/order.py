from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal

from src.models.order import OrderStatus
from src.schemas.movie import MovieRead


class OrderItemRead(BaseModel):
    id: int
    movie: MovieRead
    price_at_order: Decimal

    class Config:
        from_attributes = True


class OrderRead(BaseModel):
    id: int
    created_at: datetime
    status: OrderStatus
    total_amount: Decimal
    items: list[OrderItemRead]

    class Config:
        from_attributes = True
