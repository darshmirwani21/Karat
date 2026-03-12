"""
Karat Backend - Main Application Entry Point
FastAPI application for AI-powered financial assistant
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from api import banking, optimization, planning, dashboard
from database.connection import get_db, init_db
from middleware.error_handler import ErrorHandler, ValidationError, DatabaseError, ExternalServiceError


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

# Add error handling middleware
app.add_middleware(ErrorHandler)

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


async def check_database_health():
    """Check database connectivity"""
    try:
        db = next(get_db())
        # Simple query to test connection
        result = db.execute(text("SELECT 1"))
        if result:
            return {"status": "healthy", "response_time_ms": 0}
        return {"status": "unhealthy", "error": "No response from database"}
    except SQLAlchemyError as e:
        return {"status": "unhealthy", "error": str(e)}
    except Exception as e:
        return {"status": "unhealthy", "error": f"Unexpected error: {str(e)}"}
    finally:
        if 'db' in locals():
            db.close()


async def check_plaid_health():
    """Check Plaid configuration"""
    try:
        import os
        plaid_client_id = os.getenv("PLAID_CLIENT_ID")
        plaid_secret = os.getenv("PLAID_SECRET")
        
        if plaid_client_id and plaid_secret:
            return {"status": "configured", "sandbox_mode": True}
        else:
            return {"status": "not_configured", "error": "Plaid credentials not found"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def check_ml_models_health():
    """Check ML model availability"""
    try:
        from ml.spending_forecast import SpendingForecaster
        from optimization.savings_optimizer import SavingsOptimizer
        
        # Test basic instantiation
        forecaster = SpendingForecaster()
        optimizer = SavingsOptimizer()
        
        return {"status": "healthy", "models": ["spending_forecast", "savings_optimizer"]}
    except ImportError as e:
        return {"status": "error", "error": f"ML model import failed: {str(e)}"}
    except Exception as e:
        return {"status": "error", "error": f"ML model initialization failed: {str(e)}"}


@app.get("/")
async def root():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "Karat API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    start_time = time.time()
    
    # Run all health checks
    db_health = await check_database_health()
    plaid_health = await check_plaid_health()
    ml_health = await check_ml_models_health()
    
    total_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    # Determine overall status
    overall_status = "healthy"
    if db_health["status"] != "healthy" or ml_health["status"] != "healthy":
        overall_status = "degraded"
    if db_health["status"] == "unhealthy" or ml_health["status"] == "error":
        overall_status = "unhealthy"
    
    return {
        "status": overall_status,
        "response_time_ms": round(total_time, 2),
        "checks": {
            "database": db_health,
            "plaid": plaid_health,
            "ml_models": ml_health
        },
        "endpoints": {
            "banking": "/api/banking",
            "optimization": "/api/optimization",
            "planning": "/api/planning",
            "dashboard": "/api/dashboard"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/health/ready")
async def readiness_check():
    """Readiness check for container orchestration"""
    # Check if all critical services are ready
    db_health = await check_database_health()
    ml_health = await check_ml_models_health()
    
    if db_health["status"] == "healthy" and ml_health["status"] == "healthy":
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat()
        }
    else:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "database": db_health["status"],
                "ml_models": ml_health["status"],
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@app.get("/api/health/live")
async def liveness_check():
    """Liveness check for container orchestration"""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

