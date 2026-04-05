"""
Intelligence Service - Main Application
Provides event detection, clustering, and risk scoring for news intelligence.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager

from app.routers.intelligence import router as intelligence_router
from app.api import clustering_admin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for the application"""
    logger.info("Intelligence Service starting up...")
    # Startup logic here (database connections, etc.)
    yield
    # Shutdown logic here
    logger.info("Intelligence Service shutting down...")


# Create FastAPI application
app = FastAPI(
    title="Intelligence Service",
    description="News Intelligence - Event Detection, Clustering & Risk Analysis",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(intelligence_router)
app.include_router(clustering_admin.router, prefix="/api/v1/intelligence")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "intelligence",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Intelligence Service",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
