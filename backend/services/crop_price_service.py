"""
Crop Price Service for LARMMS

This service handles crop price data integration using various agricultural APIs
to provide current market prices, historical trends, and price forecasts.
"""

import os
import logging
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json

from utils.caching import crop_price_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CropPrice:
    """Data class for crop price information"""
    crop_type: str
    price: float  # Price per unit (e.g., per bushel, per ton)
    unit: str     # Unit of measurement
    currency: str # Currency code (USD, EUR, etc.)
    market: str   # Market/exchange name
    timestamp: datetime
    change_24h: Optional[float] = None  # 24-hour price change percentage
    volume: Optional[float] = None      # Trading volume


@dataclass
class PriceHistory:
    """Historical price data"""
    crop_type: str
    prices: List[Dict[str, Any]]  # List of {date, price, volume}
    period: str  # daily, weekly, monthly
    average_price: float
    volatility: float  # Price volatility indicator
    trend: str   # upward, downward, stable


@dataclass
class MarketAnalysis:
    """Comprehensive market analysis for a crop"""
    crop_type: str
    current_price: CropPrice
    price_history: PriceHistory
    
    # Market indicators
    market_sentiment: str  # bullish, bearish, neutral
    supply_demand_balance: str  # surplus, balanced, shortage
    seasonal_patterns: Dict[str, Any]
    
    # Price forecasts
    short_term_forecast: Dict[str, float]  # 1 week, 1 month
    long_term_outlook: str
    
    # Risk factors
    risk_factors: List[str]
    opportunities: List[str]


class CropPriceService:
    """Service for crop price data and market analysis"""
    
    # Crop type mappings for different APIs
    CROP_MAPPINGS = {
        "corn": ["corn", "maize", "CORN"],
        "soybeans": ["soybeans", "soy", "SOYBEANS"],
        "wheat": ["wheat", "WHEAT"],
        "rice": ["rice", "RICE"],
        "cotton": ["cotton", "COTTON"],
        "sugar": ["sugar", "SUGAR"],
        "coffee": ["coffee", "COFFEE"],
        "cocoa": ["cocoa", "COCOA"],
        "oats": ["oats", "OATS"],
        "barley": ["barley", "BARLEY"],
        "canola": ["canola", "rapeseed", "CANOLA"],
        "sunflower": ["sunflower", "SUNFLOWER"],
        "potatoes": ["potatoes", "POTATOES"],
        "tomatoes": ["tomatoes", "TOMATOES"],
        "apples": ["apples", "APPLES"],
        "oranges": ["oranges", "ORANGES"],
        "beef": ["cattle", "beef", "CATTLE"],
        "pork": ["hogs", "pork", "HOGS"]
    }
    
    def __init__(self):
        """Initialize the crop price service"""
        from config import settings
        self.apis = {
            "alpha_vantage": settings.ALPHA_VANTAGE_API_KEY,
            "commodities_api": settings.COMMODITIES_API_KEY,  # Optional
            "quandl_api": getattr(settings, 'QUANDL_API_KEY', '')  # Optional, may not be in config
        }
        self.initialized = any(key for key in self.apis.values())
        
        if not self.initialized:
            logger.warning("No crop price API keys found. Service will use demo data.")
        else:
            available_apis = [name for name, key in self.apis.items() if key]
            logger.info(f"✅ Crop price service initialized with APIs: {', '.join(available_apis)}")
    
    def is_available(self) -> bool:
        """Check if the crop price service is available"""
        return True  # Always available with demo data fallback
    
    async def get_current_price(self, crop_type: str, region: str = "US") -> Optional[CropPrice]:
        """
        Get current market price for a crop
        
        Args:
            crop_type: Type of crop (e.g., "corn", "soybeans")
            region: Market region (e.g., "US", "EU", "GLOBAL")
            
        Returns:
            CropPrice object with current market data
        """
        try:
            # Check cache first
            cached_data = crop_price_cache.get_crop_prices(crop_type, region)
            if cached_data:
                logger.debug(f"Using cached price data for {crop_type}")
                return CropPrice(**cached_data)
            
            # Normalize crop type
            normalized_crop = self._normalize_crop_type(crop_type)
            
            if not self.initialized:
                # Return demo data
                price_data = self._get_demo_price(normalized_crop, region)
            else:
                # Try to get from available APIs
                price_data = await self._fetch_from_apis(normalized_crop, region)
                
                if not price_data:
                    price_data = self._get_demo_price(normalized_crop, region)
            
            # Cache the result
            if price_data:
                crop_price_cache.set_crop_prices(crop_type, price_data.__dict__, region)
            
            return price_data
            
        except Exception as e:
            logger.error(f"Error getting crop price for {crop_type}: {e}")
            return self._get_demo_price(crop_type, region)
    
    async def get_price_history(
        self, 
        crop_type: str, 
        months: int = 12, 
        region: str = "US"
    ) -> Optional[PriceHistory]:
        """
        Get historical price data for a crop
        
        Args:
            crop_type: Type of crop
            months: Number of months of history
            region: Market region
            
        Returns:
            PriceHistory object with historical data and analysis
        """
        try:
            # Check cache first
            cached_data = crop_price_cache.get_price_history(crop_type, months, region)
            if cached_data:
                logger.debug(f"Using cached price history for {crop_type}")
                return PriceHistory(**cached_data)
            
            normalized_crop = self._normalize_crop_type(crop_type)
            
            if not self.initialized:
                history_data = self._get_demo_history(normalized_crop, months)
            else:
                history_data = await self._fetch_history_from_apis(normalized_crop, months, region)
                
                if not history_data:
                    history_data = self._get_demo_history(normalized_crop, months)
            
            # Cache the result
            if history_data:
                crop_price_cache.set_price_history(crop_type, history_data.__dict__, months, region)
            
            return history_data
            
        except Exception as e:
            logger.error(f"Error getting price history for {crop_type}: {e}")
            return self._get_demo_history(crop_type, months)
    
    async def get_market_analysis(
        self, 
        crop_type: str, 
        region: str = "US"
    ) -> Optional[MarketAnalysis]:
        """
        Get comprehensive market analysis for a crop
        
        Args:
            crop_type: Type of crop
            region: Market region
            
        Returns:
            MarketAnalysis object with comprehensive market data
        """
        try:
            # Get current price and history
            current_price = await self.get_current_price(crop_type, region)
            price_history = await self.get_price_history(crop_type, 12, region)
            
            if not current_price or not price_history:
                return None
            
            # Analyze market sentiment
            market_sentiment = self._analyze_market_sentiment(price_history)
            supply_demand = self._analyze_supply_demand(current_price, price_history)
            seasonal_patterns = self._analyze_seasonal_patterns(price_history)
            
            # Generate forecasts
            short_term_forecast = self._generate_short_term_forecast(current_price, price_history)
            long_term_outlook = self._generate_long_term_outlook(price_history, market_sentiment)
            
            # Identify risks and opportunities
            risk_factors = self._identify_risk_factors(crop_type, current_price, price_history)
            opportunities = self._identify_opportunities(crop_type, current_price, price_history)
            
            return MarketAnalysis(
                crop_type=crop_type,
                current_price=current_price,
                price_history=price_history,
                market_sentiment=market_sentiment,
                supply_demand_balance=supply_demand,
                seasonal_patterns=seasonal_patterns,
                short_term_forecast=short_term_forecast,
                long_term_outlook=long_term_outlook,
                risk_factors=risk_factors,
                opportunities=opportunities
            )
            
        except Exception as e:
            logger.error(f"Error in market analysis for {crop_type}: {e}")
            return None
    
    def _normalize_crop_type(self, crop_type: str) -> str:
        """Normalize crop type to standard format"""
        crop_lower = crop_type.lower().strip()
        
        for standard_name, aliases in self.CROP_MAPPINGS.items():
            if crop_lower in [alias.lower() for alias in aliases]:
                return standard_name
        
        return crop_lower
    
    async def _fetch_from_apis(self, crop_type: str, region: str) -> Optional[CropPrice]:
        """Fetch price data from available APIs"""
        # Try Commodities API first
        if self.apis["commodities_api"]:
            try:
                return await self._fetch_from_commodities_api(crop_type, region)
            except Exception as e:
                logger.debug(f"Commodities API failed: {e}")
        
        # Try Alpha Vantage API
        if self.apis["alpha_vantage"]:
            try:
                return await self._fetch_from_alpha_vantage(crop_type, region)
            except Exception as e:
                logger.debug(f"Alpha Vantage API failed: {e}")
        
        # Try other APIs as fallback
        # Add more API integrations here as needed
        
        return None
    
    async def _fetch_from_commodities_api(self, crop_type: str, region: str) -> Optional[CropPrice]:
        """Fetch data from Commodities API"""
        # This is a placeholder implementation
        # In a real implementation, you would make HTTP requests to the actual API
        logger.debug(f"Would fetch {crop_type} price from Commodities API")
        return None
    
    async def _fetch_history_from_apis(self, crop_type: str, months: int, region: str) -> Optional[PriceHistory]:
        """Fetch historical data from available APIs"""
        # Placeholder for API historical data fetching
        return None
    
    async def _fetch_from_alpha_vantage(self, crop_type: str, region: str) -> Optional[CropPrice]:
        """Fetch commodity price from Alpha Vantage API"""
        try:
            api_key = self.apis["alpha_vantage"]
            if not api_key:
                return None
            
            # Alpha Vantage commodity symbols mapping (using futures symbols)
            commodity_symbols = {
                "corn": "ZC=F",  # Corn futures
                "soybeans": "ZS=F",  # Soybean futures
                "wheat": "ZW=F",  # Wheat futures  
                "coffee": "KC=F",  # Coffee futures
                "sugar": "SB=F",  # Sugar futures
                "cotton": "CT=F",  # Cotton futures
                "cattle": "LC=F",  # Live cattle futures
                "oil": "CRUDE_OIL",  # Use WTI function
                "natural_gas": "NATURAL_GAS"  # Use separate function
            }
            
            symbol = commodity_symbols.get(crop_type.lower())
            if not symbol:
                logger.warning(f"No Alpha Vantage symbol mapping for crop: {crop_type}")
                return None
            
            # Alpha Vantage commodities endpoint - using TIME_SERIES_DAILY for commodities
            url = f"https://www.alphavantage.co/query"
            params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": f"{symbol}",  # Use commodity symbol
                "apikey": api_key,
                "outputsize": "compact"
            }
            
            # For energy commodities, use different function
            if symbol in ["CRUDE_OIL", "NATURAL_GAS"]:
                params["function"] = "WTI"  # For oil
                del params["symbol"]  # WTI doesn't need symbol
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Check for API errors
                if "Error Message" in data:
                    logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                    return None
                
                if "Information" in data:
                    logger.warning(f"Alpha Vantage API info: {data['Information']}")
                    return None
                
                # Parse the response based on function used
                if "Time Series (Daily)" in data:
                    time_series = data["Time Series (Daily)"]
                    if time_series:
                        # Get the most recent date
                        latest_date = max(time_series.keys())
                        latest_data = time_series[latest_date]
                        price = float(latest_data.get("4. close", 0))
                        
                        return CropPrice(
                            crop_type=crop_type,
                            price=price,
                            unit="USD/unit",
                            currency="USD",
                            market=f"Alpha Vantage ({region})",
                            timestamp=datetime.utcnow(),
                            change_24h=None,
                            volume=float(latest_data.get("5. volume", 0))
                        )
                elif "data" in data and data["data"]:
                    # For WTI oil data
                    latest_data = data["data"][0] if isinstance(data["data"], list) else data["data"]
                    price = float(latest_data.get("value", 0))
                    
                    return CropPrice(
                        crop_type=crop_type,
                        price=price,
                        unit="USD/barrel",
                        currency="USD",
                        market=f"Alpha Vantage ({region})",
                        timestamp=datetime.utcnow(),
                        change_24h=None,
                        volume=None
                    )
                
                logger.warning(f"Unexpected Alpha Vantage response structure for {crop_type}: {list(data.keys())}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching from Alpha Vantage: {e}")
            return None
    
    def _get_demo_price(self, crop_type: str, region: str) -> CropPrice:
        """Generate demo price data"""
        # Base prices for different crops (USD per standard unit)
        base_prices = {
            "corn": {"price": 5.80, "unit": "bushel"},
            "soybeans": {"price": 13.50, "unit": "bushel"},
            "wheat": {"price": 7.20, "unit": "bushel"},
            "rice": {"price": 650.0, "unit": "ton"},
            "cotton": {"price": 0.75, "unit": "pound"},
            "sugar": {"price": 0.18, "unit": "pound"},
            "coffee": {"price": 1.85, "unit": "pound"},
            "cocoa": {"price": 2.45, "unit": "pound"},
            "oats": {"price": 4.10, "unit": "bushel"},
            "barley": {"price": 5.50, "unit": "bushel"},
            "canola": {"price": 580.0, "unit": "ton"},
            "potatoes": {"price": 220.0, "unit": "ton"},
            "tomatoes": {"price": 1200.0, "unit": "ton"},
            "apples": {"price": 800.0, "unit": "ton"},
            "beef": {"price": 6.50, "unit": "pound"},
            "pork": {"price": 4.20, "unit": "pound"}
        }
        
        crop_data = base_prices.get(crop_type, {"price": 100.0, "unit": "ton"})
        
        # Add some realistic variation
        import random
        variation = random.uniform(-0.1, 0.1)  # ±10% variation
        current_price = crop_data["price"] * (1 + variation)
        
        return CropPrice(
            crop_type=crop_type,
            price=round(current_price, 2),
            unit=crop_data["unit"],
            currency="USD",
            market=f"{region} Market",
            timestamp=datetime.utcnow(),
            change_24h=round(variation * 100, 2),  # Convert to percentage
            volume=random.uniform(1000, 10000)
        )
    
    def _get_demo_history(self, crop_type: str, months: int) -> PriceHistory:
        """Generate demo historical price data"""
        import random
        import math
        
        base_price = self._get_demo_price(crop_type, "US").price
        prices = []
        
        # Generate monthly price history
        for i in range(months):
            date = datetime.now() - timedelta(days=30 * i)
            
            # Add seasonal and trend variations
            seasonal_factor = 1 + 0.1 * math.sin(2 * math.pi * i / 12)  # Annual cycle
            trend_factor = 1 + 0.02 * (months - i) / months  # Slight upward trend
            noise = random.uniform(0.9, 1.1)  # Random variation
            
            price = base_price * seasonal_factor * trend_factor * noise
            volume = random.uniform(5000, 15000)
            
            prices.append({
                "date": date.isoformat(),
                "price": round(price, 2),
                "volume": round(volume, 0)
            })
        
        # Calculate statistics
        price_values = [p["price"] for p in prices]
        average_price = sum(price_values) / len(price_values)
        
        # Simple volatility calculation (standard deviation)
        variance = sum((p - average_price) ** 2 for p in price_values) / len(price_values)
        volatility = (variance ** 0.5) / average_price * 100  # As percentage
        
        # Determine trend
        if price_values[0] > price_values[-1] * 1.05:
            trend = "upward"
        elif price_values[0] < price_values[-1] * 0.95:
            trend = "downward"
        else:
            trend = "stable"
        
        return PriceHistory(
            crop_type=crop_type,
            prices=list(reversed(prices)),  # Chronological order
            period="monthly",
            average_price=round(average_price, 2),
            volatility=round(volatility, 2),
            trend=trend
        )
    
    def _analyze_market_sentiment(self, history: PriceHistory) -> str:
        """Analyze market sentiment based on price trends"""
        if history.trend == "upward" and history.volatility < 15:
            return "bullish"
        elif history.trend == "downward" and history.volatility < 15:
            return "bearish"
        elif history.volatility > 25:
            return "volatile"
        else:
            return "neutral"
    
    def _analyze_supply_demand(self, current: CropPrice, history: PriceHistory) -> str:
        """Analyze supply-demand balance"""
        if current.price > history.average_price * 1.15:
            return "shortage"
        elif current.price < history.average_price * 0.85:
            return "surplus"
        else:
            return "balanced"
    
    def _analyze_seasonal_patterns(self, history: PriceHistory) -> Dict[str, Any]:
        """Analyze seasonal price patterns"""
        return {
            "peak_season": "harvest_time",
            "low_season": "planting_time",
            "seasonal_variance": round(history.volatility / 2, 1),
            "pattern_strength": "moderate"
        }
    
    def _generate_short_term_forecast(self, current: CropPrice, history: PriceHistory) -> Dict[str, float]:
        """Generate short-term price forecasts"""
        base_price = current.price
        
        # Simple forecast based on trend
        if history.trend == "upward":
            week_forecast = base_price * 1.02
            month_forecast = base_price * 1.05
        elif history.trend == "downward":
            week_forecast = base_price * 0.98
            month_forecast = base_price * 0.95
        else:
            week_forecast = base_price * 1.01
            month_forecast = base_price * 1.01
        
        return {
            "1_week": round(week_forecast, 2),
            "1_month": round(month_forecast, 2)
        }
    
    def _generate_long_term_outlook(self, history: PriceHistory, sentiment: str) -> str:
        """Generate long-term market outlook"""
        if sentiment == "bullish" and history.trend == "upward":
            return "Positive long-term outlook with continued growth expected"
        elif sentiment == "bearish" and history.trend == "downward":
            return "Challenging conditions expected, prices may remain under pressure"
        elif sentiment == "volatile":
            return "Uncertain outlook with high volatility expected to continue"
        else:
            return "Stable market conditions expected with moderate price movements"
    
    def _identify_risk_factors(self, crop_type: str, current: CropPrice, history: PriceHistory) -> List[str]:
        """Identify market risk factors"""
        risks = []
        
        if history.volatility > 20:
            risks.append("High price volatility")
        
        if current.change_24h and abs(current.change_24h) > 5:
            risks.append("Recent sharp price movements")
        
        if history.trend == "downward":
            risks.append("Declining price trend")
        
        # Crop-specific risks
        weather_sensitive_crops = ["corn", "soybeans", "wheat", "rice", "cotton"]
        if crop_type in weather_sensitive_crops:
            risks.append("Weather-dependent production")
        
        return risks
    
    def _identify_opportunities(self, crop_type: str, current: CropPrice, history: PriceHistory) -> List[str]:
        """Identify market opportunities"""
        opportunities = []
        
        if history.trend == "upward":
            opportunities.append("Rising price trend")
        
        if current.price < history.average_price * 0.9:
            opportunities.append("Below-average pricing presents buying opportunity")
        
        if history.volatility < 10:
            opportunities.append("Stable market conditions")
        
        # Seasonal opportunities
        opportunities.append("Seasonal price patterns may provide timing advantages")
        
        return opportunities


# Global service instance
crop_price_service = CropPriceService()


def get_crop_price_service() -> CropPriceService:
    """Get the global crop price service instance"""
    return crop_price_service 