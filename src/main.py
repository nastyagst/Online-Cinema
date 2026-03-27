from fastapi import FastAPI

app = FastAPI(
    title="Online Cinema API",
    description="API for managing movies, users, and orders",
    version="1.0.0",
)


@app.get("/ping")
async def pong():
    return {"message": "pong!"}
