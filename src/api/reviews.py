from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

from src.db.database import get_async_session
from src.models.movie import Movie, MovieReview
from src.models.user import User
from src.api.dependencies import get_current_user
from src.schemas.movie import ReviewCreate, ReviewRead

router = APIRouter(prefix="/movies/{movie_id}/reviews", tags=["Reviews & Ratings"])


@router.post("/", response_model=ReviewRead)
async def create_review(
    movie_id: int,
    review_data: ReviewCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    movie = await session.get(Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    stmt = select(MovieReview).where(
        MovieReview.user_id == current_user.id, MovieReview.movie_id == movie_id
    )
    res = await session.execute(stmt)
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="You already reviewed this movie")

    new_review = MovieReview(
        user_id=current_user.id, movie_id=movie_id, **review_data.model_dump()
    )

    session.add(new_review)
    await session.commit()
    await session.refresh(new_review)
    return new_review


@router.get("/", response_model=list[ReviewRead])
async def get_movie_reviews(
    movie_id: int, session: AsyncSession = Depends(get_async_session)
):
    stmt = (
        select(MovieReview)
        .options(joinedload(MovieReview.user))
        .where(MovieReview.movie_id == movie_id)
        .order_by(MovieReview.created_at.desc())
    )
    result = await session.execute(stmt)
    reviews = result.scalars().all()

    return [
        {
            "id": review.id,
            "user_email": review.user.email,
            "rating": review.rating,
            "text": review.text,
            "created_at": review.created_at,
        }
        for review in reviews
    ]


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_review(
    review_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    review = await session.get(MovieReview, review_id)

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="You can only delete your own reviews"
        )

    await session.delete(review)
    await session.commit()
    return None
