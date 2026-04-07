import enum
from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    DateTime,
    func,
    Enum,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship
from src.db.database import Base


class PaymentStatus(enum.Enum):
    SUCCESSFUL = "successful"
    CANCELED = "canceled"
    REFUNDED = "refunded"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    order_id = Column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(
        Enum(PaymentStatus), default=PaymentStatus.SUCCESSFUL, nullable=False
    )
    amount = Column(Numeric(10, 2), nullable=False)
    external_payment_id = Column(String, nullable=True)

    user = relationship("User", back_populates="payments")
    order = relationship("Order")
    items = relationship("PaymentItem", back_populates="payment", cascade="all, delete-orphan")

class PaymentItem(Base):
    __tablename__ = "payment_items"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(
        Integer, ForeignKey("payments.id", ondelete="CASCADE"), nullable=False
    )
    order_item_id = Column(
        Integer, ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False
    )
    price_at_payment = Column(Numeric(10, 2), nullable=False)

    payment = relationship("Payment", back_populates="items")
    order_item = relationship("OrderItem")
