"""
Recall Notebook Backend - FastAPI Application
Production-ready API with authentication, rate limiting, and AI integration.
"""
from contextlib import asynccontextmanager
from typing import AsyncIterator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.logging_config import configure_logging

# Configure structured logging
configure_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info(
        "starting_application",
        environment=settings.ENVIRONMENT,
        port=settings.PORT,
    )
    yield
    # Shutdown
    logger.info("shutting_down_application")


# Initialize FastAPI app
app = FastAPI(
    title="Recall Notebook API",
    description="AI-powered knowledge management backend",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": "Recall Notebook API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for Railway."""
    return {"status": "healthy", "environment": settings.ENVIRONMENT}


# Import routers
from app.api.v1 import sources, collections, search, embeddings, webhooks
from app.core.errors import (
    RecallNotebookException,
    recall_notebook_exception_handler,
    http_exception_handler,
    general_exception_handler,
)
from fastapi import HTTPException

# Exception handlers
app.add_exception_handler(RecallNotebookException, recall_notebook_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# API routers
app.include_router(sources.router, prefix="/api/v1", tags=["sources"])
app.include_router(collections.router, prefix="/api/v1", tags=["collections"])
app.include_router(search.router, prefix="/api/v1", tags=["search"])
app.include_router(embeddings.router, prefix="/api/v1", tags=["embeddings"])
app.include_router(webhooks.router, prefix="/api/v1", tags=["webhooks"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower(),
    )
