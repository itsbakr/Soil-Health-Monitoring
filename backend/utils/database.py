"""
Database utilities for Supabase integration
Provides access to farm data and analysis persistence
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import httpx
from config import settings

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Simple Supabase REST API client"""
    
    def __init__(self):
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_SERVICE_KEY or settings.SUPABASE_ANON_KEY
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        self.initialized = bool(self.url and self.key)
        
        if self.initialized:
            logger.info("✅ Supabase client initialized")
        else:
            logger.warning("⚠️ Supabase not configured - using fallback data")
    
    async def get_farm(self, farm_id: str) -> Optional[Dict[str, Any]]:
        """Get farm by ID"""
        if not self.initialized:
            return None
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.url}/rest/v1/farms?id=eq.{farm_id}",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    farms = response.json()
                    if farms and len(farms) > 0:
                        logger.info(f"📍 Found farm: {farms[0].get('name')} at {farms[0].get('location_lat')}, {farms[0].get('location_lng')}")
                        return farms[0]
                        
                logger.warning(f"Farm {farm_id} not found in database")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching farm: {e}")
            return None
    
    async def get_farm_with_coordinates(self, farm_id: str) -> Dict[str, Any]:
        """Get farm coordinates for analysis - with fallback"""
        farm = await self.get_farm(farm_id)
        
        if farm:
            return {
                "latitude": farm.get("location_lat", 30.791552),
                "longitude": farm.get("location_lng", 31.028149),
                "area_hectares": farm.get("area_hectares", 5.0),
                "name": farm.get("name", "Unknown Farm"),
                "crop_type": farm.get("crop_type", "wheat"),
                "planting_date": farm.get("planting_date"),
                "harvest_date": farm.get("harvest_date")
            }
        
        # Fallback for demo/development - Nile Delta Egypt
        logger.warning(f"Using fallback coordinates for farm {farm_id}")
        return {
            "latitude": 30.791552,
            "longitude": 31.028149,
            "area_hectares": 5.0,
            "name": "Demo Farm",
            "crop_type": "wheat",
            "planting_date": None,
            "harvest_date": None
        }
    
    async def save_soil_health_analysis(
        self, 
        farm_id: str, 
        user_id: str,
        analysis_data: Dict[str, Any]
    ) -> Optional[str]:
        """Save soil health analysis to database"""
        if not self.initialized:
            logger.warning("Database not configured - analysis not persisted")
            return None
            
        try:
            # Extract vegetation indices
            veg_indices = analysis_data.get("vegetation_indices", {})
            
            record = {
                "farm_id": farm_id,
                "user_id": user_id,
                "status": "completed",
                "overall_health": analysis_data.get("health_score", 0),
                "confidence_score": analysis_data.get("confidence_score", 0),
                "satellite_source": analysis_data.get("satellite_source", "Sentinel-2"),
                "zone_data": analysis_data.get("zones", []),
                "problem_zones": analysis_data.get("problem_areas", []),
                "heatmap_data": analysis_data.get("heatmap_data", []),
                "ndvi": veg_indices.get("ndvi"),
                "ndwi": veg_indices.get("ndwi"),
                "ndmi": veg_indices.get("ndmi"),
                "savi": veg_indices.get("savi"),
                "evi": veg_indices.get("evi"),
                "ai_summary": analysis_data.get("summary", ""),
                "recommendations": analysis_data.get("recommendations", []),
                "risk_factors": analysis_data.get("deficiencies", []),
                "completed_at": datetime.now(timezone.utc).isoformat()
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.url}/rest/v1/soil_health_analyses",
                    headers=self.headers,
                    json=record
                )
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    if result and len(result) > 0:
                        logger.info(f"✅ Saved soil health analysis: {result[0].get('id')}")
                        return result[0].get("id")
                else:
                    logger.error(f"Failed to save analysis: {response.status_code} - {response.text}")
                    
        except Exception as e:
            logger.error(f"Error saving analysis: {e}")
            
        return None
    
    async def save_roi_analysis(
        self,
        farm_id: str,
        user_id: str,
        roi_data: Dict[str, Any]
    ) -> Optional[str]:
        """Save ROI analysis to database"""
        if not self.initialized:
            logger.warning("Database not configured - ROI analysis not persisted")
            return None
            
        try:
            # Extract recommended crop info
            recommended_crop = roi_data.get("recommended_crop", {})
            
            record = {
                "farm_id": farm_id,
                "user_id": user_id,
                "status": "completed",
                "current_crop": roi_data.get("current_crop"),
                "recommendations": roi_data.get("crop_options", []),
                "market_data": roi_data.get("market_forecast", {}),
                "risk_assessment": roi_data.get("risk_assessment", {}),
                "ai_summary": roi_data.get("economic_summary", ""),
                "strategic_advice": roi_data.get("reasoning", ""),
                "projected_revenue": recommended_crop.get("estimated_revenue"),
                "projected_costs": recommended_crop.get("input_costs"),
                "projected_profit": recommended_crop.get("net_profit"),
                "completed_at": datetime.now(timezone.utc).isoformat()
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.url}/rest/v1/roi_analyses",
                    headers=self.headers,
                    json=record
                )
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    if result and len(result) > 0:
                        logger.info(f"✅ Saved ROI analysis: {result[0].get('id')}")
                        return result[0].get("id")
                else:
                    logger.error(f"Failed to save ROI analysis: {response.status_code} - {response.text}")
                        
        except Exception as e:
            logger.error(f"Error saving ROI analysis: {e}")
            
        return None
    
    async def get_soil_health_history(
        self, 
        farm_id: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get soil health analysis history for a farm"""
        if not self.initialized:
            return []
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.url}/rest/v1/soil_health_analyses?farm_id=eq.{farm_id}&status=eq.completed&order=created_at.desc&limit={limit}",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    return response.json()
                    
        except Exception as e:
            logger.error(f"Error fetching soil health history: {e}")
            
        return []
    
    async def get_roi_history(
        self, 
        farm_id: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get ROI analysis history for a farm"""
        if not self.initialized:
            return []
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.url}/rest/v1/roi_analyses?farm_id=eq.{farm_id}&status=eq.completed&order=created_at.desc&limit={limit}",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    return response.json()
                    
        except Exception as e:
            logger.error(f"Error fetching ROI history: {e}")
            
        return []
    
    async def get_combined_analysis_history(
        self,
        farm_id: str,
        limit: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get combined soil health and ROI analysis history"""
        soil_history = await self.get_soil_health_history(farm_id, limit)
        roi_history = await self.get_roi_history(farm_id, limit)
        
        return {
            "soil_health": soil_history,
            "roi": roi_history
        }


# Global client instance
db = SupabaseClient()

