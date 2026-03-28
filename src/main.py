from fastapi import FastAPI
from src.api.auth import router as auth_router
from src.api.movies import router as movies_router

app = FastAPI(
    title="Online Cinema API",
    description="API for managing movies, users, and orders",
    version="1.0.0",
)

app.include_router(auth_router, prefix="/api")
app.include_router(movies_router)

@app.get("/ping")
async def pong():
    return {"message": "pong!"}
