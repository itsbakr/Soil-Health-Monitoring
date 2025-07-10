from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from contextlib import asynccontextmanager

from routers import auth, farms, analysis
from config import settings

# Lifespan manager for startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Soil Health Platform API starting up...")
    print(f"📡 Environment: {settings.ENVIRONMENT}")
    print(f"🔗 Database URL configured: {'✅' if settings.DATABASE_URL else '❌'}")
    yield
    # Shutdown
    print("🛑 Soil Health Platform API shutting down...")

# Create FastAPI app
app = FastAPI(
    title="Soil Health Monitoring API",
    description="Backend API for comprehensive soil health monitoring and agricultural ROI optimization platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
allowed_origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring service status"""
    return {
        "status": "healthy",
        "message": "Soil Health Platform API is running",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to Soil Health Monitoring API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(farms.router, prefix="/farms", tags=["Farm Management"])
app.include_router(analysis.router, prefix="/analysis", tags=["Soil Analysis & ROI"])

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    print(f"❌ Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "detail": str(exc) if settings.ENVIRONMENT == "development" else None
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False,
        log_level="info"
    ) 