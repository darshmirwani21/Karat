"""
Karat Backend - Main Application Entry Point
FastAPI application for AI-powered financial assistant
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api import banking, optimization, planning, dashboard
from database.connection import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    init_db()
    yield
    # Cleanup if needed


app = FastAPI(
    title="Karat API",
    description="AI-Powered Financial Assistant Backend",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(banking.router, prefix="/api/banking", tags=["banking"])
app.include_router(optimization.router, prefix="/api/optimization", tags=["optimization"])
app.include_router(planning.router, prefix="/api/planning", tags=["planning"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Karat API",
        "version": "1.0.0"
    }


@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",  # TODO: Add actual DB check
        "plaid": "configured"  # TODO: Add actual Plaid check
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

