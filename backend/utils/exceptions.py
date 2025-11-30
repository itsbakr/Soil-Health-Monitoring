"""
Custom Exceptions for SoilGuard API

Provides structured error handling with:
- Descriptive error codes
- HTTP status mapping
- Error context for debugging
- User-friendly messages
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException


class SoilGuardError(Exception):
    """Base exception for all SoilGuard errors"""
    
    error_code: str = "SOILGUARD_ERROR"
    status_code: int = 500
    default_message: str = "An unexpected error occurred"
    
    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        self.message = message or self.default_message
        self.details = details or {}
        self.cause = cause
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API response"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }
    
    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException"""
        return HTTPException(
            status_code=self.status_code,
            detail=self.to_dict()
        )


# ============================================================================
# Authentication & Authorization Errors
# ============================================================================

class AuthenticationError(SoilGuardError):
    """User authentication failed"""
    error_code = "AUTH_FAILED"
    status_code = 401
    default_message = "Authentication failed"


class AuthorizationError(SoilGuardError):
    """User not authorized to perform action"""
    error_code = "NOT_AUTHORIZED"
    status_code = 403
    default_message = "You are not authorized to perform this action"


class TokenExpiredError(AuthenticationError):
    """Authentication token has expired"""
    error_code = "TOKEN_EXPIRED"
    default_message = "Your session has expired. Please log in again."


class InvalidTokenError(AuthenticationError):
    """Authentication token is invalid"""
    error_code = "INVALID_TOKEN"
    default_message = "Invalid authentication token"


# ============================================================================
# Resource Errors
# ============================================================================

class ResourceNotFoundError(SoilGuardError):
    """Requested resource not found"""
    error_code = "NOT_FOUND"
    status_code = 404
    default_message = "The requested resource was not found"


class FarmNotFoundError(ResourceNotFoundError):
    """Farm not found"""
    error_code = "FARM_NOT_FOUND"
    default_message = "Farm not found"


class AnalysisNotFoundError(ResourceNotFoundError):
    """Analysis not found"""
    error_code = "ANALYSIS_NOT_FOUND"
    default_message = "Analysis not found"


# ============================================================================
# Validation Errors
# ============================================================================

class ValidationError(SoilGuardError):
    """Request validation failed"""
    error_code = "VALIDATION_ERROR"
    status_code = 400
    default_message = "Invalid request data"


class InvalidCoordinatesError(ValidationError):
    """Invalid geographic coordinates"""
    error_code = "INVALID_COORDINATES"
    default_message = "Invalid geographic coordinates provided"


class InvalidFarmSizeError(ValidationError):
    """Farm size is invalid"""
    error_code = "INVALID_FARM_SIZE"
    default_message = "Farm size must be between 0.1 and 10000 hectares"


# ============================================================================
# External Service Errors
# ============================================================================

class ExternalServiceError(SoilGuardError):
    """External service integration failed"""
    error_code = "EXTERNAL_SERVICE_ERROR"
    status_code = 502
    default_message = "External service is temporarily unavailable"


class SatelliteServiceError(ExternalServiceError):
    """Satellite data service error"""
    error_code = "SATELLITE_SERVICE_ERROR"
    default_message = "Failed to retrieve satellite data. Please try again later."


class WeatherServiceError(ExternalServiceError):
    """Weather service error"""
    error_code = "WEATHER_SERVICE_ERROR"
    default_message = "Failed to retrieve weather data. Please try again later."


class AIServiceError(ExternalServiceError):
    """AI service error"""
    error_code = "AI_SERVICE_ERROR"
    default_message = "AI analysis service is temporarily unavailable"


class DatabaseError(ExternalServiceError):
    """Database operation failed"""
    error_code = "DATABASE_ERROR"
    status_code = 503
    default_message = "Database service is temporarily unavailable"


# ============================================================================
# Rate Limiting & Circuit Breaker Errors
# ============================================================================

class RateLimitError(SoilGuardError):
    """Rate limit exceeded"""
    error_code = "RATE_LIMIT_EXCEEDED"
    status_code = 429
    default_message = "Too many requests. Please slow down."


class CircuitBreakerOpenError(SoilGuardError):
    """Circuit breaker is open - service unavailable"""
    error_code = "CIRCUIT_BREAKER_OPEN"
    status_code = 503
    default_message = "Service temporarily unavailable due to high error rate"


class ServiceUnavailableError(SoilGuardError):
    """Service is currently unavailable"""
    error_code = "SERVICE_UNAVAILABLE"
    status_code = 503
    default_message = "Service is currently unavailable. Please try again later."


# ============================================================================
# Business Logic Errors
# ============================================================================

class DuplicateFarmError(SoilGuardError):
    """Farm with same name already exists"""
    error_code = "DUPLICATE_FARM"
    status_code = 409
    default_message = "A farm with this name already exists"


class AnalysisInProgressError(SoilGuardError):
    """Analysis already in progress for this farm"""
    error_code = "ANALYSIS_IN_PROGRESS"
    status_code = 409
    default_message = "An analysis is already in progress for this farm"


class InsufficientDataError(SoilGuardError):
    """Insufficient data for analysis"""
    error_code = "INSUFFICIENT_DATA"
    status_code = 422
    default_message = "Insufficient satellite data available for analysis"


class QuotaExceededError(SoilGuardError):
    """User quota exceeded"""
    error_code = "QUOTA_EXCEEDED"
    status_code = 429
    default_message = "You have exceeded your analysis quota for this period"

