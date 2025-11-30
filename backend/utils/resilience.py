"""
Resilience Patterns for SoilGuard API

Provides:
- Circuit breaker pattern for external services
- Retry logic with exponential backoff
- Fallback strategies
- Timeout handling
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Callable, Optional, TypeVar, Any, Dict
from dataclasses import dataclass, field
from functools import wraps
from datetime import datetime, timedelta

from .exceptions import CircuitBreakerOpenError, ExternalServiceError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Blocking calls
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5        # Failures before opening
    success_threshold: int = 2        # Successes in half-open to close
    timeout_seconds: float = 60.0     # How long circuit stays open
    half_open_max_calls: int = 3      # Max calls in half-open state


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker"""
    failures: int = 0
    successes: int = 0
    last_failure_time: Optional[datetime] = None
    state: CircuitState = CircuitState.CLOSED
    half_open_calls: int = 0
    total_calls: int = 0
    total_failures: int = 0


class CircuitBreaker:
    """
    Circuit Breaker implementation for protecting external service calls.
    
    States:
    - CLOSED: Normal operation, calls pass through
    - OPEN: Service is failing, calls are blocked
    - HALF_OPEN: Testing if service has recovered
    """
    
    # Class-level registry of circuit breakers
    _breakers: Dict[str, 'CircuitBreaker'] = {}
    
    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()
        
        # Register this breaker
        CircuitBreaker._breakers[name] = self
    
    @classmethod
    def get(cls, name: str) -> Optional['CircuitBreaker']:
        """Get a circuit breaker by name"""
        return cls._breakers.get(name)
    
    @classmethod
    def get_all_stats(cls) -> Dict[str, Dict]:
        """Get stats for all circuit breakers"""
        return {
            name: {
                "state": breaker.stats.state.value,
                "failures": breaker.stats.failures,
                "successes": breaker.stats.successes,
                "total_calls": breaker.stats.total_calls,
                "total_failures": breaker.stats.total_failures,
            }
            for name, breaker in cls._breakers.items()
        }
    
    async def _should_allow_call(self) -> bool:
        """Check if call should be allowed based on current state"""
        if self.stats.state == CircuitState.CLOSED:
            return True
        
        if self.stats.state == CircuitState.OPEN:
            # Check if timeout has passed
            if self.stats.last_failure_time:
                elapsed = datetime.now() - self.stats.last_failure_time
                if elapsed > timedelta(seconds=self.config.timeout_seconds):
                    # Transition to half-open
                    async with self._lock:
                        self.stats.state = CircuitState.HALF_OPEN
                        self.stats.half_open_calls = 0
                        self.stats.successes = 0
                    logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN")
                    return True
            return False
        
        if self.stats.state == CircuitState.HALF_OPEN:
            # Allow limited calls in half-open state
            return self.stats.half_open_calls < self.config.half_open_max_calls
        
        return True
    
    async def record_success(self):
        """Record a successful call"""
        async with self._lock:
            self.stats.total_calls += 1
            self.stats.successes += 1
            
            if self.stats.state == CircuitState.HALF_OPEN:
                if self.stats.successes >= self.config.success_threshold:
                    # Service recovered, close circuit
                    self.stats.state = CircuitState.CLOSED
                    self.stats.failures = 0
                    self.stats.successes = 0
                    logger.info(f"Circuit breaker '{self.name}' CLOSED - service recovered")
    
    async def record_failure(self, error: Optional[Exception] = None):
        """Record a failed call"""
        async with self._lock:
            self.stats.total_calls += 1
            self.stats.total_failures += 1
            self.stats.failures += 1
            self.stats.last_failure_time = datetime.now()
            
            if self.stats.state == CircuitState.HALF_OPEN:
                # Failure in half-open, go back to open
                self.stats.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker '{self.name}' OPEN - failure in half-open state")
            
            elif self.stats.state == CircuitState.CLOSED:
                if self.stats.failures >= self.config.failure_threshold:
                    self.stats.state = CircuitState.OPEN
                    logger.warning(
                        f"Circuit breaker '{self.name}' OPEN - "
                        f"threshold reached ({self.stats.failures} failures)"
                    )
    
    async def call(
        self,
        func: Callable[..., T],
        *args,
        fallback: Optional[Callable[..., T]] = None,
        **kwargs
    ) -> T:
        """
        Execute a function through the circuit breaker.
        
        Args:
            func: Async function to execute
            *args: Function arguments
            fallback: Optional fallback function if circuit is open
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open and no fallback
        """
        if not await self._should_allow_call():
            if fallback:
                logger.info(f"Circuit breaker '{self.name}' OPEN - using fallback")
                return await fallback(*args, **kwargs) if asyncio.iscoroutinefunction(fallback) else fallback(*args, **kwargs)
            raise CircuitBreakerOpenError(
                f"Service '{self.name}' is temporarily unavailable",
                details={"circuit_state": self.stats.state.value}
            )
        
        if self.stats.state == CircuitState.HALF_OPEN:
            async with self._lock:
                self.stats.half_open_calls += 1
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            await self.record_success()
            return result
        except Exception as e:
            await self.record_failure(e)
            raise


def circuit_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None,
    fallback: Optional[Callable] = None
):
    """
    Decorator to apply circuit breaker pattern to a function.
    
    Usage:
        @circuit_breaker("satellite_service")
        async def fetch_satellite_data(lat, lon):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        breaker = CircuitBreaker(name, config)
        
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await breaker.call(func, *args, fallback=fallback, **kwargs)
        
        return wrapper
    return decorator


@dataclass
class RetryConfig:
    """Configuration for retry logic"""
    max_retries: int = 3
    base_delay: float = 1.0           # Base delay in seconds
    max_delay: float = 30.0           # Maximum delay
    exponential_base: float = 2.0     # Exponential backoff base
    jitter: bool = True               # Add random jitter
    retry_exceptions: tuple = (Exception,)  # Exceptions to retry on


async def retry_with_backoff(
    func: Callable[..., T],
    *args,
    config: Optional[RetryConfig] = None,
    **kwargs
) -> T:
    """
    Execute a function with retry logic and exponential backoff.
    
    Args:
        func: Async function to execute
        *args: Function arguments
        config: Retry configuration
        **kwargs: Function keyword arguments
        
    Returns:
        Function result
        
    Raises:
        Last exception if all retries fail
    """
    config = config or RetryConfig()
    last_exception = None
    
    for attempt in range(config.max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            return func(*args, **kwargs)
            
        except config.retry_exceptions as e:
            last_exception = e
            
            if attempt == config.max_retries:
                logger.error(
                    f"All {config.max_retries} retries failed for {func.__name__}: {e}"
                )
                raise
            
            # Calculate delay with exponential backoff
            delay = min(
                config.base_delay * (config.exponential_base ** attempt),
                config.max_delay
            )
            
            # Add jitter
            if config.jitter:
                import random
                delay *= (0.5 + random.random())
            
            logger.warning(
                f"Retry {attempt + 1}/{config.max_retries} for {func.__name__} "
                f"after {delay:.2f}s - Error: {e}"
            )
            
            await asyncio.sleep(delay)
    
    raise last_exception


def retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    retry_exceptions: tuple = (Exception,)
):
    """
    Decorator to add retry logic with exponential backoff.
    
    Usage:
        @retry(max_retries=3, retry_exceptions=(ConnectionError,))
        async def fetch_data():
            ...
    """
    config = RetryConfig(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
        retry_exceptions=retry_exceptions
    )
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await retry_with_backoff(func, *args, config=config, **kwargs)
        return wrapper
    return decorator


async def with_timeout(
    func: Callable[..., T],
    *args,
    timeout_seconds: float = 30.0,
    **kwargs
) -> T:
    """
    Execute a function with a timeout.
    
    Args:
        func: Async function to execute
        timeout_seconds: Timeout in seconds
        *args: Function arguments
        **kwargs: Function keyword arguments
        
    Returns:
        Function result
        
    Raises:
        asyncio.TimeoutError if timeout exceeded
    """
    try:
        return await asyncio.wait_for(
            func(*args, **kwargs),
            timeout=timeout_seconds
        )
    except asyncio.TimeoutError:
        logger.error(f"Timeout after {timeout_seconds}s for {func.__name__}")
        raise ExternalServiceError(
            f"Operation timed out after {timeout_seconds} seconds"
        )


def timeout(seconds: float = 30.0):
    """
    Decorator to add timeout to an async function.
    
    Usage:
        @timeout(30.0)
        async def slow_operation():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await with_timeout(func, *args, timeout_seconds=seconds, **kwargs)
        return wrapper
    return decorator


# Pre-configured circuit breakers for common services
satellite_circuit = CircuitBreaker(
    "satellite_service",
    CircuitBreakerConfig(
        failure_threshold=3,
        timeout_seconds=120.0,
        success_threshold=2
    )
)

weather_circuit = CircuitBreaker(
    "weather_service",
    CircuitBreakerConfig(
        failure_threshold=5,
        timeout_seconds=60.0
    )
)

ai_circuit = CircuitBreaker(
    "ai_service",
    CircuitBreakerConfig(
        failure_threshold=3,
        timeout_seconds=90.0
    )
)

database_circuit = CircuitBreaker(
    "database",
    CircuitBreakerConfig(
        failure_threshold=5,
        timeout_seconds=30.0
    )
)

