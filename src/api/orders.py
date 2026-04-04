from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.db.database import get_async_session
from src.api.dependencies import get_current_user, get_current_moderator
from src.models import Movie
from src.models.user import User
from src.models.cart import Cart, CartItem
from src.models.order import Order, OrderItem, OrderStatus
from src.schemas.order import OrderRead

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderRead)
async def place_order(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    cart_query = (
        select(Cart)
        .options(joinedload(Cart.items).joinedload(CartItem.movie))
        .where(Cart.user_id == current_user.id)
    )
    cart_result = await session.execute(cart_query)
    cart = cart_result.unique().scalar_one_or_none()

    if not cart or not cart.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Your cart is empty"
        )

    purchased_query = (
        select(OrderItem.movie_id)
        .join(Order)
        .where(Order.user_id == current_user.id, Order.status == OrderStatus.PAID)
    )
    purchased_result = await session.execute(purchased_query)
    purchased_ids = set(purchased_result.scalars().all())

    valid_items = [item for item in cart.items if item.movie_id not in purchased_ids]

    if not valid_items:
        raise HTTPException(
            status_code=400, detail="All movies in your cart were already purchased."
        )

    total_amount = sum(item.movie.price for item in cart.items)

    new_order = Order(
        user_id=current_user.id, status=OrderStatus.PENDING, total_amount=total_amount
    )
    session.add(new_order)
    await session.flush()

    for cart_item in cart.items:
        order_item = OrderItem(
            order_id=new_order.id,
            movie_id=cart_item.movie_id,
            price_at_order=cart_item.movie.price,
        )
        session.add(order_item)

    for cart_item in cart.items:
        await session.delete(cart_item)

    await session.commit()

    final_query = (
        select(Order)
        .options(
            selectinload(Order.items)
            .selectinload(OrderItem.movie)
            .selectinload(Movie.certification),
            selectinload(Order.items)
            .selectinload(OrderItem.movie)
            .selectinload(Movie.genres),
            selectinload(Order.items)
            .selectinload(OrderItem.movie)
            .selectinload(Movie.directors),
            selectinload(Order.items)
            .selectinload(OrderItem.movie)
            .selectinload(Movie.stars),
        )
        .where(Order.id == new_order.id)
    )

    final_result = await session.execute(final_query)
    return final_result.unique().scalar_one()


@router.get("/my_orders", response_model=List[OrderRead])
async def get_my_orders(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    query = (
        select(Order)
        .options(
            selectinload(Order.items)
            .selectinload(OrderItem.movie)
            .selectinload(Movie.genres),
            selectinload(Order.items)
            .selectinload(OrderItem.movie)
            .selectinload(Movie.certification),
            selectinload(Order.items)
            .selectinload(OrderItem.movie)
            .selectinload(Movie.directors),
            selectinload(Order.items)
            .selectinload(OrderItem.movie)
            .selectinload(Movie.stars),
        )
        .where(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
    )
    result = await session.execute(query)
    orders = result.unique().scalars().all()
    return orders


@router.get("/all", response_model=List[OrderRead])
async def get_all_orders(
    status: Optional[OrderStatus] = None,
    user_id: Optional[int] = None,
    session: AsyncSession = Depends(get_async_session),
    moderator: User = Depends(get_current_moderator),
):
    query = (
        select(Order)
        .options(
            selectinload(Order.items)
            .selectinload(OrderItem.movie)
            .selectinload(Movie.certification),
            selectinload(Order.items)
            .selectinload(OrderItem.movie)
            .selectinload(Movie.genres),
            selectinload(Order.items)
            .selectinload(OrderItem.movie)
            .selectinload(Movie.directors),
            selectinload(Order.items)
            .selectinload(OrderItem.movie)
            .selectinload(Movie.stars),
        )
        .order_by(Order.created_at.desc())
    )

    if status:
        query = query.where(Order.status == status)
    if user_id:
        query = query.where(Order.user_id == user_id)

    result = await session.execute(query)
    return result.unique().scalars().all()
