"""
Satellite Data Service for LARMMS

This service handles all satellite data processing using Google Earth Engine (GEE) API.
It provides functionality for:
- Landsat 8/9 data retrieval
- Vegetation indices calculation (NDVI, NDWI, SAVI, EVI, NDMI)
- Soil condition indices (BSI, SI, CI, BI)
- Cloud masking and data quality assessment
- Coordinate-to-pixel calculations for farm area analysis
"""

import ee
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FarmCoordinates:
    """Data class for farm location and boundaries"""
    latitude: float
    longitude: float
    area_hectares: float
    
    def to_ee_geometry(self) -> ee.Geometry:
        """Convert farm coordinates to Earth Engine geometry"""
        # For now, create a simple point geometry
        # In future, we could create a polygon based on farm boundaries
        return ee.Geometry.Point([self.longitude, self.latitude])
    
    def get_buffer_radius(self) -> float:
        """Calculate appropriate buffer radius based on farm area"""
        # Calculate radius assuming circular farm area
        # Area = π * r², so r = sqrt(Area / π)
        import math
        area_m2 = self.area_hectares * 10000  # Convert hectares to square meters
        radius_m = math.sqrt(area_m2 / math.pi)
        return max(radius_m, 30)  # Minimum 30m to cover at least one Landsat pixel


@dataclass
class SatelliteData:
    """Data class for processed satellite data"""
    farm_id: str
    date_captured: datetime
    cloud_coverage: float
    
    # Vegetation indices
    ndvi: float
    ndwi: float
    savi: float
    evi: float
    ndmi: float
    
    # Soil condition indices
    bsi: float  # Bare Soil Index
    si: float   # Salinity Index
    ci: float   # Coloration Index
    bi: float   # Brightness Index
    
    # Primary indicators
    surface_temperature: float
    moisture_estimate: float
    
    # Quality metrics
    pixel_count: int
    valid_pixels: int
    data_quality_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'farm_id': self.farm_id,
            'date_captured': self.date_captured.isoformat(),
            'cloud_coverage': self.cloud_coverage,
            'ndvi': self.ndvi,
            'ndwi': self.ndwi,
            'savi': self.savi,
            'evi': self.evi,
            'ndmi': self.ndmi,
            'bsi': self.bsi,
            'si': self.si,
            'ci': self.ci,
            'bi': self.bi,
            'surface_temperature': self.surface_temperature,
            'moisture_estimate': self.moisture_estimate,
            'pixel_count': self.pixel_count,
            'valid_pixels': self.valid_pixels,
            'data_quality_score': self.data_quality_score
        }


class SatelliteService:
    """Service for satellite data processing using Google Earth Engine"""
    
    def __init__(self):
        """Initialize the satellite service"""
        self.initialized = False
        self._setup_earth_engine()
    
    def _setup_earth_engine(self):
        """Initialize Google Earth Engine authentication"""
        try:
            # First, try using service account JSON file (preferred method)
            service_account_file = "ee_sa.json"
            if os.path.exists(service_account_file):
                logger.info("Found service account file, initializing Google Earth Engine...")
                credentials = ee.ServiceAccountCredentials(
                    None,  # Email will be read from JSON file
                    key_file=service_account_file
                )
                ee.Initialize(credentials, project="land-degradation-soil-moisture")
                self.initialized = True
                logger.info("✅ Google Earth Engine initialized with service account from JSON file")
                return
            
            # Fallback to environment variables
            from config import settings
            service_account_email = settings.GOOGLE_EARTH_ENGINE_SERVICE_ACCOUNT
            private_key = settings.GOOGLE_EARTH_ENGINE_PRIVATE_KEY
            project_id = settings.GOOGLE_EARTH_ENGINE_PROJECT_ID or 'land-degradation-soil-moisture'
            
            if service_account_email and private_key:
                logger.info("Initializing Google Earth Engine with service account from env vars...")
                private_key_data = private_key.replace('\\n', '\n')  # Handle escaped newlines
                credentials = ee.ServiceAccountCredentials(
                    email=service_account_email,
                    key_data=private_key_data
                )
                ee.Initialize(credentials, project=project_id)
                self.initialized = True
                logger.info("✅ Google Earth Engine initialized with service account from env vars")
            else:
                # Try default authentication (for development)
                logger.info("Attempting default Google Earth Engine authentication...")
                ee.Initialize()
                self.initialized = True
                logger.info("✅ Google Earth Engine initialized with default credentials")
                
        except Exception as e:
            logger.warning(f"EE initialization failed: {e}")
            logger.info("Google Earth Engine not available - service will use demo data")
            self.initialized = False
    
    def _authenticate_service_account(self):
        """Authenticate using service account (for production)"""
        # This would typically load service account credentials
        # For now, we'll use the default authentication method
        # In production, you would:
        # 1. Download service account key from Google Cloud Console
        # 2. Set GOOGLE_APPLICATION_CREDENTIALS environment variable
        # 3. Use ee.ServiceAccountCredentials()
        
        service_account_key = os.getenv('GOOGLE_EE_SERVICE_ACCOUNT_KEY')
        if service_account_key:
            # Parse service account key and authenticate
            credentials = ee.ServiceAccountCredentials(
                email=os.getenv('GOOGLE_EE_SERVICE_ACCOUNT_EMAIL'),
                key_data=service_account_key
            )
            ee.Initialize(credentials)
        else:
            # Fall back to default authentication
            ee.Authenticate()
    
    def is_available(self) -> bool:
        """Check if the satellite service is available"""
        return self.initialized
    
    def get_landsat_collection(self, start_date: datetime, end_date: datetime) -> ee.ImageCollection:
        """Get Landsat 8/9 image collection for date range"""
        if not self.initialized:
            raise RuntimeError("Earth Engine not initialized")
        
        # Combine Landsat 8 and 9 collections
        landsat8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
            .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        
        landsat9 = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2') \
            .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        
        # Merge collections
        return landsat8.merge(landsat9)
    
    def apply_cloud_mask(self, image: ee.Image) -> ee.Image:
        """Apply cloud masking to Landsat image"""
        # Use QA_PIXEL band for cloud masking
        qa = image.select('QA_PIXEL')
        
        # Cloud and shadow mask
        cloud_mask = qa.bitwiseAnd(1 << 3).eq(0)  # Cloud
        shadow_mask = qa.bitwiseAnd(1 << 4).eq(0)  # Cloud shadow
        
        # Apply mask
        return image.updateMask(cloud_mask.And(shadow_mask))
    
    def calculate_vegetation_indices(self, image: ee.Image) -> ee.Image:
        """Calculate vegetation indices from Landsat image"""
        # Scale factors for Landsat Collection 2
        scale_factor = 0.0000275
        add_offset = -0.2
        
        # Apply scaling factors
        scaled = image.select(['SR_B.*']).multiply(scale_factor).add(add_offset)
        
        # Extract bands (Landsat 8/9 band numbers)
        blue = scaled.select('SR_B2')      # Blue
        green = scaled.select('SR_B3')     # Green  
        red = scaled.select('SR_B4')       # Red
        nir = scaled.select('SR_B5')       # Near Infrared
        swir1 = scaled.select('SR_B6')     # SWIR 1
        swir2 = scaled.select('SR_B7')     # SWIR 2
        
        # Calculate vegetation indices
        ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI')
        ndwi = green.subtract(nir).divide(green.add(nir)).rename('NDWI')
        
        # SAVI (Soil-Adjusted Vegetation Index) - L factor = 0.5
        L = 0.5
        savi = nir.subtract(red).divide(nir.add(red).add(L)).multiply(1 + L).rename('SAVI')
        
        # EVI (Enhanced Vegetation Index)
        evi = nir.subtract(red).divide(
            nir.add(red.multiply(6)).subtract(blue.multiply(7.5)).add(1)
        ).multiply(2.5).rename('EVI')
        
        # NDMI (Normalized Difference Moisture Index)
        ndmi = nir.subtract(swir1).divide(nir.add(swir1)).rename('NDMI')
        
        return image.addBands([ndvi, ndwi, savi, evi, ndmi])
    
    def calculate_soil_indices(self, image: ee.Image) -> ee.Image:
        """Calculate soil condition indices"""
        # Scale factors for Landsat Collection 2
        scale_factor = 0.0000275
        add_offset = -0.2
        
        # Apply scaling factors
        scaled = image.select(['SR_B.*']).multiply(scale_factor).add(add_offset)
        
        # Extract bands
        blue = scaled.select('SR_B2')
        green = scaled.select('SR_B3') 
        red = scaled.select('SR_B4')
        nir = scaled.select('SR_B5')
        swir1 = scaled.select('SR_B6')
        swir2 = scaled.select('SR_B7')
        
        # BSI (Bare Soil Index)
        bsi = swir1.add(red).subtract(nir).subtract(blue).divide(
            swir1.add(red).add(nir).add(blue)
        ).rename('BSI')
        
        # SI (Salinity Index) - simplified version
        si = green.multiply(red).divide(blue).rename('SI')
        
        # CI (Coloration Index) - proxy for organic matter
        ci = red.subtract(green).divide(red.add(green)).rename('CI')
        
        # BI (Brightness Index) - overall reflectance
        bi = blue.add(green).add(red).divide(3).rename('BI')
        
        return image.addBands([bsi, si, ci, bi])
    
    def get_farm_satellite_data(
        self, 
        farm_coords: FarmCoordinates, 
        start_date: datetime = None,
        end_date: datetime = None,
        max_cloud_cover: float = 20.0
    ) -> Optional[SatelliteData]:
        """
        Get processed satellite data for a specific farm
        
        Args:
            farm_coords: Farm location and area information
            start_date: Start date for data collection (defaults to 30 days ago)
            end_date: End date for data collection (defaults to today)
            max_cloud_cover: Maximum cloud coverage percentage
            
        Returns:
            SatelliteData object with processed indices and metrics
        """
        if not self.initialized:
            logger.error("Earth Engine not initialized")
            return None
        
        try:
            # Set default date range (last 30 days)
            if end_date is None:
                end_date = datetime.now()
            if start_date is None:
                start_date = end_date - timedelta(days=30)
            
            # Get farm geometry
            farm_point = farm_coords.to_ee_geometry()
            buffer_radius = farm_coords.get_buffer_radius()
            farm_area = farm_point.buffer(buffer_radius)
            
            # Get Landsat collection
            collection = self.get_landsat_collection(start_date, end_date)
            
            # Filter by location and cloud cover
            filtered = collection.filterBounds(farm_area) \
                                .filter(ee.Filter.lt('CLOUD_COVER', max_cloud_cover))
            
            # Check if any images are available
            image_count = filtered.size().getInfo()
            if image_count == 0:
                logger.warning(f"No suitable images found for farm at {farm_coords.latitude}, {farm_coords.longitude}")
                return None
            
            # Get the most recent image
            latest_image = filtered.sort('system:time_start', False).first()
            
            # Apply cloud masking
            masked_image = self.apply_cloud_mask(latest_image)
            
            # Calculate vegetation indices
            with_vegetation = self.calculate_vegetation_indices(masked_image)
            
            # Calculate soil indices
            with_soil = self.calculate_soil_indices(with_vegetation)
            
            # Extract statistics for the farm area
            stats = with_soil.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=farm_area,
                scale=30,  # Landsat pixel size
                maxPixels=1e9
            )
            
            # Get image metadata
            metadata = latest_image.getInfo()['properties']
            capture_date = datetime.fromtimestamp(metadata['system:time_start'] / 1000)
            cloud_cover = metadata.get('CLOUD_COVER', 0)
            
            # Extract calculated values
            stats_dict = stats.getInfo()
            
            # Create SatelliteData object
            return SatelliteData(
                farm_id=f"{farm_coords.latitude}_{farm_coords.longitude}",
                date_captured=capture_date,
                cloud_coverage=cloud_cover,
                
                # Vegetation indices
                ndvi=stats_dict.get('NDVI', 0),
                ndwi=stats_dict.get('NDWI', 0),
                savi=stats_dict.get('SAVI', 0),
                evi=stats_dict.get('EVI', 0),
                ndmi=stats_dict.get('NDMI', 0),
                
                # Soil indices
                bsi=stats_dict.get('BSI', 0),
                si=stats_dict.get('SI', 0),
                ci=stats_dict.get('CI', 0),
                bi=stats_dict.get('BI', 0),
                
                # Basic indicators (placeholder calculations)
                surface_temperature=metadata.get('TEMPERATURE', 20.0),  # Placeholder
                moisture_estimate=stats_dict.get('NDMI', 0) * 100,  # NDMI as moisture proxy
                
                # Quality metrics
                pixel_count=100,  # Placeholder
                valid_pixels=90,  # Placeholder
                data_quality_score=min(100, max(0, 100 - cloud_cover))
            )
            
        except Exception as e:
            logger.error(f"Error processing satellite data: {e}")
            return None
    
    def get_historical_data(
        self, 
        farm_coords: FarmCoordinates, 
        months_back: int = 12
    ) -> List[SatelliteData]:
        """
        Get historical satellite data for trend analysis
        
        Args:
            farm_coords: Farm location and area
            months_back: Number of months of historical data to retrieve
            
        Returns:
            List of SatelliteData objects for different time periods
        """
        historical_data = []
        end_date = datetime.now()
        
        # Get data for each month
        for i in range(months_back):
            month_end = end_date - timedelta(days=30 * i)
            month_start = month_end - timedelta(days=30)
            
            data = self.get_farm_satellite_data(
                farm_coords, 
                start_date=month_start, 
                end_date=month_end
            )
            
            if data:
                historical_data.append(data)
        
        return historical_data
    
    def health_score_from_indices(self, data: SatelliteData) -> float:
        """
        Calculate overall soil health score from satellite indices
        
        This is a simplified scoring system that can be refined with more research
        """
        if not data:
            return 0.0
        
        # NDVI scoring (higher is better for crops)
        ndvi_score = min(100, max(0, (data.ndvi + 1) * 50))  # Scale -1 to 1 → 0 to 100
        
        # Moisture scoring (NDMI-based)
        moisture_score = min(100, max(0, (data.ndmi + 1) * 50))
        
        # Soil condition scoring (lower BSI is better)
        soil_score = min(100, max(0, 100 - (data.bsi + 1) * 50))
        
        # Data quality impact
        quality_factor = data.data_quality_score / 100
        
        # Weighted average
        health_score = (ndvi_score * 0.4 + moisture_score * 0.3 + soil_score * 0.3) * quality_factor
        
        return round(health_score, 1)


# Global service instance
satellite_service = SatelliteService()


def get_satellite_service() -> SatelliteService:
    """Get the global satellite service instance"""
    return satellite_service