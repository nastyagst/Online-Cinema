import enum

from sqlalchemy import Column, Integer, ForeignKey, DateTime, func, Enum, Numeric
from sqlalchemy.orm import relationship

from src.db.database import Base


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELED = "canceled"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=True)

    user = relationship("User", back_populates="orders")
    items = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    movie_id = Column(
        Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False
    )
    price_at_order = Column(Numeric(10, 2), nullable=False)

    order = relationship("Order", back_populates="items")
    movie = relationship("Movie")
