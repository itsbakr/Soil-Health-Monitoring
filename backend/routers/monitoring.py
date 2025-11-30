"""
Monitoring Router

Provides endpoints for:
- Detailed health checks
- Dependency status
- System metrics
- Service readiness/liveness probes
"""

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
import logging
import asyncio
from typing import Dict, Any, Optional
import os
import psutil

from config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


async def check_database_connection() -> Dict[str, Any]:
    """Check database connectivity."""
    try:
        if not settings.DATABASE_URL:
            return {"status": "unconfigured", "message": "Database URL not set"}
        
        # Simple connection check would go here
        # For now, return configured status
        return {"status": "configured", "message": "Database URL configured"}
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


async def check_supabase_connection() -> Dict[str, Any]:
    """Check Supabase connectivity."""
    try:
        if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
            return {"status": "unconfigured", "message": "Supabase credentials not set"}
        
        return {"status": "configured", "url": settings.SUPABASE_URL[:30] + "..."}
    except Exception as e:
        logger.error(f"Supabase check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


async def check_google_earth_engine() -> Dict[str, Any]:
    """Check Google Earth Engine availability."""
    try:
        # Check if GEE credentials are configured
        gee_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or settings.GEE_SERVICE_ACCOUNT_KEY
        if gee_creds:
            return {"status": "configured", "message": "GEE credentials present"}
        return {"status": "unconfigured", "message": "GEE credentials not set"}
    except Exception as e:
        logger.error(f"GEE check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


async def check_ai_services() -> Dict[str, Any]:
    """Check AI service credentials."""
    services = {}
    
    # Check Gemini
    if hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY:
        services["gemini"] = {"status": "configured"}
    else:
        services["gemini"] = {"status": "unconfigured"}
    
    # Check Anthropic
    if hasattr(settings, 'ANTHROPIC_API_KEY') and settings.ANTHROPIC_API_KEY:
        services["anthropic"] = {"status": "configured"}
    else:
        services["anthropic"] = {"status": "unconfigured"}
    
    return services


async def check_weather_service() -> Dict[str, Any]:
    """Check weather service availability."""
    try:
        if hasattr(settings, 'OPENWEATHER_API_KEY') and settings.OPENWEATHER_API_KEY:
            return {"status": "configured"}
        return {"status": "unconfigured", "message": "OpenWeather API key not set"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


def get_system_metrics() -> Dict[str, Any]:
    """Get current system metrics."""
    try:
        process = psutil.Process(os.getpid())
        
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory": {
                "total_mb": psutil.virtual_memory().total / (1024 * 1024),
                "available_mb": psutil.virtual_memory().available / (1024 * 1024),
                "percent_used": psutil.virtual_memory().percent,
                "process_mb": process.memory_info().rss / (1024 * 1024)
            },
            "disk": {
                "total_gb": psutil.disk_usage('/').total / (1024 ** 3),
                "free_gb": psutil.disk_usage('/').free / (1024 ** 3),
                "percent_used": psutil.disk_usage('/').percent
            },
            "open_files": len(process.open_files()),
            "threads": process.num_threads()
        }
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        return {"error": str(e)}


@router.get("/ready", tags=["Monitoring"])
async def readiness_probe():
    """
    Kubernetes-style readiness probe.
    
    Returns 200 if the service is ready to accept traffic.
    Used by load balancers and orchestrators.
    """
    checks = await asyncio.gather(
        check_database_connection(),
        check_supabase_connection(),
        return_exceptions=True
    )
    
    db_status = checks[0] if not isinstance(checks[0], Exception) else {"status": "error"}
    supabase_status = checks[1] if not isinstance(checks[1], Exception) else {"status": "error"}
    
    # Service is ready if core dependencies are at least configured
    is_ready = (
        db_status.get("status") in ["configured", "healthy"] or
        supabase_status.get("status") in ["configured", "healthy"]
    )
    
    if not is_ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/live", tags=["Monitoring"])
async def liveness_probe():
    """
    Kubernetes-style liveness probe.
    
    Returns 200 if the service is alive and should not be restarted.
    A simple check that doesn't depend on external services.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/detailed", tags=["Monitoring"])
async def detailed_health_check():
    """
    Comprehensive health check with all dependency statuses.
    
    Returns detailed status of all system components:
    - Database connectivity
    - Supabase connection
    - Google Earth Engine
    - AI services (Gemini, Anthropic)
    - Weather service
    - System metrics
    
    Use this for detailed debugging and monitoring dashboards.
    """
    start_time = datetime.utcnow()
    
    # Run all checks concurrently
    checks = await asyncio.gather(
        check_database_connection(),
        check_supabase_connection(),
        check_google_earth_engine(),
        check_ai_services(),
        check_weather_service(),
        return_exceptions=True
    )
    
    # Process results
    dependencies = {
        "database": checks[0] if not isinstance(checks[0], Exception) else {"status": "error", "error": str(checks[0])},
        "supabase": checks[1] if not isinstance(checks[1], Exception) else {"status": "error", "error": str(checks[1])},
        "google_earth_engine": checks[2] if not isinstance(checks[2], Exception) else {"status": "error", "error": str(checks[2])},
        "ai_services": checks[3] if not isinstance(checks[3], Exception) else {"status": "error", "error": str(checks[3])},
        "weather_service": checks[4] if not isinstance(checks[4], Exception) else {"status": "error", "error": str(checks[4])},
    }
    
    # Get system metrics
    system_metrics = get_system_metrics()
    
    # Calculate overall health
    unhealthy_count = sum(
        1 for dep in dependencies.values() 
        if isinstance(dep, dict) and dep.get("status") == "unhealthy"
    )
    
    if unhealthy_count == 0:
        overall_status = "healthy"
    elif unhealthy_count < 2:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"
    
    end_time = datetime.utcnow()
    check_duration_ms = (end_time - start_time).total_seconds() * 1000
    
    return {
        "status": overall_status,
        "timestamp": end_time.isoformat(),
        "check_duration_ms": round(check_duration_ms, 2),
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "dependencies": dependencies,
        "system": system_metrics
    }


@router.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    """
    Get system and application metrics.
    
    Returns:
    - System resource usage
    - Process information
    - Basic application stats
    
    Can be scraped by Prometheus or similar monitoring tools.
    """
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "system": get_system_metrics(),
        "application": {
            "environment": settings.ENVIRONMENT,
            "version": "1.0.0",
            "uptime_check": "healthy"
        }
    }

