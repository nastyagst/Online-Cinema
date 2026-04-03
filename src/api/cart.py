from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload


from src.db.database import get_async_session
from src.api.dependencies import get_current_user
from src.models import Movie
from src.models.user import User
from src.models.cart import Cart, CartItem
from src.schemas.cart import CartRead, CartItemCreate

router = APIRouter(prefix="/cart", tags=["Shopping Cart"])


@router.post("/add", response_model=CartRead)
async def add_to_cart(
    item_in: CartItemCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    cart_query = select(Cart).where(Cart.user_id == current_user.id)
    result = await session.execute(cart_query)
    cart = result.scalar_one_or_none()

    if not cart:
        cart = Cart(user_id=current_user.id)
        session.add(cart)
        await session.flush()

    item_query = select(CartItem).where(
        CartItem.cart_id == cart.id, CartItem.movie_id == item_in.movie_id
    )
    item_result = await session.execute(item_query)
    if item_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This movie is already in your cart.",
        )

    new_item = CartItem(cart_id=cart.id, movie_id=item_in.movie_id)
    session.add(new_item)
    await session.commit()

    final_query = (
        select(Cart)
        .options(
            selectinload(Cart.items)
            .selectinload(CartItem.movie)
            .selectinload(Movie.certification),
            selectinload(Cart.items)
            .selectinload(CartItem.movie)
            .selectinload(Movie.genres),
            selectinload(Cart.items)
            .selectinload(CartItem.movie)
            .selectinload(Movie.directors),
            selectinload(Cart.items)
            .selectinload(CartItem.movie)
            .selectinload(Movie.stars),
        )
        .where(Cart.id == cart.id)
    )

    final_result = await session.execute(final_query)
    return final_result.unique().scalar_one()


@router.get("/", response_model=CartRead)
async def get_my_cart(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    query = (
        select(Cart)
        .options(
            selectinload(Cart.items)
            .selectinload(CartItem.movie)
            .selectinload(Movie.certification),
            selectinload(Cart.items)
            .selectinload(CartItem.movie)
            .selectinload(Movie.genres),
            selectinload(Cart.items)
            .selectinload(CartItem.movie)
            .selectinload(Movie.directors),
            selectinload(Cart.items)
            .selectinload(CartItem.movie)
            .selectinload(Movie.stars),
        )
        .where(Cart.user_id == current_user.id)
    )
    result = await session.execute(query)
    cart = result.unique().scalar_one_or_none()

    if not cart:
        return CartRead(id=0, user_id=current_user.id, items=[])
    return cart


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_cart(
    item_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(CartItem)
        .join(Cart)
        .where(CartItem.id == item_id, Cart.user_id == current_user.id)
    )
    result = await session.execute(stmt)
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The movie was not found in your cart.",
        )

    await session.delete(item)
    await session.commit()

    return None
