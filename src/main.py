import logging
import os
from fastapi import FastAPI
import uvicorn
from src.db.factory import make_database
from contextlib import asynccontextmanager
from src.config import get_settings
from src.routers import hybrid_search, ping
from src.services.opensearch.factory import make_opensearch_client
from src.services.arxiv.factory import make_arxiv_client
from src.services.pdf_parser.factory import make_pdf_parser_service
from src.services.embedding.factory import make_embeddings_client
from src.services.ollama.factory import make_ollama_client
from src.services.langfuse.factory import make_langfuse_tracer
from src.routers.ask import ask_router, stream_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Starting application...")
    settings = get_settings()
    app.state.settings = settings

    database = make_database()
    app.state.database = database
    logging.info("Database connected")

    # Initialize search service
    opensearch_client = make_opensearch_client()
    app.state.opensearch_client = opensearch_client
    logging.info("Search service initialized")

    if opensearch_client.health_check():
        logging.info("Search service is healthy")
    else:
        logging.error("Search service is not healthy")

    app.state.arxiv_client = make_arxiv_client()
    app.state.opensearch_client = make_opensearch_client()
    app.state.pdf_parser = make_pdf_parser_service()
    app.state.embeddings_service = make_embeddings_client()
    app.state.ollama_client = make_ollama_client()
    app.state.langfuse_tracer = make_langfuse_tracer()
    logging.info("Services initialized: arXiv API client, OpenSearch client, PDF parser, and embeddings service")

    logging.info("API startup complete")
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
app.include_router(hybrid_search.router, prefix="/api/v1")
app.include_router(ask_router, prefix="/api/v1")
app.include_router(stream_router, prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)