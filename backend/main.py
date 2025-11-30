from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
from contextlib import asynccontextmanager

from routers import auth, farms, analysis, admin, monitoring
from config import settings
from utils.logging_config import (
    setup_logging,
    RequestLoggingMiddleware,
    init_sentry,
    get_correlation_id
)
from utils.rate_limiter import limiter, rate_limit_exceeded_handler
from utils.security import SecurityHeadersMiddleware, RequestValidationMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Initialize logging
setup_logging(
    level=settings.LOG_LEVEL if hasattr(settings, 'LOG_LEVEL') else "INFO",
    json_format=settings.ENVIRONMENT == "production"
)

# Initialize Sentry for error tracking (if DSN is configured)
init_sentry(
    dsn=settings.SENTRY_DSN if hasattr(settings, 'SENTRY_DSN') else None,
    environment=settings.ENVIRONMENT
)

logger = logging.getLogger(__name__)

# Lifespan manager for startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Soil Health Platform API starting up...")
    logger.info(f"📡 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🔗 Database URL configured: {'✅' if settings.DATABASE_URL else '❌'}")
    yield
    # Shutdown
    logger.info("🛑 Soil Health Platform API shutting down...")

# API Version
API_VERSION = "1.0.0"

# OpenAPI Tags metadata for better documentation organization
tags_metadata = [
    {
        "name": "Health",
        "description": "Service health checks and system status",
    },
    {
        "name": "Monitoring",
        "description": "System monitoring, metrics, and detailed health checks for infrastructure observability.",
    },
    {
        "name": "Authentication",
        "description": "User authentication and authorization endpoints. Handles JWT-based authentication.",
    },
    {
        "name": "Farm Management",
        "description": "CRUD operations for farm data. Create, read, update, and delete farm information.",
    },
    {
        "name": "Soil Analysis & ROI",
        "description": "Satellite-based soil health analysis and ROI projections using AI-powered insights.",
        "externalDocs": {
            "description": "Learn more about satellite indices",
            "url": "https://earthobservatory.nasa.gov/features/MeasuringVegetation"
        }
    },
    {
        "name": "Admin Dashboard",
        "description": "Administrative endpoints for B2B partners and system monitoring.",
    },
]

# Create FastAPI app with enhanced OpenAPI documentation
app = FastAPI(
    title="SoilGuard API",
    description="""
## Soil Health Monitoring & Agricultural Intelligence Platform

SoilGuard provides comprehensive soil health monitoring and agricultural ROI optimization
through satellite data analysis and AI-powered insights.

### Key Features

* **Satellite Data Analysis** - Vegetation indices (NDVI, NDWI, EVI, SAVI) from Sentinel-2 and Landsat
* **Soil Health Assessment** - Multi-factor analysis including moisture, salinity, and organic matter
* **Zone-Based Analysis** - Granular farm area analysis with grid-based health mapping
* **AI-Powered Recommendations** - Crop suggestions and treatment plans using Google Gemini & Anthropic Claude
* **ROI Projections** - Economic analysis and yield predictions
* **Weather Integration** - Real-time weather data and forecasts for agricultural planning

### Authentication

All protected endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_token>
```

### Rate Limiting

API requests are rate-limited to ensure fair usage:
- Standard endpoints: 60 requests/minute
- Analysis endpoints: 10 requests/minute

### Error Handling

All errors include a correlation ID for tracking. When reporting issues, please include this ID.

### API Versioning

Current version: **v1.0.0**

Version is included in responses and can be used for compatibility checking.
    """,
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=tags_metadata,
    contact={
        "name": "SoilGuard Support",
        "email": "support@soilguard.io",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware, environment=settings.ENVIRONMENT)

# Add request validation middleware
app.add_middleware(RequestValidationMiddleware)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

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
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring service status.
    
    Returns:
        - status: Current health status (healthy/degraded/unhealthy)
        - message: Human-readable status message
        - version: API version
        - environment: Deployment environment
        - timestamp: Current server timestamp
    
    Use this endpoint for:
    - Load balancer health checks
    - Monitoring systems (Prometheus, DataDog, etc.)
    - Service discovery health validation
    """
    from datetime import datetime
    return {
        "status": "healthy",
        "message": "SoilGuard API is running",
        "version": API_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat()
    }

# Root endpoint
@app.get("/", tags=["Health"])
async def root():
    """
    Root endpoint providing API information and navigation links.
    
    Returns basic API information including:
    - API name and version
    - Documentation URLs
    - Quick start information
    """
    return {
        "name": "SoilGuard API",
        "description": "Soil Health Monitoring & Agricultural Intelligence Platform",
        "version": API_VERSION,
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        },
        "health": "/health",
        "getting_started": "Visit /docs for interactive API documentation"
    }

# API Version endpoint
@app.get("/api/version", tags=["Health"])
async def get_api_version():
    """
    Get detailed API version information.
    
    Use this for version compatibility checking in client applications.
    """
    return {
        "version": API_VERSION,
        "major": int(API_VERSION.split('.')[0]),
        "minor": int(API_VERSION.split('.')[1]),
        "patch": int(API_VERSION.split('.')[2]),
        "api_prefix": "/api/v1",
        "deprecated_versions": [],
        "supported_versions": ["1.0.0"]
    }

# Include routers with API versioning
# v1 API routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(farms.router, prefix="/api/v1/farms", tags=["Farm Management"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Soil Analysis & ROI"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin Dashboard"])

# Monitoring endpoints (not versioned - infrastructure concerns)
app.include_router(monitoring.router, prefix="/monitoring", tags=["Monitoring"])

# Legacy routes (deprecated, will be removed in v2)
# Keeping for backward compatibility
app.include_router(auth.router, prefix="/auth", tags=["Authentication"], deprecated=True)
app.include_router(farms.router, prefix="/farms", tags=["Farm Management"], deprecated=True)
app.include_router(analysis.router, prefix="/analysis", tags=["Soil Analysis & ROI"], deprecated=True)
app.include_router(admin.router, prefix="/admin", tags=["Admin Dashboard"], deprecated=True)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    correlation_id = get_correlation_id()
    
    logger.error(
        f"❌ Unhandled exception: {exc}",
        exc_info=True,
        extra={
            "correlation_id": correlation_id,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "correlation_id": correlation_id,
            "detail": str(exc) if settings.ENVIRONMENT == "development" else None
        },
        headers={"X-Correlation-ID": correlation_id}
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False,
        log_level="info"
    ) 