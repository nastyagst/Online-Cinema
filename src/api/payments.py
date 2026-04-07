import stripe
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi.responses import HTMLResponse

from src.db.database import get_async_session
from src.api.dependencies import get_current_user
from src.models.user import User
from src.models.order import Order, OrderStatus, OrderItem
from src.models.cart import Cart, CartItem
from src.models.payment import Payment, PaymentStatus
from src.schemas.payment import PaymentLink
from src.core.security import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET

stripe.api_key = STRIPE_SECRET_KEY

router = APIRouter(prefix="/payments", tags=["Payment"])


@router.post("/create-checkout-session/{order_id}", response_model=PaymentLink)
async def create_checkout_session(
    order_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    query = (
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.movie))
        .where(Order.id == order_id, Order.user_id == current_user.id)
    )
    result = await session.execute(query)
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status == OrderStatus.PAID:
        raise HTTPException(status_code=400, detail="Order already paid")

    line_items = []
    for item in order.items:
        line_items.append(
            {
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": item.movie.name,
                    },
                    "unit_amount": int(item.price_at_order * 100),
                },
                "quantity": 1,
            }
        )

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url="http://localhost:8002/api/payments/success",
            cancel_url="http://localhost:8002/api/payments/cancel",
            metadata={"order_id": str(order.id)},
        )
        return {"checkout_url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(
    request: Request, session: AsyncSession = Depends(get_async_session)
):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:

        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event.type == "checkout.session.completed":

        session_obj = event.data.object

        order_id = getattr(session_obj.metadata, "order_id", None)

        if order_id:
            try:
                stmt = select(Order).where(Order.id == int(order_id))
                res = await session.execute(stmt)
                order = res.scalar_one_or_none()

                if order and order.status != OrderStatus.PAID:
                    order.status = OrderStatus.PAID

                    new_payment = Payment(
                        user_id=order.user_id,
                        order_id=order.id,
                        amount=order.total_amount,
                        status=PaymentStatus.SUCCESSFUL,
                        external_payment_id=session_obj.id,
                    )
                    session.add(new_payment)

                    cart_stmt = select(Cart).where(Cart.user_id == order.user_id)
                    cart_res = await session.execute(cart_stmt)
                    user_cart = cart_res.scalar_one_or_none()

                    if user_cart:
                        items_stmt = select(OrderItem.movie_id).where(OrderItem.order_id == order.id)
                        items_res = await session.execute(items_stmt)
                        movie_ids_in_order = items_res.scalars().all()

                        if movie_ids_in_order:
                            delete_stmt = delete(CartItem).where(
                                CartItem.cart_id == user_cart.id,
                                CartItem.movie_id.in_(movie_ids_in_order),
                            )
                            await session.execute(delete_stmt)

                    await session.commit()
            except Exception as e:
                print(f"Database error: {e}")
                await session.rollback()

    return {"status": "success"}


@router.get("/success", response_class=HTMLResponse)
async def payment_success():
    return """
        <html>
            <head><title>Payment Successful!</title></head>
            <body style="text-align: center; margin-top: 50px; font-family: Arial, sans-serif;">
                <h1 style="color: green;">Payment Successful!</h1>
                <p>Thank you for your purchase. Your movies are now available in your account.</p>
            </body>
        </html>
        """

@router.get("/cancel", response_class=HTMLResponse)
async def payment_cancel():
    return """
        <html>
            <head><title>Payment Canceled</title></head>
            <body style="text-align: center; margin-top: 50px; font-family: Arial, sans-serif;">
                <h1 style="color: red;">Payment Canceled </h1>
                <p>You did not complete the payment. You can return to your cart and try again.</p>
            </body>
        </html>
        """
