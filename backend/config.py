import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Environment
    ENVIRONMENT: str = Field(default="development", description="Environment (development, staging, production)")
    
    # Database
    DATABASE_URL: str = Field(default="", description="Supabase database URL")
    SUPABASE_URL: str = Field(default="", description="Supabase project URL")
    SUPABASE_ANON_KEY: str = Field(default="", description="Supabase anonymous key")
    SUPABASE_SERVICE_KEY: str = Field(default="", description="Supabase service role key")
    
    # External APIs
    GOOGLE_EARTH_ENGINE_KEY: str = Field(default="", description="Google Earth Engine API key")
    GOOGLE_EARTH_ENGINE_SERVICE_ACCOUNT: str = Field(default="", description="GEE service account email")
    GOOGLE_EARTH_ENGINE_PRIVATE_KEY: str = Field(default="", description="GEE private key")
    
    OPENWEATHER_API_KEY: str = Field(default="", description="OpenWeatherMap API key")
    ALPHA_VANTAGE_API_KEY: str = Field(default="", description="Alpha Vantage API key")
    COMMODITIES_API_KEY: str = Field(default="", description="Commodities API key (optional)")
    GOOGLE_EARTH_ENGINE_PROJECT_ID: str = Field(default="", description="Google Earth Engine project ID")
    
    # Supabase Configuration (for backend auth validation)
    SUPABASE_URL: str = Field(default="", description="Supabase project URL")
    SUPABASE_SERVICE_KEY: str = Field(default="", description="Supabase service role key")
    
    # Optional configuration
    SECRET_KEY: str = Field(default="dev-secret-key-change-in-production", description="Application secret key")
    CORS_ORIGINS: str = Field(default="http://localhost:3000", description="CORS allowed origins")
    DEBUG: str = Field(default="true", description="Debug mode")
    NODE_ENV: str = Field(default="development", description="Node environment")
    
    # AI APIs
    GOOGLE_GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key")
    ANTHROPIC_API_KEY: str = Field(default="", description="Anthropic Claude API key")
    
    # CORS
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        description="Comma-separated list of allowed CORS origins"
    )
    
    # Cache settings
    REDIS_URL: str = Field(default="redis://localhost:6379", description="Redis URL for caching")
    CACHE_TTL_HOURS: int = Field(default=24, description="Cache TTL in hours for satellite data")
    PRICE_CACHE_TTL_HOURS: int = Field(default=6, description="Cache TTL in hours for price data")
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="API rate limit per minute")
    
    # Monitoring & Error Tracking
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    ENABLE_METRICS: bool = Field(default=True, description="Enable metrics collection")
    SENTRY_DSN: str = Field(default="", description="Sentry DSN for error tracking")
    
    class Config:
        env_file = [".env", "../.env"]  # Check current dir first, then parent
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables

# Create settings instance
settings = Settings()

# Validation function
def validate_settings():
    """Validate that required settings are configured"""
    required_for_production = [
        "DATABASE_URL",
        "SUPABASE_URL", 
        "SUPABASE_ANON_KEY",
        "GOOGLE_GEMINI_API_KEY",
        "ANTHROPIC_API_KEY"
    ]
    
    if settings.ENVIRONMENT == "production":
        missing = []
        for setting in required_for_production:
            if not getattr(settings, setting):
                missing.append(setting)
        
        if missing:
            raise ValueError(f"Missing required production settings: {', '.join(missing)}")
    
    return True

# Validate on import
validate_settings() 