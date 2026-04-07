from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from .order import OrderRead


class PaymentRead(BaseModel):
    id: int
    order_id: int
    amount: Decimal
    status: str
    created_at: datetime
    external_payment_id: str | None

    class Config:
        from_attributes = True


class PaymentLink(BaseModel):
    checkout_url: str
