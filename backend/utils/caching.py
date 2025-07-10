"""
Caching Utilities for LARMMS

This module provides caching functionality for satellite data, weather information,
and crop price data to minimize external API calls and improve performance.
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Any, Optional, Dict
import os
import logging

logger = logging.getLogger(__name__)


class SimpleFileCache:
    """Simple file-based cache for development"""
    
    def __init__(self, cache_dir: str = "cache"):
        """Initialize cache with directory"""
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_path(self, key: str) -> str:
        """Generate cache file path from key"""
        # Create a safe filename from the key
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{safe_key}.json")
    
    def get(self, key: str, max_age_hours: int = 24) -> Optional[Any]:
        """
        Get value from cache if it exists and is not expired
        
        Args:
            key: Cache key
            max_age_hours: Maximum age in hours before cache expires
            
        Returns:
            Cached value or None if not found/expired
        """
        try:
            cache_path = self._get_cache_path(key)
            
            if not os.path.exists(cache_path):
                return None
            
            # Check if cache is expired
            file_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
            if datetime.now() - file_time > timedelta(hours=max_age_hours):
                # Remove expired cache
                os.remove(cache_path)
                return None
            
            # Load and return cached data
            with open(cache_path, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.warning(f"Error reading cache for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any) -> bool:
        """
        Store value in cache
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_path = self._get_cache_path(key)
            
            with open(cache_path, 'w') as f:
                json.dump(value, f, default=str)  # default=str for datetime serialization
            
            return True
            
        except Exception as e:
            logger.error(f"Error writing cache for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete cached value"""
        try:
            cache_path = self._get_cache_path(key)
            if os.path.exists(cache_path):
                os.remove(cache_path)
            return True
        except Exception as e:
            logger.error(f"Error deleting cache for key {key}: {e}")
            return False
    
    def clear_expired(self, max_age_hours: int = 24):
        """Clear all expired cache files"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.cache_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    
                    if file_time < cutoff_time:
                        os.remove(filepath)
                        logger.debug(f"Removed expired cache file: {filename}")
                        
        except Exception as e:
            logger.error(f"Error clearing expired cache: {e}")


class SatelliteDataCache:
    """Specialized cache for satellite data"""
    
    def __init__(self, cache: SimpleFileCache):
        self.cache = cache
    
    def get_satellite_data(self, latitude: float, longitude: float, date_range_days: int = 30) -> Optional[Dict]:
        """Get cached satellite data for a farm location"""
        # Create unique key based on location and date range
        key = f"satellite_{latitude:.6f}_{longitude:.6f}_{date_range_days}"
        
        # Cache satellite data for 12 hours (satellite data doesn't change frequently)
        return self.cache.get(key, max_age_hours=12)
    
    def set_satellite_data(self, latitude: float, longitude: float, data: Dict, date_range_days: int = 30) -> bool:
        """Cache satellite data for a farm location"""
        key = f"satellite_{latitude:.6f}_{longitude:.6f}_{date_range_days}"
        return self.cache.set(key, data)
    
    def get_historical_data(self, latitude: float, longitude: float, months: int = 12) -> Optional[Dict]:
        """Get cached historical satellite data"""
        key = f"historical_{latitude:.6f}_{longitude:.6f}_{months}"
        
        # Cache historical data for 24 hours
        return self.cache.get(key, max_age_hours=24)
    
    def set_historical_data(self, latitude: float, longitude: float, data: Dict, months: int = 12) -> bool:
        """Cache historical satellite data"""
        key = f"historical_{latitude:.6f}_{longitude:.6f}_{months}"
        return self.cache.set(key, data)


class WeatherDataCache:
    """Specialized cache for weather data"""
    
    def __init__(self, cache: SimpleFileCache):
        self.cache = cache
    
    def get_current_weather(self, latitude: float, longitude: float) -> Optional[Dict]:
        """Get cached current weather data"""
        key = f"weather_current_{latitude:.4f}_{longitude:.4f}"
        
        # Cache current weather for 1 hour
        return self.cache.get(key, max_age_hours=1)
    
    def set_current_weather(self, latitude: float, longitude: float, data: Dict) -> bool:
        """Cache current weather data"""
        key = f"weather_current_{latitude:.4f}_{longitude:.4f}"
        return self.cache.set(key, data)
    
    def get_forecast(self, latitude: float, longitude: float, days: int = 7) -> Optional[Dict]:
        """Get cached weather forecast"""
        key = f"weather_forecast_{latitude:.4f}_{longitude:.4f}_{days}"
        
        # Cache forecast for 6 hours
        return self.cache.get(key, max_age_hours=6)
    
    def set_forecast(self, latitude: float, longitude: float, data: Dict, days: int = 7) -> bool:
        """Cache weather forecast"""
        key = f"weather_forecast_{latitude:.4f}_{longitude:.4f}_{days}"
        return self.cache.set(key, data)


class CropPriceCache:
    """Specialized cache for crop price data"""
    
    def __init__(self, cache: SimpleFileCache):
        self.cache = cache
    
    def get_crop_prices(self, crop_type: str, region: str = "global") -> Optional[Dict]:
        """Get cached crop price data"""
        key = f"prices_{crop_type}_{region}"
        
        # Cache crop prices for 4 hours (markets change frequently)
        return self.cache.get(key, max_age_hours=4)
    
    def set_crop_prices(self, crop_type: str, data: Dict, region: str = "global") -> bool:
        """Cache crop price data"""
        key = f"prices_{crop_type}_{region}"
        return self.cache.set(key, data)
    
    def get_price_history(self, crop_type: str, months: int = 12, region: str = "global") -> Optional[Dict]:
        """Get cached historical price data"""
        key = f"price_history_{crop_type}_{region}_{months}"
        
        # Cache price history for 24 hours
        return self.cache.get(key, max_age_hours=24)
    
    def set_price_history(self, crop_type: str, data: Dict, months: int = 12, region: str = "global") -> bool:
        """Cache historical price data"""
        key = f"price_history_{crop_type}_{region}_{months}"
        return self.cache.set(key, data)


# Global cache instances
_base_cache = SimpleFileCache()
satellite_cache = SatelliteDataCache(_base_cache)
weather_cache = WeatherDataCache(_base_cache)
crop_price_cache = CropPriceCache(_base_cache)


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    cache_dir = _base_cache.cache_dir
    
    if not os.path.exists(cache_dir):
        return {"total_files": 0, "total_size_mb": 0}
    
    total_files = 0
    total_size = 0
    
    for filename in os.listdir(cache_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(cache_dir, filename)
            total_files += 1
            total_size += os.path.getsize(filepath)
    
    return {
        "total_files": total_files,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "cache_directory": cache_dir
    }


def clear_all_cache():
    """Clear all cached data"""
    try:
        cache_dir = _base_cache.cache_dir
        for filename in os.listdir(cache_dir):
            if filename.endswith('.json'):
                os.remove(os.path.join(cache_dir, filename))
        logger.info("All cache cleared successfully")
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")


def cleanup_expired_cache():
    """Clean up expired cache files (run periodically)"""
    _base_cache.clear_expired(max_age_hours=48)  # Remove files older than 48 hours 