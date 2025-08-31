"""
Weather Service for LARMMS

This service handles weather data integration using OpenWeatherMap API.
Provides current weather conditions and forecasts for farm locations.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import pyowm
from pyowm.owm import OWM
from pyowm.commons.exceptions import NotFoundError, UnauthorizedError, APIRequestError

from utils.caching import weather_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class WeatherCondition:
    """Data class for current weather conditions"""
    temperature: float  # Celsius
    humidity: float     # Percentage
    pressure: float     # hPa
    wind_speed: float   # m/s
    wind_direction: float  # degrees
    precipitation: float   # mm
    cloud_coverage: float  # percentage
    uv_index: Optional[float] = None
    visibility: Optional[float] = None  # km
    description: str = ""
    icon: str = ""
    timestamp: datetime = None


@dataclass
class WeatherForecast:
    """Data class for weather forecast"""
    date: datetime
    temperature_max: float
    temperature_min: float
    humidity: float
    precipitation: float
    precipitation_probability: float  # percentage
    wind_speed: float
    description: str
    icon: str


@dataclass
class AgriculturalWeatherData:
    """Comprehensive weather data for agricultural analysis"""
    location: Dict[str, float]  # lat, lon
    current: WeatherCondition
    forecast: List[WeatherForecast]  # 7-day forecast
    
    # Agricultural indices
    growing_degree_days: float
    chill_hours: float
    heat_stress_index: float
    drought_risk: str  # low, moderate, high
    frost_risk: str    # low, moderate, high
    
    # Seasonal summary
    seasonal_summary: Dict[str, Any]


class WeatherService:
    """Service for weather data processing using OpenWeatherMap API"""
    
    def __init__(self):
        """Initialize the weather service"""
        from config import settings
        self.api_key = settings.OPENWEATHER_API_KEY
        self.owm = None
        self.initialized = False
        self._setup_weather_api()
    
    def _setup_weather_api(self):
        """Initialize OpenWeatherMap API connection"""
        try:
            if not self.api_key:
                logger.warning("OpenWeatherMap API key not found. Weather service will use demo data.")
                self.initialized = False
                return
            
            # Clean and validate API key
            self.api_key = self.api_key.strip()
            logger.info(f"🔑 Weather API key length: {len(self.api_key)}")
            logger.info(f"🔑 Weather API key starts with: {self.api_key[:8]}...")
            
            self.owm = OWM(self.api_key)
            
            # Test the API connection
            mgr = self.owm.weather_manager()
            # Try a simple API call to validate the key
            mgr.weather_at_place("London,UK")
            
            self.initialized = True
            logger.info("OpenWeatherMap API initialized successfully")
            
        except UnauthorizedError:
            logger.error(f"Invalid OpenWeatherMap API key - key length: {len(self.api_key) if self.api_key else 0}")
            self.initialized = False
        except Exception as e:
            logger.warning(f"Weather API initialization failed: {e}")
            self.initialized = False
    
    def is_available(self) -> bool:
        """Check if the weather service is available"""
        return self.initialized
    
    def get_current_weather(self, latitude: float, longitude: float) -> Optional[WeatherCondition]:
        """
        Get current weather conditions for a location
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            
        Returns:
            WeatherCondition object or None if failed
        """
        try:
            # Check cache first
            cached_data = weather_cache.get_current_weather(latitude, longitude)
            if cached_data:
                logger.debug(f"Using cached weather data for {latitude}, {longitude}")
                return WeatherCondition(**cached_data)
            
            if not self.initialized:
                # Return demo data
                return self._get_demo_weather()
            
            # Get weather from API
            mgr = self.owm.weather_manager()
            observation = mgr.weather_at_coords(latitude, longitude)
            weather = observation.weather
            
            # Extract weather data
            temp_data = weather.temperature('celsius')
            wind_data = weather.wind()
            
            current_weather = WeatherCondition(
                temperature=temp_data.get('temp', 20.0),
                humidity=weather.humidity or 50.0,
                pressure=weather.pressure.get('press', 1013.25),
                wind_speed=wind_data.get('speed', 0.0),
                wind_direction=wind_data.get('deg', 0.0),
                precipitation=weather.rain.get('1h', 0.0) if weather.rain else 0.0,
                cloud_coverage=weather.clouds or 0.0,
                uv_index=None,  # Requires separate API call
                visibility=weather.visibility_distance,
                description=weather.detailed_status,
                icon=weather.weather_icon_name,
                timestamp=datetime.utcnow()
            )
            
            # Cache the result
            weather_cache.set_current_weather(
                latitude, longitude, 
                current_weather.__dict__
            )
            
            return current_weather
            
        except Exception as e:
            logger.error(f"Error getting current weather: {e}")
            return self._get_demo_weather()
    
    def get_weather_forecast(self, latitude: float, longitude: float, days: int = 7) -> List[WeatherForecast]:
        """
        Get weather forecast for a location
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            days: Number of days to forecast (max 5 for free API)
            
        Returns:
            List of WeatherForecast objects
        """
        try:
            # Check cache first
            cached_data = weather_cache.get_forecast(latitude, longitude, days)
            if cached_data:
                logger.debug(f"Using cached forecast data for {latitude}, {longitude}")
                return [WeatherForecast(**forecast) for forecast in cached_data]
            
            if not self.initialized:
                # Return demo forecast
                return self._get_demo_forecast(days)
            
            # Get forecast from API (free tier allows 5 days)
            forecast_days = min(days, 5)
            mgr = self.owm.weather_manager()
            forecast = mgr.forecast_at_coords(latitude, longitude, "3h")
            
            # Process forecast data
            daily_forecasts = []
            current_date = None
            daily_data = {}
            
            for weather in forecast.forecast:
                forecast_time = weather.reference_time('date')
                forecast_date = forecast_time.date()
                
                if current_date != forecast_date:
                    # Save previous day's data
                    if current_date and daily_data:
                        daily_forecasts.append(self._create_daily_forecast(current_date, daily_data))
                    
                    # Start new day
                    current_date = forecast_date
                    daily_data = {
                        'temps': [],
                        'humidity': [],
                        'precipitation': [],
                        'precipitation_prob': [],
                        'wind_speed': [],
                        'descriptions': [],
                        'icons': []
                    }
                
                # Collect data for the day
                temp_data = weather.temperature('celsius')
                daily_data['temps'].append(temp_data.get('temp', 20.0))
                daily_data['humidity'].append(weather.humidity or 50.0)
                daily_data['precipitation'].append(weather.rain.get('3h', 0.0) if weather.rain else 0.0)
                daily_data['precipitation_prob'].append(0.0)  # Not available in free tier
                daily_data['wind_speed'].append(weather.wind().get('speed', 0.0))
                daily_data['descriptions'].append(weather.detailed_status)
                daily_data['icons'].append(weather.weather_icon_name)
            
            # Add last day
            if current_date and daily_data:
                daily_forecasts.append(self._create_daily_forecast(current_date, daily_data))
            
            # Cache the result
            forecast_data = [forecast.__dict__ for forecast in daily_forecasts]
            weather_cache.set_forecast(latitude, longitude, forecast_data, days)
            
            return daily_forecasts
            
        except Exception as e:
            logger.error(f"Error getting weather forecast: {e}")
            return self._get_demo_forecast(days)
    
    def _create_daily_forecast(self, date, daily_data) -> WeatherForecast:
        """Create daily forecast from 3-hourly data"""
        return WeatherForecast(
            date=datetime.combine(date, datetime.min.time()),
            temperature_max=max(daily_data['temps']) if daily_data['temps'] else 25.0,
            temperature_min=min(daily_data['temps']) if daily_data['temps'] else 15.0,
            humidity=sum(daily_data['humidity']) / len(daily_data['humidity']) if daily_data['humidity'] else 50.0,
            precipitation=sum(daily_data['precipitation']) if daily_data['precipitation'] else 0.0,
            precipitation_probability=sum(daily_data['precipitation_prob']) / len(daily_data['precipitation_prob']) if daily_data['precipitation_prob'] else 20.0,
            wind_speed=sum(daily_data['wind_speed']) / len(daily_data['wind_speed']) if daily_data['wind_speed'] else 5.0,
            description=daily_data['descriptions'][0] if daily_data['descriptions'] else "Partly cloudy",
            icon=daily_data['icons'][0] if daily_data['icons'] else "02d"
        )
    
    def get_agricultural_weather_analysis(
        self, 
        latitude: float, 
        longitude: float,
        crop_type: str = "general"
    ) -> Optional[AgriculturalWeatherData]:
        """
        Get comprehensive weather analysis for agricultural purposes
        
        Args:
            latitude: Farm latitude
            longitude: Farm longitude
            crop_type: Type of crop for specialized analysis
            
        Returns:
            AgriculturalWeatherData object with comprehensive analysis
        """
        try:
            # Get current weather and forecast
            current = self.get_current_weather(latitude, longitude)
            forecast = self.get_weather_forecast(latitude, longitude, 7)
            
            if not current or not forecast:
                return None
            
            # Calculate agricultural indices
            growing_degree_days = self._calculate_growing_degree_days(current, forecast)
            chill_hours = self._calculate_chill_hours(forecast)
            heat_stress_index = self._calculate_heat_stress_index(current, forecast)
            drought_risk = self._assess_drought_risk(current, forecast)
            frost_risk = self._assess_frost_risk(current, forecast)
            
            # Create seasonal summary
            seasonal_summary = {
                "avg_temperature": sum(f.temperature_max + f.temperature_min for f in forecast) / (2 * len(forecast)),
                "total_precipitation": sum(f.precipitation for f in forecast),
                "avg_humidity": sum(f.humidity for f in forecast) / len(forecast),
                "avg_wind_speed": sum(f.wind_speed for f in forecast) / len(forecast),
                "optimal_conditions": growing_degree_days > 100 and drought_risk == "low" and frost_risk == "low"
            }
            
            return AgriculturalWeatherData(
                location={"lat": latitude, "lon": longitude},
                current=current,
                forecast=forecast,
                growing_degree_days=growing_degree_days,
                chill_hours=chill_hours,
                heat_stress_index=heat_stress_index,
                drought_risk=drought_risk,
                frost_risk=frost_risk,
                seasonal_summary=seasonal_summary
            )
            
        except Exception as e:
            logger.error(f"Error in agricultural weather analysis: {e}")
            return None
    
    def _calculate_growing_degree_days(self, current: WeatherCondition, forecast: List[WeatherForecast]) -> float:
        """Calculate Growing Degree Days (GDD) - accumulated heat units"""
        base_temp = 10.0  # Base temperature for most crops (Celsius)
        gdd = 0.0
        
        # Add current day
        daily_avg = current.temperature
        if daily_avg > base_temp:
            gdd += daily_avg - base_temp
        
        # Add forecast days
        for day in forecast:
            daily_avg = (day.temperature_max + day.temperature_min) / 2
            if daily_avg > base_temp:
                gdd += daily_avg - base_temp
        
        return round(gdd, 1)
    
    def _calculate_chill_hours(self, forecast: List[WeatherForecast]) -> float:
        """Calculate chill hours (hours below 7°C) - important for fruit trees"""
        chill_hours = 0.0
        
        for day in forecast:
            # Estimate hours below 7°C based on min temperature
            if day.temperature_min < 7.0:
                # Rough estimate: if min temp is below 7°C, assume 6-12 hours of chill
                chill_hours += max(0, 12 - (day.temperature_min + 7) / 2)
        
        return round(chill_hours, 1)
    
    def _calculate_heat_stress_index(self, current: WeatherCondition, forecast: List[WeatherForecast]) -> float:
        """Calculate heat stress index for crops"""
        stress_threshold = 30.0  # Temperature threshold for heat stress
        stress_index = 0.0
        
        # Current conditions
        if current.temperature > stress_threshold:
            stress_index += (current.temperature - stress_threshold) * 0.5
        
        # Forecast conditions
        for day in forecast:
            if day.temperature_max > stress_threshold:
                stress_index += (day.temperature_max - stress_threshold) * 0.3
        
        return round(stress_index, 1)
    
    def _assess_drought_risk(self, current: WeatherCondition, forecast: List[WeatherForecast]) -> str:
        """Assess drought risk based on precipitation and humidity"""
        total_precipitation = sum(f.precipitation for f in forecast)
        avg_humidity = (current.humidity + sum(f.humidity for f in forecast)) / (len(forecast) + 1)
        
        if total_precipitation < 5.0 and avg_humidity < 40:
            return "high"
        elif total_precipitation < 15.0 and avg_humidity < 60:
            return "moderate"
        else:
            return "low"
    
    def _assess_frost_risk(self, current: WeatherCondition, forecast: List[WeatherForecast]) -> str:
        """Assess frost risk based on temperature forecast"""
        frost_threshold = 2.0  # Celsius
        
        # Check current and forecast minimum temperatures
        min_temps = [current.temperature] + [f.temperature_min for f in forecast]
        
        if any(temp <= frost_threshold for temp in min_temps):
            return "high"
        elif any(temp <= frost_threshold + 3 for temp in min_temps):
            return "moderate"
        else:
            return "low"
    
    def _get_demo_weather(self) -> WeatherCondition:
        """Return demo weather data when API is not available"""
        return WeatherCondition(
            temperature=22.5,
            humidity=65.0,
            pressure=1013.25,
            wind_speed=3.5,
            wind_direction=180.0,
            precipitation=0.0,
            cloud_coverage=25.0,
            uv_index=6.0,
            visibility=10.0,
            description="partly cloudy",
            icon="02d",
            timestamp=datetime.utcnow()
        )
    
    def _get_demo_forecast(self, days: int) -> List[WeatherForecast]:
        """Return demo forecast data when API is not available"""
        forecasts = []
        base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        for i in range(days):
            forecasts.append(WeatherForecast(
                date=base_date + timedelta(days=i),
                temperature_max=25.0 + (i % 3) * 2,
                temperature_min=15.0 + (i % 3) * 2,
                humidity=60.0 + (i % 4) * 5,
                precipitation=0.5 if i % 3 == 0 else 0.0,
                precipitation_probability=30.0 if i % 3 == 0 else 10.0,
                wind_speed=4.0 + (i % 2) * 2,
                description="partly cloudy" if i % 2 == 0 else "sunny",
                icon="02d" if i % 2 == 0 else "01d"
            ))
        
        return forecasts


# Global service instance
weather_service = WeatherService()


def get_weather_service() -> WeatherService:
    """Get the global weather service instance"""
    return weather_service 