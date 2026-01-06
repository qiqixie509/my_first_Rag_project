import logging
import os
from fastapi import FastAPI
import uvicorn
from db.interfaces.postgresql import PostgreSQLDatabase
from db.interfaces import make_database
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Starting application...")
    settings = get_settings()
    app.state.settings = settings

    database = make_database()
    app.state.database = database
    logging.info("Database connected")

    yield
    database.teardown()
    logging.info("API shutdown complete")

app = FastAPI(
    title="My First Rag Project",
    description="My First Rag Project",
    version="0.0.1",
    lifespan=lifespan,
)

app.include_router(ping.router, prefix="/api/v1") # Health check endpoint

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)