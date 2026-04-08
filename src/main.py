from fastapi import FastAPI
from src.api.auth import router as auth_router
from src.api.movies import router as movies_router
from src.api.metadata import router as metadata_router
from src.api.cart import router as cart_router
from src.api.orders import router as orders_router
from src.api.payments import router as payments_router
from src.api.favorites import router as favorites_router

app = FastAPI(
    title="Online Cinema API",
    description="API for managing movies, users, and orders",
    version="1.0.0",
    swagger_ui_parameters={"persistAuthorization": True}
)

app.include_router(auth_router, prefix="/api")
app.include_router(movies_router)
app.include_router(metadata_router)
app.include_router(cart_router, prefix="/api")
app.include_router(orders_router, prefix="/api")
app.include_router(payments_router, prefix="/api")
app.include_router(favorites_router)


@app.get("/ping")
async def pong():
    return {"message": "pong!"}
