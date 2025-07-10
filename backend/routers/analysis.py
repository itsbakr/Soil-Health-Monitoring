from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid
import logging

from routers.auth import get_current_user_id
from services.satellite_service import get_satellite_service, FarmCoordinates, SatelliteData
from services.weather_service import get_weather_service
from services.crop_price_service import get_crop_price_service
from services.soil_health_agent import soil_health_agent
from services.roi_agent import roi_agent
from services.ai_config import ai_config
from utils.satellite_calculations import (
    classify_vegetation_health, 
    calculate_soil_salinity_level,
    estimate_soil_moisture,
    calculate_ndvi_trend
)
from utils.caching import satellite_cache

router = APIRouter()

# Configure logging
logger = logging.getLogger(__name__)

# In-memory storage for analysis results (in production, use database)
analysis_results = {}

# Background task functions
async def process_soil_health_analysis(analysis_id: str, farm_id: str, farm_coords: FarmCoordinates, include_historical: bool = True):
    """Background task to process comprehensive soil health analysis using satellite, weather, and market data"""
    import time
    
    analysis_start = time.time()
    analysis_short_id = analysis_id[:8]
    
    try:
        logger.info(f"🚀 [ANALYSIS-{analysis_short_id}] Starting comprehensive analysis for farm {farm_id}")
        
        # Update status to in progress
        if analysis_id in analysis_results:
            analysis_results[analysis_id]["status"] = "in_progress"
        
        # Get all services - timing each
        service_start = time.time()
        satellite_service = get_satellite_service()
        weather_service = get_weather_service()
        crop_price_service = get_crop_price_service()
        logger.info(f"⚡ [ANALYSIS-{analysis_short_id}] Services initialized in {time.time() - service_start:.2f}s")
        
        if not satellite_service.is_available():
            logger.warning(f"📡 [ANALYSIS-{analysis_short_id}] Satellite service not available, using demo data")
        
        # Get current satellite data
        sat_start = time.time()
        current_data = satellite_service.get_farm_satellite_data(farm_coords)
        logger.info(f"🛰️ [ANALYSIS-{analysis_short_id}] Satellite data retrieved in {time.time() - sat_start:.2f}s")
        
        if not current_data:
            logger.warning(f"⚠️ [ANALYSIS-{analysis_short_id}] No satellite data available for farm {farm_id}, using fallback")
            # Use placeholder data for demo
            current_data = SatelliteData(
                farm_id=farm_id,
                date_captured=datetime.now(),
                cloud_coverage=15.0,
                ndvi=0.65, ndwi=0.15, savi=0.58, evi=0.42, ndmi=0.35,
                bsi=0.12, si=0.08, ci=1.2, bi=0.25,
                surface_temperature=22.5, moisture_estimate=35.0,
                pixel_count=100, valid_pixels=90, data_quality_score=85.0
            )
        
        # Get weather analysis
        weather_start = time.time()
        weather_data = weather_service.get_agricultural_weather_analysis(
            farm_coords.latitude, 
            farm_coords.longitude,
            "general"  # Default crop type - could be enhanced with actual crop data
        )
        logger.info(f"🌤️ [ANALYSIS-{analysis_short_id}] Weather analysis completed in {time.time() - weather_start:.2f}s")
        
        # Get market analysis for common crops
        market_start = time.time()
        corn_prices = await crop_price_service.get_market_analysis("corn")
        logger.info(f"🌽 [ANALYSIS-{analysis_short_id}] Corn market data retrieved in {time.time() - market_start:.2f}s")
        
        soy_start = time.time()
        soybean_prices = await crop_price_service.get_market_analysis("soybeans")
        logger.info(f"🫘 [ANALYSIS-{analysis_short_id}] Soybean market data retrieved in {time.time() - soy_start:.2f}s")
        
        wheat_start = time.time()
        wheat_prices = await crop_price_service.get_market_analysis("wheat")
        logger.info(f"🌾 [ANALYSIS-{analysis_short_id}] Wheat market data retrieved in {time.time() - wheat_start:.2f}s")
        
        # Get historical data if requested
        historical_data = []
        trend_analysis = None
        
        if include_historical:
            historical_data = satellite_service.get_historical_data(farm_coords, months_back=6)
            if historical_data:
                ndvi_values = [data.ndvi for data in historical_data]
                dates = [data.date_captured for data in historical_data]
                trend_stats = calculate_ndvi_trend(ndvi_values, dates)
                trend_analysis = f"NDVI trend shows {trend_stats['improvement']:.1f}% change over 6 months"
        
        # Classify vegetation health
        vegetation_health = classify_vegetation_health(current_data.ndvi)
        
        # Calculate soil indicators
        salinity_info = calculate_soil_salinity_level(current_data.si)
        moisture_info = estimate_soil_moisture(current_data.ndmi)
        
        # Prepare comprehensive farm data for AI analysis
        farm_analysis_data = {
            "farm_id": farm_id,
            "size_acres": 100,  # Would get from database
            "current_crop": "corn",  # Would get from database
            "location": f"{farm_coords.latitude:.4f}, {farm_coords.longitude:.4f}",
            "soil_analysis": {
                "ndvi": current_data.ndvi,
                "ndwi": current_data.ndwi,
                "savi": current_data.savi,
                "evi": current_data.evi,
                "ndmi": current_data.ndmi,
                "bsi": current_data.bsi,
                "si": current_data.si,
                "ci": current_data.ci,
                "bi": current_data.bi,
                "ph_estimate": 6.8,  # Would calculate from spectral data
                "salinity_estimate": current_data.si / 10,  # Normalized estimate
                "moisture_content": current_data.ndmi,
                "land_surface_temp": current_data.surface_temperature
            },
            "weather_data": {
                "current": {
                    "temperature": weather_data.current.temperature,
                    "humidity": weather_data.current.humidity,
                    "precipitation": weather_data.current.precipitation,
                    "description": weather_data.current.description,
                    "pressure": weather_data.current.pressure,
                    "wind_speed": weather_data.current.wind_speed,
                    "cloud_coverage": weather_data.current.cloud_coverage
                },
                "location": weather_data.location,
                "growing_degree_days": weather_data.growing_degree_days,
                "drought_risk": weather_data.drought_risk,
                "frost_risk": weather_data.frost_risk,
                "heat_stress_index": weather_data.heat_stress_index
            } if weather_data else {},
            "market_data": {
                "corn": {
                    "current_price": corn_prices.current_price.__dict__ if corn_prices and corn_prices.current_price else {},
                    "market_sentiment": corn_prices.market_sentiment if corn_prices else None,
                    "trend": corn_prices.price_history.trend if corn_prices and corn_prices.price_history else None
                } if corn_prices else {},
                "soybeans": {
                    "current_price": soybean_prices.current_price.__dict__ if soybean_prices and soybean_prices.current_price else {},
                    "market_sentiment": soybean_prices.market_sentiment if soybean_prices else None,
                    "trend": soybean_prices.price_history.trend if soybean_prices and soybean_prices.price_history else None
                } if soybean_prices else {},
                "wheat": {
                    "current_price": wheat_prices.current_price.__dict__ if wheat_prices and wheat_prices.current_price else {},
                    "market_sentiment": wheat_prices.market_sentiment if wheat_prices else None,
                    "trend": wheat_prices.price_history.trend if wheat_prices and wheat_prices.price_history else None
                } if wheat_prices else {}
            },
            "historical_data": historical_data
        }
        
        # Use AI agents for sophisticated analysis
        ai_start = time.time()
        logger.info(f"🤖 [ANALYSIS-{analysis_short_id}] Running AI-powered soil health analysis...")
        soil_health_report = await soil_health_agent.analyze_soil_health(farm_analysis_data)
        ai_duration = time.time() - ai_start
        
        # Extract results from AI analysis
        health_score = soil_health_report.overall_score
        overall_health = soil_health_report.health_status.lower()
        deficiencies = [def_item.get("issue", str(def_item)) for def_item in soil_health_report.deficiencies]
        recommendations = [rec.get("description", str(rec)) for rec in soil_health_report.recommendations]
        summary = soil_health_report.farmer_summary or soil_health_report.explanation[:200] + "..."
        
        logger.info(f"🧠 [ANALYSIS-{analysis_short_id}] AI analysis completed in {ai_duration:.2f}s - Health Score: {health_score:.1f}, Status: {overall_health}")
        
        # Update analysis result with enhanced data
        if analysis_id in analysis_results:
            analysis_results[analysis_id].update({
                "status": "completed",
                "confidence_score": current_data.data_quality_score / 100.0,  # Convert from 0-100 to 0-1
                "overall_health": overall_health,
                "soil_indicators": {
                    "ph_level": 6.8,  # Placeholder - would need additional sensors
                    "salinity": current_data.si,
                    "moisture_content": moisture_info['percentage'],
                    "temperature": current_data.surface_temperature,
                    "organic_matter": max(0, (current_data.ci + 1) * 2.5)  # Rough estimate from CI
                },
                "vegetation_indices": {
                    "ndvi": current_data.ndvi,
                    "ndwi": current_data.ndwi,
                    "savi": current_data.savi,
                    "evi": current_data.evi,
                    "ndmi": current_data.ndmi
                },
                "soil_condition_indices": {
                    "bsi": current_data.bsi,
                    "si": current_data.si,
                    "ci": current_data.ci,
                    "bi": current_data.bi
                },
                "weather_data": {
                    "current_conditions": {
                        "temperature": weather_data.current.temperature if weather_data else None,
                        "humidity": weather_data.current.humidity if weather_data else None,
                        "precipitation": weather_data.current.precipitation if weather_data else None,
                        "description": weather_data.current.description if weather_data else None
                    },
                    "agricultural_indices": {
                        "growing_degree_days": weather_data.growing_degree_days if weather_data else None,
                        "drought_risk": weather_data.drought_risk if weather_data else None,
                        "frost_risk": weather_data.frost_risk if weather_data else None,
                        "heat_stress_index": weather_data.heat_stress_index if weather_data else None
                    }
                } if weather_data else None,
                "market_insights": {
                    "corn_sentiment": corn_prices.market_sentiment if corn_prices else None,
                    "soybean_sentiment": soybean_prices.market_sentiment if soybean_prices else None,
                    "wheat_sentiment": wheat_prices.market_sentiment if wheat_prices else None,
                    "favorable_crops": [
                        crop for crop, prices in [
                            ("corn", corn_prices), 
                            ("soybeans", soybean_prices), 
                            ("wheat", wheat_prices)
                        ] if prices and prices.market_sentiment in ["bullish", "neutral"]
                    ]
                },
                "summary": summary,
                "deficiencies": deficiencies,
                "recommendations": recommendations,
                "trend_analysis": trend_analysis
            })
        
        total_duration = time.time() - analysis_start
        logger.info(f"✅ [ANALYSIS-{analysis_short_id}] Comprehensive analysis completed for farm {farm_id} in {total_duration:.2f}s")
        
    except Exception as e:
        total_duration = time.time() - analysis_start
        logger.error(f"❌ [ANALYSIS-{analysis_short_id}] Error in comprehensive analysis after {total_duration:.2f}s: {e}")
        if analysis_id in analysis_results:
            analysis_results[analysis_id]["status"] = "failed"
            analysis_results[analysis_id]["error"] = str(e)

# Enums
class AnalysisStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class HealthLevel(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"

class CropRecommendation(str, Enum):
    HIGHLY_RECOMMENDED = "highly_recommended"
    RECOMMENDED = "recommended"
    NEUTRAL = "neutral"
    NOT_RECOMMENDED = "not_recommended"

# Pydantic models
class SoilHealthIndicators(BaseModel):
    ph_level: float = Field(..., ge=0, le=14, description="Soil pH level")
    salinity: float = Field(..., ge=0, description="Soil salinity (EC)")
    moisture_content: float = Field(..., ge=0, le=100, description="Soil moisture percentage")
    temperature: float = Field(..., description="Land surface temperature (°C)")
    organic_matter: float = Field(..., ge=0, le=100, description="Organic matter percentage")

class VegetationIndices(BaseModel):
    ndvi: float = Field(..., ge=-1, le=1, description="Normalized Difference Vegetation Index")
    ndwi: float = Field(..., ge=-1, le=1, description="Normalized Difference Water Index")
    savi: float = Field(..., ge=-1, le=1, description="Soil-Adjusted Vegetation Index")
    evi: float = Field(..., ge=-1, le=1, description="Enhanced Vegetation Index")
    ndmi: float = Field(..., ge=-1, le=1, description="Normalized Difference Moisture Index")

class SoilConditionIndices(BaseModel):
    bsi: float = Field(..., description="Bare Soil Index")
    si: float = Field(..., description="Salinity Index")
    ci: float = Field(..., description="Coloration Index")
    bi: float = Field(..., description="Brightness Index")

class SoilHealthReport(BaseModel):
    id: str
    farm_id: str
    analysis_date: datetime
    status: AnalysisStatus
    confidence_score: float = Field(..., ge=0, le=1, description="AI confidence score (0-1)")
    overall_health: HealthLevel
    
    # Detailed indicators
    soil_indicators: SoilHealthIndicators
    vegetation_indices: VegetationIndices
    soil_condition_indices: SoilConditionIndices
    
    # AI insights
    summary: str = Field(..., description="Human-readable summary")
    deficiencies: List[str] = Field(default=[], description="Identified soil deficiencies")
    recommendations: List[str] = Field(default=[], description="Fertilizer/amendment recommendations")
    trend_analysis: Optional[str] = Field(None, description="Trend compared to historical data")
    
    created_at: datetime

class CropOption(BaseModel):
    crop_type: str
    recommendation_level: CropRecommendation
    expected_yield: float = Field(..., description="Expected yield per acre/hectare")
    estimated_revenue: float = Field(..., description="Estimated revenue")
    input_costs: float = Field(..., description="Estimated input costs")
    net_profit: float = Field(..., description="Estimated net profit")
    roi_percentage: float = Field(..., description="Return on investment percentage")
    soil_health_impact: str = Field(..., description="Impact on long-term soil health")
    confidence_score: float = Field(..., ge=0, le=1, description="AI confidence score (0-1)")

class ROIAnalysisReport(BaseModel):
    id: str
    farm_id: str
    soil_health_report_id: str
    analysis_date: datetime
    status: AnalysisStatus
    
    # Market conditions
    market_forecast: Dict[str, Any] = Field(default={}, description="Market price forecasts")
    weather_forecast: Dict[str, Any] = Field(default={}, description="Weather predictions")
    
    # Crop recommendations
    crop_options: List[CropOption] = Field(default=[], description="Available crop options")
    recommended_crop: Optional[str] = Field(None, description="Top recommended crop")
    
    # Economic analysis
    economic_summary: str = Field(..., description="Human-readable economic analysis")
    risk_assessment: str = Field(..., description="Risk factors and mitigation")
    reasoning: str = Field(..., description="AI reasoning explanation")
    
    created_at: datetime

class AnalysisRequest(BaseModel):
    farm_id: str
    include_historical: bool = Field(default=True, description="Include historical trend analysis")
    generate_roi: bool = Field(default=True, description="Generate ROI recommendations")

# Helper functions
async def get_farm_coordinates(farm_id: str) -> FarmCoordinates:
    """Get farm coordinates from database - placeholder implementation"""
    # TODO: Replace with actual database query
    # For demo purposes, return sample coordinates
    return FarmCoordinates(
        latitude=40.7128,  # New York coordinates as example
        longitude=-74.0060,
        area_hectares=10.0
    )

@router.post("/soil-health", response_model=SoilHealthReport, status_code=status.HTTP_202_ACCEPTED)
async def analyze_soil_health(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Initiate soil health analysis for a farm using satellite data
    
    - **farm_id**: ID of the farm to analyze
    - **include_historical**: Whether to include historical trend analysis
    """
    try:
        # Generate unique analysis ID
        analysis_id = str(uuid.uuid4())
        
        # Get farm coordinates
        farm_coords = await get_farm_coordinates(request.farm_id)
        
        # Create initial analysis record
        initial_analysis = {
            "id": analysis_id,
            "farm_id": request.farm_id,
            "analysis_date": datetime.utcnow(),
            "status": "pending",
            "confidence_score": 0.0,
            "overall_health": "good",
            "soil_indicators": {
                "ph_level": 0.0,
                "salinity": 0.0,
                "moisture_content": 0.0,
                "temperature": 0.0,
                "organic_matter": 0.0
            },
            "vegetation_indices": {
                "ndvi": 0.0,
                "ndwi": 0.0,
                "savi": 0.0,
                "evi": 0.0,
                "ndmi": 0.0
            },
            "soil_condition_indices": {
                "bsi": 0.0,
                "si": 0.0,
                "ci": 0.0,
                "bi": 0.0
            },
            "summary": "Analysis in progress...",
            "deficiencies": [],
            "recommendations": [],
            "trend_analysis": None,
            "created_at": datetime.utcnow()
        }
        
        # Store initial analysis
        analysis_results[analysis_id] = initial_analysis
        
        # Add background task for actual processing
        background_tasks.add_task(
            process_soil_health_analysis,
            analysis_id,
            request.farm_id,
            farm_coords,
            request.include_historical
        )
        
        # Return initial response
        return initial_analysis
        
    except Exception as e:
        logger.error(f"Error initiating soil health analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate analysis: {str(e)}"
        )

@router.post("/roi-analysis", response_model=ROIAnalysisReport, status_code=status.HTTP_202_ACCEPTED)
async def analyze_roi(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Generate ROI analysis and crop recommendations for a farm
    
    - **farm_id**: ID of the farm to analyze
    """
    # TODO: Implement actual ROI analysis with Claude API
    # TODO: Add background task for processing
    # For now, return a placeholder response
    
    analysis_id = f"roi-analysis-{datetime.utcnow().timestamp()}"
    
    return {
        "id": analysis_id,
        "farm_id": request.farm_id,
        "soil_health_report_id": "soil-analysis-123",
        "analysis_date": datetime.utcnow(),
        "status": "pending",
        "market_forecast": {
            "corn": {"price": 5.50, "trend": "stable"},
            "soybeans": {"price": 12.80, "trend": "increasing"}
        },
        "weather_forecast": {
            "precipitation": "average",
            "temperature": "above_average",
            "growing_days": 180
        },
        "crop_options": [
            {
                "crop_type": "soybeans",
                "recommendation_level": "highly_recommended",
                "expected_yield": 50.0,
                "estimated_revenue": 640.0,
                "input_costs": 320.0,
                "net_profit": 320.0,
                "roi_percentage": 100.0,
                "soil_health_impact": "Improves nitrogen fixation and soil structure",
                "confidence_score": 0.88
            },
            {
                "crop_type": "corn",
                "recommendation_level": "recommended",
                "expected_yield": 180.0,
                "estimated_revenue": 990.0,
                "input_costs": 580.0,
                "net_profit": 410.0,
                "roi_percentage": 70.7,
                "soil_health_impact": "Neutral impact with proper management",
                "confidence_score": 0.82
            }
        ],
        "recommended_crop": "soybeans",
        "economic_summary": "Based on current soil conditions and market forecasts, soybeans offer the best ROI while improving soil health.",
        "risk_assessment": "Low risk scenario with stable weather patterns expected. Monitor for late-season drought conditions.",
        "reasoning": "Soybeans are recommended due to nitrogen-fixing properties that benefit your soil's organic matter levels, combined with favorable market conditions.",
        "created_at": datetime.utcnow()
    }

@router.get("/soil-health/{analysis_id}", response_model=SoilHealthReport)
async def get_soil_health_report(
    analysis_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get a specific soil health analysis report
    """
    try:
        if analysis_id not in analysis_results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found"
            )
        
        analysis = analysis_results[analysis_id]
        
        # Check if analysis failed
        if analysis.get("status") == "failed":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Analysis failed: {analysis.get('error', 'Unknown error')}"
            )
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving soil health report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analysis"
        )

@router.get("/roi-analysis/{analysis_id}", response_model=ROIAnalysisReport)
async def get_roi_report(
    analysis_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get a specific ROI analysis report
    """
    # TODO: Implement report retrieval from database
    # TODO: Verify user ownership
    
    # Return placeholder ROI report for now
    return {
        "id": analysis_id,
        "farm_id": "placeholder-farm-id",
        "soil_health_report_id": "soil-analysis-123",
        "analysis_date": datetime.utcnow(),
        "status": "completed",
        "market_forecast": {
            "corn": {"price": 5.50, "trend": "stable"},
            "soybeans": {"price": 12.80, "trend": "increasing"}
        },
        "weather_forecast": {
            "precipitation": "average",
            "temperature": "above_average",
            "growing_days": 180
        },
        "crop_options": [
            {
                "crop_type": "soybeans",
                "recommendation_level": "highly_recommended",
                "expected_yield": 50.0,
                "estimated_revenue": 640.0,
                "input_costs": 320.0,
                "net_profit": 320.0,
                "roi_percentage": 100.0,
                "soil_health_impact": "Improves nitrogen fixation and soil structure",
                "confidence_score": 0.88
            },
            {
                "crop_type": "corn",
                "recommendation_level": "recommended",
                "expected_yield": 180.0,
                "estimated_revenue": 990.0,
                "input_costs": 580.0,
                "net_profit": 410.0,
                "roi_percentage": 70.7,
                "soil_health_impact": "Neutral impact with proper management",
                "confidence_score": 0.82
            }
        ],
        "recommended_crop": "soybeans",
        "economic_summary": "Based on current soil conditions and market forecasts, soybeans offer the best ROI while improving soil health.",
        "risk_assessment": "Low risk scenario with stable weather patterns expected. Monitor for late-season drought conditions.",
        "reasoning": "Soybeans are recommended due to nitrogen-fixing properties that benefit your soil's organic matter levels, combined with favorable market conditions.",
        "created_at": datetime.utcnow()
    }

@router.get("/farm/{farm_id}/history")
async def get_farm_analysis_history(
    farm_id: str,
    limit: int = 10,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get analysis history for a specific farm
    """
    # TODO: Implement history retrieval
    # TODO: Verify farm ownership
    return {
        "farm_id": farm_id,
        "analyses": [],
        "total_count": 0
    } 

@router.get("/status")
async def get_analysis_status():
    """
    Get comprehensive analysis system status including all integrated services
    """
    try:
        satellite_service = get_satellite_service()
        weather_service = get_weather_service()
        crop_price_service = get_crop_price_service()
        
        # Check overall system status
        satellite_available = satellite_service.is_available()
        weather_available = weather_service.is_available()
        price_available = crop_price_service.is_available()
        
        overall_status = "operational" if all([satellite_available, weather_available, price_available]) else "partial"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow(),
            "services": {
                "satellite_data": {
                    "available": satellite_available,
                    "provider": "Google Earth Engine",
                    "data_sources": ["Landsat 8", "Landsat 9"],
                    "status": "operational" if satellite_available else "degraded - using demo data"
                },
                "weather_data": {
                    "available": weather_available,
                    "provider": "OpenWeatherMap",
                    "features": ["current_conditions", "7_day_forecast", "agricultural_indices"],
                    "status": "operational" if weather_available else "degraded - using demo data"
                },
                "crop_prices": {
                    "available": price_available,
                    "providers": ["Commodities API", "USDA", "Market Data"],
                    "features": ["current_prices", "historical_trends", "market_analysis"],
                    "status": "operational" if price_available else "degraded - using demo data"
                },
                "ai_analysis": {
                    "available": True,  # Always available with fallback logic
                    "providers": ai_config.get_status(),
                    "features": ["soil_health_assessment", "roi_analysis", "crop_recommendations", "advanced_prompting"],
                    "strategy": "Hybrid - Gemini for text generation, Claude for reasoning",
                    "status": "operational" if (ai_config.gemini_available or ai_config.claude_available) else "degraded - using rule-based fallback"
                }
            },
            "data_integration": {
                "satellite_weather_fusion": True,
                "market_price_integration": True,
                "comprehensive_analysis": True,
                "real_time_updates": True
            },
            "cache_stats": satellite_cache.cache.get_cache_stats() if hasattr(satellite_cache.cache, 'get_cache_stats') else {},
            "analysis_queue": {
                "pending": len([r for r in analysis_results.values() if r["status"] == "pending"]),
                "in_progress": len([r for r in analysis_results.values() if r["status"] == "in_progress"]),
                "completed": len([r for r in analysis_results.values() if r["status"] == "completed"]),
                "failed": len([r for r in analysis_results.values() if r["status"] == "failed"]),
                "total_analyses": len(analysis_results)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting analysis status: {e}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow(),
            "error": str(e),
            "services": {
                "satellite_data": {"available": False, "status": "error"},
                "weather_data": {"available": False, "status": "error"},
                "crop_prices": {"available": False, "status": "error"},
                "ai_analysis": {"available": False, "status": "error"}
            }
        } 