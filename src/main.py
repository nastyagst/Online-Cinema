from fastapi import FastAPI, Depends
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from src.api.auth import router as auth_router
from src.api.dependencies import get_current_user

from src.api.movies import router as movies_router
from src.api.metadata import router as metadata_router
from src.api.cart import router as cart_router
from src.api.orders import router as orders_router
from src.api.payments import router as payments_router
from src.api.favorites import router as favorites_router
from src.api.reviews import router as reviews_router
from src.models.user import User

app = FastAPI(
    title="Online Cinema API",
    description="API for managing movies, users, and orders",
    version="1.0.0",
    swagger_ui_parameters={"persistAuthorization": True},
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.include_router(auth_router, prefix="/api")
app.include_router(movies_router)
app.include_router(metadata_router)
app.include_router(cart_router, prefix="/api")
app.include_router(orders_router, prefix="/api")
app.include_router(payments_router, prefix="/api")
app.include_router(favorites_router, prefix="/api")
app.include_router(reviews_router, prefix="/api")


@app.get("/docs", include_in_schema=False)
async def protected_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title=app.title + " - Swagger UI",
        swagger_ui_parameters=app.swagger_ui_parameters,
    )


@app.get("/api/openapi.json", include_in_schema=False)
async def get_open_api_endpoint():
    return get_openapi(title=app.title, version=app.version, routes=app.routes)


@app.get("/ping")
async def pong():
    return {"message": "pong!"}
