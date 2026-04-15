import pytest
from httpx import AsyncClient
from unittest.mock import patch

from sqlalchemy import select


@pytest.fixture
async def created_order(user_client: AsyncClient, moderator_client: AsyncClient, setup_certification):
    movie_data = {
        "name": "Payment Movie",
        "year": 2024,
        "time": 100,
        "imdb": 8.0,
        "votes": 100,
        "description": "Test",
        "price": 20.0,
        "certification_id": setup_certification.id,
    }
    m_resp = await moderator_client.post("/api/movies/", json=movie_data)
    movie = m_resp.json()
    await user_client.post("/api/cart/add", json={"movie_id": movie["id"]})
    o_resp = await user_client.post("/api/orders/")
    return o_resp.json()


@pytest.mark.asyncio
async def test_create_checkout_session(user_client: AsyncClient, created_order: dict):
    with patch("stripe.checkout.Session.create") as mock_stripe:
        mock_stripe.return_value.url = "https://stripe.com/test-url"
        response = await user_client.post(f"/api/payments/create-checkout-session/{created_order['id']}")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_stripe_webhook_success(client: AsyncClient, created_order: dict, db_session):
    from src.models.order import Order, OrderStatus

    class MockObject:
        def __init__(self, data):
            for k, v in data.items():
                setattr(self, k, MockObject(v) if isinstance(v, dict) else v)

    mock_event = MockObject(
        {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test",
                    "metadata": {"order_id": str(created_order["id"])},
                }
            },
        }
    )

    with (
        patch("stripe.Webhook.construct_event", return_value=mock_event),
        patch("src.tasks.send_payment_success_email.delay"),
    ):
        headers = {"stripe-signature": "test_sig"}
        response = await client.post("/api/payments/webhook", content=b"payload", headers=headers)
        assert response.status_code == 200

        db_session.expire_all()

        res = await db_session.execute(select(Order).where(Order.id == created_order["id"]))
        order = res.scalar_one()
        assert order.status == OrderStatus.PAID


@pytest.mark.asyncio
async def test_payment_success_page(client: AsyncClient):
    response = await client.get("/api/payments/success")
    assert response.status_code == 200
