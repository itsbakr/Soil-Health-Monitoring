"""
Structured Logging Configuration for SoilGuard

Provides:
- Correlation ID tracking across requests
- JSON structured logging for production
- Human-readable format for development
- Request/response logging middleware
- Performance timing
"""

import logging
import json
import sys
import time
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from contextvars import ContextVar
from functools import wraps

# Context variable for request correlation ID
correlation_id_var: ContextVar[str] = ContextVar('correlation_id', default='')


class CorrelationIdFilter(logging.Filter):
    """Add correlation ID to log records"""
    
    def filter(self, record):
        record.correlation_id = correlation_id_var.get() or '-'
        return True


class JsonFormatter(logging.Formatter):
    """Format log records as JSON for production"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, 'correlation_id', '-'),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        return json.dumps(log_data)


class DevFormatter(logging.Formatter):
    """Human-readable format for development"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, '')
        correlation_id = getattr(record, 'correlation_id', '-')
        
        # Truncate correlation ID for readability
        short_id = correlation_id[:8] if len(correlation_id) > 8 else correlation_id
        
        return (
            f"{color}[{record.levelname:8}]{self.RESET} "
            f"[{short_id}] "
            f"{record.name}: "
            f"{record.getMessage()}"
        )


def setup_logging(
    level: str = "INFO",
    json_format: bool = False,
    log_file: Optional[str] = None
) -> None:
    """
    Configure application logging
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        json_format: Use JSON format (recommended for production)
        log_file: Optional file path for log output
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    
    # Set formatter based on format preference
    if json_format:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(DevFormatter())
    
    # Add correlation ID filter
    handler.addFilter(CorrelationIdFilter())
    
    root_logger.addHandler(handler)
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(JsonFormatter())  # Always JSON for files
        file_handler.addFilter(CorrelationIdFilter())
        root_logger.addHandler(file_handler)
    
    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_correlation_id() -> str:
    """Get the current correlation ID"""
    return correlation_id_var.get()


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID for the current context"""
    correlation_id_var.set(correlation_id)


def generate_correlation_id() -> str:
    """Generate a new correlation ID"""
    return str(uuid.uuid4())


class LogContext:
    """Context manager for logging with extra data"""
    
    def __init__(self, logger: logging.Logger, **extra_data):
        self.logger = logger
        self.extra_data = extra_data
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def info(self, msg: str, **kwargs):
        self._log(logging.INFO, msg, **kwargs)
    
    def debug(self, msg: str, **kwargs):
        self._log(logging.DEBUG, msg, **kwargs)
    
    def warning(self, msg: str, **kwargs):
        self._log(logging.WARNING, msg, **kwargs)
    
    def error(self, msg: str, **kwargs):
        self._log(logging.ERROR, msg, **kwargs)
    
    def _log(self, level: int, msg: str, **kwargs):
        extra = {**self.extra_data, **kwargs}
        record = self.logger.makeRecord(
            self.logger.name,
            level,
            "",
            0,
            msg,
            (),
            None
        )
        record.extra_data = extra
        self.logger.handle(record)


def log_performance(logger: Optional[logging.Logger] = None):
    """Decorator to log function performance"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            _logger = logger or logging.getLogger(func.__module__)
            start_time = time.perf_counter()
            
            try:
                result = await func(*args, **kwargs)
                duration = (time.perf_counter() - start_time) * 1000
                _logger.info(f"⚡ {func.__name__} completed in {duration:.2f}ms")
                return result
            except Exception as e:
                duration = (time.perf_counter() - start_time) * 1000
                _logger.error(f"❌ {func.__name__} failed after {duration:.2f}ms: {e}")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            _logger = logger or logging.getLogger(func.__module__)
            start_time = time.perf_counter()
            
            try:
                result = func(*args, **kwargs)
                duration = (time.perf_counter() - start_time) * 1000
                _logger.info(f"⚡ {func.__name__} completed in {duration:.2f}ms")
                return result
            except Exception as e:
                duration = (time.perf_counter() - start_time) * 1000
                _logger.error(f"❌ {func.__name__} failed after {duration:.2f}ms: {e}")
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# FastAPI Middleware for request logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests with correlation IDs"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate or extract correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or generate_correlation_id()
        set_correlation_id(correlation_id)
        
        logger = logging.getLogger("api.request")
        
        # Log request
        start_time = time.perf_counter()
        logger.info(f"→ {request.method} {request.url.path}")
        
        # Process request
        try:
            response: Response = await call_next(request)
            
            # Calculate duration
            duration = (time.perf_counter() - start_time) * 1000
            
            # Log response
            status_emoji = "✅" if response.status_code < 400 else "⚠️" if response.status_code < 500 else "❌"
            logger.info(f"← {status_emoji} {response.status_code} {request.url.path} ({duration:.0f}ms)")
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            
            return response
            
        except Exception as e:
            duration = (time.perf_counter() - start_time) * 1000
            logger.error(f"← ❌ 500 {request.url.path} ({duration:.0f}ms) - {str(e)}")
            raise


# Sentry integration helper
def init_sentry(dsn: Optional[str] = None, environment: str = "development"):
    """Initialize Sentry for error tracking"""
    logger = logging.getLogger(__name__)
    
    if not dsn:
        logger.info("Sentry DSN not provided, error tracking disabled")
        return
    
    # Validate DSN format - skip if it contains placeholder values
    if any(placeholder in dsn.lower() for placeholder in ['your-', 'example', 'placeholder', 'xxx']):
        logger.info("Sentry DSN appears to be a placeholder, error tracking disabled")
        return
    
    # Basic DSN format validation (should contain @ and numeric project ID)
    if '@' not in dsn or not any(char.isdigit() for char in dsn.split('/')[-1]):
        logger.warning("Invalid Sentry DSN format, error tracking disabled")
        return
    
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            traces_sample_rate=0.1 if environment == "production" else 1.0,
            profiles_sample_rate=0.1 if environment == "production" else 1.0,
            integrations=[
                FastApiIntegration(),
                LoggingIntegration(level=logging.ERROR, event_level=logging.ERROR)
            ],
            before_send=lambda event, hint: _add_correlation_id(event, hint)
        )
        logger.info(f"Sentry initialized for {environment}")
        
    except ImportError:
        logger.warning("sentry-sdk not installed, error tracking disabled")
    except Exception as e:
        logger.warning(f"Failed to initialize Sentry: {e}")


def _add_correlation_id(event, hint):
    """Add correlation ID to Sentry events"""
    correlation_id = get_correlation_id()
    if correlation_id:
        event.setdefault("tags", {})["correlation_id"] = correlation_id
    return event

