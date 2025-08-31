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

def _extract_weather_data(weather_data, weather_service, farm_coords: FarmCoordinates):
    """Extract weather data handling both AgriculturalWeatherData and WeatherCondition objects"""
    from services.weather_service import AgriculturalWeatherData, WeatherCondition
    from datetime import datetime
    
    def safe_date_format(date_obj):
        """Safely format a date object to ISO string"""
        if hasattr(date_obj, 'isoformat'):
            return date_obj.isoformat()
        elif isinstance(date_obj, str):
            return date_obj
        else:
            return str(date_obj)
    
    if not weather_data:
        return {}
    
    # Check if it's AgriculturalWeatherData (comprehensive) or WeatherCondition (basic)
    if isinstance(weather_data, AgriculturalWeatherData):
        return {
            "current_conditions": {
                "temperature": weather_data.current.temperature,
                "humidity": weather_data.current.humidity,
                "pressure": weather_data.current.pressure,
                "wind_speed": weather_data.current.wind_speed,
                "description": weather_data.current.description,
                "precipitation": weather_data.current.precipitation
            },
            "forecast": [
                {
                    "date": safe_date_format(f.date),
                    "temperature_max": getattr(f, 'temperature_max', 25.0),
                    "temperature_min": getattr(f, 'temperature_min', 15.0),
                    "precipitation": getattr(f, 'precipitation', 0.0),
                    "description": getattr(f, 'description', 'Partly cloudy')
                } for f in weather_data.forecast[:5] if f  # Limit to 5 days, skip None entries
            ],
            "agricultural_indices": {
                "growing_degree_days": weather_data.growing_degree_days,
                "drought_risk": weather_data.drought_risk,
                "frost_risk": weather_data.frost_risk,
                "heat_stress_index": weather_data.heat_stress_index
            }
        }
    elif isinstance(weather_data, WeatherCondition):
        # Fallback for basic weather data
        forecast = weather_service.get_weather_forecast(farm_coords.latitude, farm_coords.longitude, 7)
        return {
            "current_conditions": {
                "temperature": weather_data.temperature,
                "humidity": weather_data.humidity,
                "pressure": weather_data.pressure,
                "wind_speed": weather_data.wind_speed,
                "description": weather_data.description,
                "precipitation": weather_data.precipitation
            },
            "forecast": [
                {
                    "date": safe_date_format(f.date),
                    "temperature_max": getattr(f, 'temperature_max', 25.0),
                    "temperature_min": getattr(f, 'temperature_min', 15.0),
                    "precipitation": getattr(f, 'precipitation', 0.0),
                    "description": getattr(f, 'description', 'Partly cloudy')
                } for f in forecast[:5] if f  # Limit to 5 days, skip None entries
            ] if forecast else [],
            "agricultural_indices": {
                "growing_degree_days": None,
                "drought_risk": "moderate",
                "frost_risk": "low" if weather_data.temperature > 5 else "moderate",
                "heat_stress_index": max(0, (weather_data.temperature - 30) * 0.1) if weather_data.temperature > 30 else 0.0
            }
        }
    else:
        return {}

# Background task functions
async def process_roi_analysis(analysis_id: str, farm_id: str, farm_coords: FarmCoordinates):
    """Background task to process comprehensive ROI analysis"""
    import time
    
    analysis_start = time.time()
    analysis_short_id = analysis_id[:8]
    
    try:
        logger.info(f"💰 [ROI-{analysis_short_id}] Starting comprehensive ROI analysis for farm {farm_id}")
        
        # Update status to in progress
        if analysis_id in analysis_results:
            analysis_results[analysis_id]["status"] = "in_progress"
        
        # Get all services
        satellite_service = get_satellite_service()
        weather_service = get_weather_service()
        crop_price_service = get_crop_price_service()
        
        # Collect comprehensive data
        logger.info(f"📊 [ROI-{analysis_short_id}] Gathering data for analysis...")
        
        # Get satellite data
        satellite_data = satellite_service.get_farm_satellite_data(farm_coords)
        
        # Get weather data (try agricultural analysis first, fall back to current weather)
        weather_data = weather_service.get_agricultural_weather_analysis(
            farm_coords.latitude, farm_coords.longitude
        )
        if not weather_data:
            # Fallback to basic weather data
            current_weather = weather_service.get_current_weather(
                farm_coords.latitude, farm_coords.longitude
            )
            weather_data = current_weather
        
        # Get market data for major crops
        corn_prices = await crop_price_service.get_market_analysis("corn", "US")
        soybean_prices = await crop_price_service.get_market_analysis("soybeans", "US")
        wheat_prices = await crop_price_service.get_market_analysis("wheat", "US")
        
        # Prepare comprehensive farm data
        farm_analysis_data = {
            "farm_id": farm_id,
            "farm_coords": {
                "latitude": farm_coords.latitude,
                "longitude": farm_coords.longitude,
                "size_acres": farm_coords.area_hectares * 2.47105  # Convert hectares to acres
            },
            "soil_analysis": {
                "ndvi": satellite_data.ndvi if satellite_data else 0.45,
                "ndwi": satellite_data.ndwi if satellite_data else 0.15,
                "moisture": satellite_data.moisture_estimate if satellite_data else 45.0,
                "organic_matter": 2.5,  # Would come from soil tests
                "ph_estimate": 6.5,  # Would come from soil tests
                "salinity": satellite_data.si if satellite_data else 0.1,
                "temperature": satellite_data.surface_temperature if satellite_data else 20.0
            },
            "weather_data": _extract_weather_data(weather_data, weather_service, farm_coords),
            "market_data": {
                "corn": {
                    "current_price": corn_prices.current_price.price if corn_prices and corn_prices.current_price else 5.50,
                    "unit": corn_prices.current_price.unit if corn_prices and corn_prices.current_price else "$/bushel",
                    "market_sentiment": corn_prices.market_sentiment if corn_prices else "neutral",
                    "trend": corn_prices.price_history.trend if corn_prices and corn_prices.price_history else "stable"
                } if corn_prices else {},
                "soybeans": {
                    "current_price": soybean_prices.current_price.price if soybean_prices and soybean_prices.current_price else 12.80,
                    "unit": soybean_prices.current_price.unit if soybean_prices and soybean_prices.current_price else "$/bushel",
                    "market_sentiment": soybean_prices.market_sentiment if soybean_prices else "neutral",
                    "trend": soybean_prices.price_history.trend if soybean_prices and soybean_prices.price_history else "stable"
                } if soybean_prices else {},
                "wheat": {
                    "current_price": wheat_prices.current_price.price if wheat_prices and wheat_prices.current_price else 6.80,
                    "unit": wheat_prices.current_price.unit if wheat_prices and wheat_prices.current_price else "$/bushel",
                    "market_sentiment": wheat_prices.market_sentiment if wheat_prices else "neutral",
                    "trend": wheat_prices.price_history.trend if wheat_prices and wheat_prices.price_history else "stable"
                } if wheat_prices else {}
            }
        }
        
        # First try to reuse existing soil health analysis, or create new one
        logger.info(f"🔬 [ROI-{analysis_short_id}] Getting soil health analysis...")
        
        # Look for existing soil health analysis for this farm (from last 24 hours)
        existing_soil_analysis = None
        for analysis_key, analysis_data in analysis_results.items():
            if (analysis_data.get("farm_id") == farm_id and 
                analysis_data.get("status") == "completed" and
                "soil_indicators" in analysis_data):
                
                # Check if analysis is recent (within 24 hours)
                analysis_time = analysis_data.get("analysis_date")
                if analysis_time and (datetime.utcnow() - analysis_time).total_seconds() < 86400:
                    existing_soil_analysis = analysis_data
                    logger.info(f"🔄 [ROI-{analysis_short_id}] Reusing existing soil health analysis: {analysis_key[:8]}")
                    break
        
        if existing_soil_analysis:
            # Convert existing analysis to SoilHealthReport format for ROI agent
            soil_health_report = _convert_to_soil_health_report(existing_soil_analysis)
            logger.info(f"✅ [ROI-{analysis_short_id}] Using existing soil health analysis - Score: {soil_health_report.overall_score:.1f}, Status: {soil_health_report.health_status}")
        else:
            # No recent analysis found, run new soil health analysis
            logger.info(f"🔬 [ROI-{analysis_short_id}] Running new soil health analysis...")
            soil_health_report = await soil_health_agent.analyze_soil_health(farm_analysis_data)
            logger.info(f"🔬 [ROI-{analysis_short_id}] New soil health analysis complete - Score: {soil_health_report.overall_score:.1f}, Status: {soil_health_report.health_status}")
        
        # Now run comprehensive ROI analysis
        logger.info(f"💡 [ROI-{analysis_short_id}] Running comprehensive ROI analysis...")
        logger.info(f"📊 [ROI-{analysis_short_id}] Input data: Soil Score: {soil_health_report.overall_score:.1f}, Farm Size: {farm_analysis_data['farm_coords']['size_acres']:.1f} acres")
        
        roi_report = await roi_agent.analyze_roi_and_recommend_crops(
            farm_analysis_data,
            soil_health_report,
            farm_analysis_data["market_data"],
            farm_analysis_data["weather_data"]
        )
        
        logger.info(f"✅ [ROI-{analysis_short_id}] ROI analysis completed - Recommended crop: {roi_report.recommended_crop.crop_name}")
        
        # Convert to API format
        crop_options = []
        for crop_rec in roi_report.alternative_crops:
            crop_options.append({
                "crop_type": crop_rec.crop_name.lower(),
                "recommendation_level": "highly_recommended" if crop_rec.roi_percentage > 80 else 
                                       "recommended" if crop_rec.roi_percentage > 50 else 
                                       "consider" if crop_rec.roi_percentage > 20 else "not_recommended",
                "expected_yield": crop_rec.expected_yield,
                "estimated_revenue": crop_rec.expected_revenue,
                "input_costs": crop_rec.input_costs,
                "net_profit": crop_rec.net_profit,
                "roi_percentage": crop_rec.roi_percentage,
                "soil_health_impact": f"Soil compatibility: {crop_rec.soil_compatibility:.1%} | " + crop_rec.reasoning,
                "confidence_score": crop_rec.confidence_score,
                "risk_level": crop_rec.risk_level.value if hasattr(crop_rec.risk_level, 'value') else str(crop_rec.risk_level)
            })
        
        # Update analysis result with comprehensive data
        if analysis_id in analysis_results:
            # Generate a unique ID for the soil health report
            soil_health_report_id = f"soil-{analysis_id[:8]}-{int(time.time())}"
            analysis_results[analysis_id].update({
                "status": "completed",
                "soil_health_report_id": soil_health_report_id,
                "market_forecast": {
                    "corn": {
                        "price": corn_prices.current_price.price if corn_prices and corn_prices.current_price else 5.50,
                        "trend": corn_prices.price_history.trend if corn_prices and corn_prices.price_history else "stable"
                    },
                    "soybeans": {
                        "price": soybean_prices.current_price.price if soybean_prices and soybean_prices.current_price else 12.80,
                        "trend": soybean_prices.price_history.trend if soybean_prices and soybean_prices.price_history else "stable"
                    },
                    "wheat": {
                        "price": wheat_prices.current_price.price if wheat_prices and wheat_prices.current_price else 6.80,
                        "trend": wheat_prices.price_history.trend if wheat_prices and wheat_prices.price_history else "stable"
                    }
                },
                "weather_forecast": {
                    "optimistic": f"Favorable weather conditions with {roi_report.scenario_analysis.get('optimistic', {}).get('probability', 0.25)*100:.0f}% probability",
                    "most_likely": f"Expected weather patterns with {roi_report.scenario_analysis.get('most_likely', {}).get('probability', 0.50)*100:.0f}% probability", 
                    "pessimistic": f"Challenging weather conditions with {roi_report.scenario_analysis.get('pessimistic', {}).get('probability', 0.25)*100:.0f}% probability"
                },
                "crop_options": crop_options,
                "recommended_crop": roi_report.recommended_crop.crop_name.lower(),
                "economic_summary": f"""
🎯 **RECOMMENDED CROP: {roi_report.recommended_crop.crop_name.upper()}**

**FINANCIAL PROJECTION:**
• Expected ROI: {roi_report.recommended_crop.roi_percentage:.1f}%
• Net Profit per Acre: ${roi_report.recommended_crop.net_profit:.0f}
• Total Expected Revenue: ${roi_report.recommended_crop.expected_revenue:.0f}/acre
• Input Costs: ${roi_report.recommended_crop.input_costs:.0f}/acre
• Payback Period: {roi_report.recommended_crop.payback_period} months

**3-YEAR PROJECTION:**
• Year 1 Profit: ${roi_report.economic_projections.get('year_1_profit', 0):.0f}/acre
• Year 2 Profit: ${roi_report.economic_projections.get('year_2_profit', 0):.0f}/acre (with soil improvement)
• Year 3 Profit: ${roi_report.economic_projections.get('year_3_profit', 0):.0f}/acre
• Total 3-Year ROI: {roi_report.economic_projections.get('total_3_year_roi', 0):.1f}%

**SOIL HEALTH IMPACT:**
• Soil Compatibility: {roi_report.recommended_crop.soil_compatibility:.1%}
• Expected soil improvement with proper management
• Long-term sustainability score: {soil_health_report.overall_score + 10:.0f}/100 (projected)

**MARKET ANALYSIS:**
• Market Favorability: {roi_report.recommended_crop.market_favorability:.1%}
• Current market trend supports this crop choice
• Risk Level: {roi_report.recommended_crop.risk_level.value.title()}
                """,
                "risk_assessment": f"""
🛡️ **RISK ANALYSIS - {roi_report.recommended_crop.risk_level.value.upper()} RISK**

**SCENARIO ANALYSIS:**
• Optimistic (25% chance): {roi_report.scenario_analysis['optimistic']['roi']:.1f}% ROI
• Most Likely (50% chance): {roi_report.scenario_analysis['most_likely']['roi']:.1f}% ROI  
• Pessimistic (25% chance): {roi_report.scenario_analysis['pessimistic']['roi']:.1f}% ROI

**KEY RISK FACTORS:**
{chr(10).join(f"• {risk}" for risk in roi_report.recommended_crop.risk_factors)}

**MITIGATION STRATEGIES:**
{chr(10).join(f"• {strategy}" for strategy in roi_report.recommended_crop.mitigation_strategies)}

**OVERALL RISK LEVEL:** {roi_report.risk_assessment['overall_risk']}
**MITIGATION EFFECTIVENESS:** {roi_report.risk_assessment['mitigation_effectiveness']:.0%}

**CONFIDENCE LEVEL:** {roi_report.confidence_level:.1%}
                """,
                "reasoning": f"""
🧠 **AI ANALYSIS REASONING**

**WHY {roi_report.recommended_crop.crop_name.upper()} IS RECOMMENDED:**

{roi_report.detailed_reasoning}

**IMPLEMENTATION STEPS:**
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(roi_report.recommended_crop.implementation_steps))}

**DECISION FACTORS:**
{chr(10).join(f"• {factor}" for factor in roi_report.decision_matrix['winning_factors'])}

**FARMER SUMMARY:**
{roi_report.farmer_explanation}

**MONITORING PLAN:**
{roi_report.monitoring_plan.get('summary', 'Regular monitoring of soil health, market conditions, and crop performance recommended.')}

**MODEL CONFIDENCE:** {roi_report.confidence_level:.1%}
**ANALYSIS METHOD:** {roi_report.model_used}
                """,
                # Add ROI AI Insights
                "detailed_reasoning": roi_report.detailed_reasoning,
                "farmer_explanation": roi_report.farmer_explanation,
                "ai_insights": {
                    "executive_summary": roi_report.executive_summary,
                    "decision_matrix": roi_report.decision_matrix,
                    "scenario_analysis": roi_report.scenario_analysis,
                    "implementation_timeline": roi_report.implementation_timeline,
                    "monitoring_plan": roi_report.monitoring_plan
                },
                "model_used": roi_report.model_used,
                "confidence_level": roi_report.confidence_level
            })
        
        total_duration = time.time() - analysis_start
        logger.info(f"✅ [ROI-{analysis_short_id}] Comprehensive ROI analysis completed in {total_duration:.2f}s")
        
    except Exception as e:
        import traceback
        logger.error(f"❌ [ROI-{analysis_short_id}] Error in ROI analysis: {e}")
        logger.error(f"❌ [ROI-{analysis_short_id}] Full traceback: {traceback.format_exc()}")
        
        if analysis_id in analysis_results:
            analysis_results[analysis_id].update({
                "status": "failed",
                "economic_summary": f"Analysis failed: {str(e)}. Please try again or contact support.",
                "risk_assessment": "Unable to assess risk due to analysis failure. Recommend consulting with agricultural experts.",
                "reasoning": f"Technical Error: {str(e)}. The system encountered an issue while processing your farm data."
            })

def _convert_to_soil_health_report(existing_analysis: Dict[str, Any]):
    """Convert existing soil health analysis to SoilHealthReport format for ROI agent"""
    from services.soil_health_agent import SoilHealthReport
    
    # Create a minimal SoilHealthReport object from existing analysis data
    # This allows ROI agent to build on existing soil health results
    
    class MockSoilHealthReport:
        def __init__(self, analysis_data):
            self.id = analysis_data.get("id", "")
            self.overall_score = analysis_data.get("health_score", 0.0)
            self.health_status = analysis_data.get("overall_health", "unknown") 
            self.confidence_score = analysis_data.get("confidence_score", 0.0)
            
            # Extract key indicators and deficiencies from the analysis
            soil_indicators = analysis_data.get("soil_indicators", {})
            self.key_indicators = [
                f"NDVI: {soil_indicators.get('ndvi', 0):.2f}",
                f"Moisture: {soil_indicators.get('moisture_estimate', 0):.1f}%",
                f"Organic Matter: {soil_indicators.get('organic_matter', 0):.1f}%"
            ]
            
            # Create deficiencies list based on health status
            if self.health_status in ["critical", "poor"]:
                self.deficiencies = [
                    {"issue": "Low soil health score", "severity": "high"},
                    {"issue": "Requires immediate attention", "severity": "high"}
                ]
            elif self.health_status == "fair":
                self.deficiencies = [
                    {"issue": "Moderate soil health concerns", "severity": "medium"}
                ]
            else:
                self.deficiencies = []
    
    return MockSoilHealthReport(existing_analysis)

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
                "health_score": health_score,  # Add the numeric health score (0-100)
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
                "weather_data": _extract_weather_data(weather_data, weather_service, farm_coords) if weather_data else None,
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
                "trend_analysis": trend_analysis,
                # Add AI Insights from the soil health report
                "technical_analysis": soil_health_report.technical_analysis,
                "farmer_summary": soil_health_report.farmer_summary,
                "ai_explanation": soil_health_report.explanation,
                "model_used": soil_health_report.model_used,
                "generated_at": soil_health_report.generated_at.isoformat() if soil_health_report.generated_at else datetime.utcnow().isoformat(),
                "ai_confidence": soil_health_report.confidence_score,
                "key_indicators_ai": soil_health_report.key_indicators
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
    CRITICAL = "critical"

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
    health_score: float = Field(..., ge=0, le=100, description="Numeric health score (0-100)")
    
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
            "health_score": 0.0,
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
    Generate comprehensive ROI analysis and crop recommendations for a farm
    
    - **farm_id**: ID of the farm to analyze
    """
    analysis_id = f"roi-{str(uuid.uuid4())}"
    
    # Create initial analysis record
    initial_analysis = {
        "id": analysis_id,
        "farm_id": request.farm_id,
        "soil_health_report_id": "",
        "analysis_date": datetime.utcnow(),
        "status": "pending",
        "market_forecast": {},
        "weather_forecast": {},
        "crop_options": [],
        "recommended_crop": None,
        "economic_summary": "Analysis in progress...",
        "risk_assessment": "Risk assessment pending...",
        "reasoning": "Comprehensive analysis starting...",
        "created_at": datetime.utcnow()
    }
    
    # Store initial result
    analysis_results[analysis_id] = initial_analysis
    
    # Get farm coordinates
    farm_coords = await get_farm_coordinates(request.farm_id)
    
    # Start background processing
    background_tasks.add_task(
        process_roi_analysis,
        analysis_id,
        request.farm_id,
        farm_coords
    )
    
    return initial_analysis

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
    if analysis_id not in analysis_results:
        raise HTTPException(status_code=404, detail="ROI analysis not found")
    
    return analysis_results[analysis_id]

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

@router.get("/debug/config")
async def debug_configuration():
    """Debug endpoint to check API key configuration status"""
    from config import settings
    
    return {
        "environment_variables": {
            "GOOGLE_GEMINI_API_KEY": {
                "present": bool(settings.GOOGLE_GEMINI_API_KEY),
                "length": len(settings.GOOGLE_GEMINI_API_KEY) if settings.GOOGLE_GEMINI_API_KEY else 0,
                "first_10_chars": settings.GOOGLE_GEMINI_API_KEY[:10] if settings.GOOGLE_GEMINI_API_KEY else "N/A"
            },
            "ANTHROPIC_API_KEY": {
                "present": bool(settings.ANTHROPIC_API_KEY),
                "length": len(settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else 0,
                "first_10_chars": settings.ANTHROPIC_API_KEY[:10] if settings.ANTHROPIC_API_KEY else "N/A"
            },
            "OPENWEATHER_API_KEY": {
                "present": bool(settings.OPENWEATHER_API_KEY),
                "length": len(settings.OPENWEATHER_API_KEY) if settings.OPENWEATHER_API_KEY else 0,
                "first_8_chars": settings.OPENWEATHER_API_KEY[:8] if settings.OPENWEATHER_API_KEY else "N/A"
            }
        },
        "service_status": {
            "ai_services": ai_config.get_status(),
            "weather_available": get_weather_service().is_available(),
            "satellite_available": get_satellite_service().is_available(),
            "price_available": get_crop_price_service().is_available()
        }
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