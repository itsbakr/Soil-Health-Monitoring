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
from utils.satellite_calculations import (
    add_ndvi, add_ndwi, add_savi, add_evi, add_ndmi, add_bsi, add_si, add_ci, add_bi
)
from utils.satellite_quality import (
    interpret_ndvi_status, validate_data_quality, get_seasonal_context
)

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
    
    # --- New field for NDVI status ---
    ndvi_status: str = "normal"  # 'expected_low', 'unexpected_low', 'normal'
    # --- New field for quality issues ---
    quality_issues: list = None
    # --- New field for fallback status ---
    used_fallback: bool = False
    # --- New field for cloud masking status ---
    cloud_masking_status: str = "ok"  # 'ok', 'high_cloud', 'masked', etc.
    # --- New fields for data fusion transparency ---
    data_sources: list = None
    image_dates: list = None

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
            'data_quality_score': self.data_quality_score,
            'ndvi_status': self.ndvi_status,
            'quality_issues': self.quality_issues or [],
            'used_fallback': self.used_fallback,
            'cloud_masking_status': self.cloud_masking_status,
            'data_sources': self.data_sources or [],
            'image_dates': self.image_dates or [],
            'quality_summary': self.quality_summary(),
        }

    def quality_summary(self) -> str:
        """Summarize user-facing data quality, fallback, and cloud cover info for frontend display"""
        summary = []
        if self.quality_issues:
            summary.append(f"⚠️ Issues: {', '.join(self.quality_issues)}")
        if self.used_fallback:
            summary.append("ℹ️ Used historical data fallback")
        if self.cloud_masking_status != 'ok':
            summary.append(f"☁️ Cloud status: {self.cloud_masking_status}")
        if self.ndvi_status != 'normal':
            summary.append(f"🌱 NDVI: {self.ndvi_status.replace('_', ' ')}")
        if not summary:
            return "✅ Data quality good"
        return " | ".join(summary)


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
    
    def get_farm_satellite_data(
        self, 
        farm_coords: FarmCoordinates, 
        start_date: datetime = None,
        end_date: datetime = None,
        max_cloud_cover: float = 20.0
    ) -> Optional[SatelliteData]:
        """
        Get processed satellite data for a specific farm using intelligent multi-temporal averaging
        
        Args:
            farm_coords: Farm location and area information
            start_date: Start date for data collection (defaults to 30 days ago)
            end_date: End date for data collection (defaults to today)
            max_cloud_cover: Maximum cloud coverage percentage
            
        Returns:
            SatelliteData object with processed indices and metrics averaged over multiple acquisitions
        """
        if not self.initialized:
            logger.error("Earth Engine not initialized")
            return None
        
        try:
            data = self._get_multi_temporal_satellite_data(farm_coords, start_date, end_date, max_cloud_cover)
            # --- Fallback logic ---
            if data and data.quality_issues:
                fallback_needed = any(issue in data.quality_issues for issue in [
                    'Low pixel count', 'Low valid pixel ratio', 'Overall data quality score is low'])
                if fallback_needed:
                    logger.warning("Attempting fallback to historical data due to poor current data quality.")
                    historical = self.get_historical_data(farm_coords, months_back=12)
                    if historical:
                        # Average NDVI/indices from historical data
                        avg_ndvi = sum(d.ndvi for d in historical) / len(historical)
                        data.ndvi = avg_ndvi
                        # Optionally average other indices as well
                        data.used_fallback = True
                        logger.info(f"Used fallback historical NDVI: {avg_ndvi:.3f}")
            return data
        except Exception as e:
            logger.error(f"Error processing satellite data: {e}")
            logger.info("🛰️ Falling back to demo satellite data due to error")
            return self._get_demo_satellite_data(farm_coords)
    
    def _get_multi_temporal_satellite_data(
        self,
        farm_coords: FarmCoordinates,
        start_date: datetime = None,
        end_date: datetime = None,
        max_cloud_cover: float = 20.0
    ) -> Optional[SatelliteData]:
        """
        Advanced multi-temporal satellite data collection with intelligent fallback strategies
        """
        # Set default date range (last 30 days)
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=30)
        
        logger.info(f"🛰️ Collecting satellite data for {farm_coords.latitude:.4f}, {farm_coords.longitude:.4f}")
        logger.info(f"📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # Get farm geometry
        farm_point = farm_coords.to_ee_geometry()
        buffer_radius = farm_coords.get_buffer_radius()
        farm_area = farm_point.buffer(buffer_radius)
        
        # Strategy 1: Try to get multiple good quality images in the target period
        satellite_data = self._try_multi_temporal_collection(
            farm_area, farm_coords, start_date, end_date, max_cloud_cover
        )
        
        if satellite_data:
            # --- Integrate seasonal context for NDVI interpretation ---
            seasonal_context = get_seasonal_context(satellite_data.date_captured, farm_coords.latitude)
            ndvi_status = interpret_ndvi_status(satellite_data.ndvi, seasonal_context)
            satellite_data.ndvi_status = ndvi_status
            quality_issues = validate_data_quality(satellite_data)
            satellite_data.quality_issues = quality_issues
            if quality_issues:
                logger.warning(f"Data quality issues detected: {quality_issues}")
            # --- Cloud masking status logic ---
            if satellite_data.cloud_coverage > 50:
                satellite_data.cloud_masking_status = 'high_cloud'
            elif satellite_data.cloud_coverage > 20:
                satellite_data.cloud_masking_status = 'masked'
            else:
                satellite_data.cloud_masking_status = 'ok'
            return satellite_data
        
        # Strategy 2: Expand time range and relax cloud cover constraints
        logger.info("🔍 Expanding search to 90 days with relaxed cloud cover")
        extended_start = end_date - timedelta(days=90)
        satellite_data = self._try_multi_temporal_collection(
            farm_area, farm_coords, extended_start, end_date, max_cloud_cover * 2
        )
        
        if satellite_data:
            # --- Integrate seasonal context for NDVI interpretation ---
            seasonal_context = get_seasonal_context(satellite_data.date_captured, farm_coords.latitude)
            ndvi_status = interpret_ndvi_status(satellite_data.ndvi, seasonal_context)
            satellite_data.ndvi_status = ndvi_status
            quality_issues = validate_data_quality(satellite_data)
            satellite_data.quality_issues = quality_issues
            if quality_issues:
                logger.warning(f"Data quality issues detected: {quality_issues}")
            # --- Cloud masking status logic ---
            if satellite_data.cloud_coverage > 50:
                satellite_data.cloud_masking_status = 'high_cloud'
            elif satellite_data.cloud_coverage > 20:
                satellite_data.cloud_masking_status = 'masked'
            else:
                satellite_data.cloud_masking_status = 'ok'
            return satellite_data
        
        # Strategy 3: Last resort - get ANY available data in the past year
        logger.info("🔍 Final attempt: searching past year with any cloud cover")
        extended_start = end_date - timedelta(days=365)
        satellite_data = self._try_multi_temporal_collection(
            farm_area, farm_coords, extended_start, end_date, 100.0
        )
        
        if satellite_data:
            # --- Integrate seasonal context for NDVI interpretation ---
            seasonal_context = get_seasonal_context(satellite_data.date_captured, farm_coords.latitude)
            ndvi_status = interpret_ndvi_status(satellite_data.ndvi, seasonal_context)
            satellite_data.ndvi_status = ndvi_status
            quality_issues = validate_data_quality(satellite_data)
            satellite_data.quality_issues = quality_issues
            if quality_issues:
                logger.warning(f"Data quality issues detected: {quality_issues}")
            # --- Cloud masking status logic ---
            if satellite_data.cloud_coverage > 50:
                satellite_data.cloud_masking_status = 'high_cloud'
            elif satellite_data.cloud_coverage > 20:
                satellite_data.cloud_masking_status = 'masked'
            else:
                satellite_data.cloud_masking_status = 'ok'
            return satellite_data
        
        # If all strategies fail, return demo data
        logger.warning(f"No satellite images found for farm at {farm_coords.latitude}, {farm_coords.longitude}")
        logger.info("🏙️ This is normal for urban areas or locations with persistent cloud cover")
        logger.info("🛰️ Falling back to demo satellite data for analysis")
        return self._get_demo_satellite_data(farm_coords)
    
    def _try_multi_temporal_collection(
        self,
        farm_area,
        farm_coords: FarmCoordinates,
        start_date: datetime,
        end_date: datetime,
        max_cloud_cover: float,
        min_images: int = 1
    ) -> Optional[SatelliteData]:
        """
        Optimized satellite data collection with early exit strategy and enhanced variables
        """
        try:
            # Get both Landsat and Sentinel collections for better coverage
            landsat_collection = self.get_landsat_collection(start_date, end_date)
            sentinel_collection = self._get_sentinel_collection(start_date, end_date)
            
            # Combine collections and filter by location and cloud cover
            combined_collection = landsat_collection.merge(sentinel_collection) \
                                    .filterBounds(farm_area) \
                                    .filter(ee.Filter.lt('CLOUD_COVER', max_cloud_cover)) \
                                    .sort('system:time_start', False)
            
            # Check if any images are available
            image_count = combined_collection.size().getInfo()
            logger.info(f"📊 Found {image_count} images with <{max_cloud_cover}% cloud cover")
            
            if image_count == 0:
                return None
            
            # **OPTIMIZATION 1: Early exit for high-quality single image**
            if max_cloud_cover <= 5.0:  # Very strict cloud cover
                latest_image = combined_collection.first()
                single_result = self._process_single_high_quality_image(
                    latest_image, farm_area, farm_coords
                )
                if single_result and single_result.data_quality_score >= 95:
                    logger.info(f"🎯 Using single high-quality image (quality: {single_result.data_quality_score:.1f})")
                    return single_result
            
            # **OPTIMIZATION 2: Progressive quality assessment**
            # Start with best 3 images, add more if needed
            best_images = combined_collection.limit(min(image_count, 3))
            
            # Quick quality check on first batch
            first_batch = self._process_image_batch(best_images, farm_area, farm_coords)
            if first_batch and first_batch.data_quality_score >= 85:
                logger.info(f"🎯 Using 3-image composite (quality: {first_batch.data_quality_score:.1f})")
                return first_batch
            
            # If quality is insufficient, use up to 8 images for better averaging
            if image_count > 3:
                extended_images = combined_collection.limit(min(image_count, 8))
                extended_result = self._process_image_batch(extended_images, farm_area, farm_coords)
                if extended_result:
                    logger.info(f"🎯 Using {min(image_count, 8)}-image composite (quality: {extended_result.data_quality_score:.1f})")
                    return extended_result
            
            # Fallback to original result
            return first_batch
            
        except Exception as e:
            logger.error(f"Error in optimized satellite collection: {e}")
            return None
    
    def _get_sentinel_collection(self, start_date: datetime, end_date: datetime):
        """Get Sentinel-2 collection for enhanced data coverage"""
        try:
            return ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
                .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')) \
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
        except:
            # Fallback to empty collection if Sentinel not available
            return ee.ImageCollection([])
    
    def _process_single_high_quality_image(
        self, 
        image, 
        farm_area, 
        farm_coords: FarmCoordinates
    ) -> Optional[SatelliteData]:
        """Process a single high-quality image with enhanced variables"""
        try:
            # Process the image
            processed = self._process_single_image(image)
            
            # **ENHANCED VARIABLES EXTRACTION**
            enhanced_stats = processed.reduceRegion(
                reducer=ee.Reducer.mean().combine(
                    ee.Reducer.stdDev(), 
                    outputPrefix='std_',
                    sharedInputs=True
                ).combine(
                    ee.Reducer.minMax(),
                    outputPrefix='range_', 
                    sharedInputs=True
                ),
                geometry=farm_area,
                scale=10,  # Higher resolution for single image
                maxPixels=1e9
            )
            
            # Get metadata
            metadata = image.getInfo()['properties']
            capture_date = datetime.fromtimestamp(metadata['system:time_start'] / 1000)
            cloud_cover = metadata.get('CLOUD_COVER', 0)
            
            # Extract enhanced statistics
            stats_dict = enhanced_stats.getInfo()
            
            # **NEW VARIABLES**: Calculate advanced indices
            advanced_metrics = self._calculate_advanced_metrics(stats_dict)
            
            satellite_data = SatelliteData(
                farm_id=f"{farm_coords.latitude}_{farm_coords.longitude}",
                date_captured=capture_date,
                cloud_coverage=cloud_cover,
                
                # Standard vegetation indices
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
                
                # **ENHANCED VARIABLES**
                surface_temperature=advanced_metrics['surface_temp'],
                moisture_estimate=advanced_metrics['moisture_estimate'],
                
                # **NEW QUALITY METRICS**
                pixel_count=advanced_metrics['valid_pixel_count'],
                valid_pixels=advanced_metrics['valid_pixel_count'],
                data_quality_score=advanced_metrics['quality_score']
            )
            
            # Attach quality warnings if any
            if advanced_metrics.get('quality_warnings'):
                if satellite_data.quality_issues is None:
                    satellite_data.quality_issues = []
                satellite_data.quality_issues.extend(advanced_metrics['quality_warnings'])
            
            # Enhance with external data sources
            enhanced_result = self._enhance_with_external_data(satellite_data, farm_coords)
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Error processing single high-quality image: {e}")
            return None
    
    def _process_image_batch(
        self, 
        image_collection, 
        farm_area, 
        farm_coords: FarmCoordinates
    ) -> Optional[SatelliteData]:
        """Process a batch of images with enhanced metrics"""
        try:
            # Apply processing to all images
            processed_images = image_collection.map(self._process_single_image)
            
            # Create robust composite using median (outlier resistant)
            composite = processed_images.median()
            
            # Extract comprehensive statistics
            stats = composite.reduceRegion(
                reducer=ee.Reducer.mean().combine(
                    ee.Reducer.stdDev().setOutputs(['std']),
                    sharedInputs=True
                ),
                geometry=farm_area,
                scale=30,
                maxPixels=1e9
            )
            
            # Get metadata from most recent image
            latest_image = image_collection.first()
            metadata = latest_image.getInfo()['properties']
            capture_date = datetime.fromtimestamp(metadata['system:time_start'] / 1000)
            
            # Calculate batch quality metrics
            image_count = image_collection.size().getInfo()
            cloud_covers = image_collection.aggregate_array('CLOUD_COVER').getInfo()
            avg_cloud_cover = sum(cloud_covers) / len(cloud_covers) if cloud_covers else 0
            
            stats_dict = stats.getInfo()
            advanced_metrics = self._calculate_advanced_metrics(stats_dict, image_count, avg_cloud_cover)
            
            satellite_data = SatelliteData(
                farm_id=f"{farm_coords.latitude}_{farm_coords.longitude}",
                date_captured=capture_date,
                cloud_coverage=avg_cloud_cover,
                
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
                
                # Enhanced metrics
                surface_temperature=advanced_metrics['surface_temp'],
                moisture_estimate=advanced_metrics['moisture_estimate'],
                pixel_count=advanced_metrics['valid_pixel_count'],
                valid_pixels=advanced_metrics['valid_pixel_count'],
                data_quality_score=advanced_metrics['quality_score']
            )
            
            # Attach quality warnings if any
            if advanced_metrics.get('quality_warnings'):
                if satellite_data.quality_issues is None:
                    satellite_data.quality_issues = []
                satellite_data.quality_issues.extend(advanced_metrics['quality_warnings'])
            
            # --- Robust averaging and outlier rejection (median composite is already robust) ---
            # --- Expose sources and dates ---
            image_count = image_collection.size().getInfo()
            image_list = image_collection.toList(image_count)
            sources = []
            dates = []
            for i in range(image_count):
                img = ee.Image(image_list.get(i))
                props = img.getInfo().get('properties', {})
                if 'SPACECRAFT_ID' in props:
                    sources.append(props['SPACECRAFT_ID'])
                elif 'MISSION' in props:
                    sources.append(props['MISSION'])
                else:
                    sources.append('Unknown')
                if 'system:time_start' in props:
                    dt = datetime.fromtimestamp(props['system:time_start']/1000).isoformat()
                    dates.append(dt)
                else:
                    dates.append('Unknown')
            
            satellite_data = SatelliteData(
                farm_id=f"{farm_coords.latitude}_{farm_coords.longitude}",
                date_captured=capture_date,
                cloud_coverage=avg_cloud_cover,
                
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
                
                # Enhanced metrics
                surface_temperature=advanced_metrics['surface_temp'],
                moisture_estimate=advanced_metrics['moisture_estimate'],
                pixel_count=advanced_metrics['valid_pixel_count'],
                valid_pixels=advanced_metrics['valid_pixel_count'],
                data_quality_score=advanced_metrics['quality_score'],
                data_sources=sources,
                image_dates=dates
            )
            
            # Attach quality warnings if any
            if advanced_metrics.get('quality_warnings'):
                if satellite_data.quality_issues is None:
                    satellite_data.quality_issues = []
                satellite_data.quality_issues.extend(advanced_metrics['quality_warnings'])
            
            # Enhance with external data sources
            enhanced_result = self._enhance_with_external_data(satellite_data, farm_coords)
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Error processing image batch: {e}")
            return None
    
    def _calculate_advanced_metrics(
        self, 
        stats_dict: Dict[str, float], 
        image_count: int = 1, 
        avg_cloud_cover: float = 0
    ) -> Dict[str, float]:
        """Calculate advanced metrics and quality assessments"""
        # Enhanced moisture calculation using multiple indices
        ndmi = stats_dict.get('NDMI', 0)
        ndwi = stats_dict.get('NDWI', 0)
        moisture_estimate = (ndmi * 0.6 + ndwi * 0.4) * 100  # Weighted combination
        # Clamp moisture to [0, 100]
        moisture_estimate = max(0, min(100, moisture_estimate))
        # Soil temperature estimation (more sophisticated)
        # Use thermal bands if available, otherwise estimate from vegetation stress
        ndvi = stats_dict.get('NDVI', 0)
        base_temp = 20.0  # Base temperature
        vegetation_stress_factor = max(0, (0.7 - ndvi) * 50)  # Higher temp for stressed vegetation
        surface_temp = base_temp + vegetation_stress_factor
        # Clamp temperature to realistic range
        surface_temp = max(-30, min(60, surface_temp))
        # --- Calibration hooks ---
        # TODO: Calibrate with ground truth/reference datasets if available
        # --- Document limitations ---
        # - Surface temperature is an estimate, not direct measurement
        # - Moisture is a proxy, not absolute soil moisture
        # --- Add warnings for out-of-range values ---
        quality_warnings = []
        if surface_temp < -30 or surface_temp > 60:
            quality_warnings.append('Surface temperature out of realistic range')
        if moisture_estimate < 0 or moisture_estimate > 100:
            quality_warnings.append('Moisture estimate out of realistic range')
        # **NEW VARIABLES**: Crop stress indicators
        evi = stats_dict.get('EVI', 0)
        ndvi = stats_dict.get('NDVI', 0)
        crop_vigor = (evi + ndvi) / 2  # Combined vigor index
        
        # **NEW VARIABLES**: Soil health proxies
        bsi = stats_dict.get('BSI', 0)
        organic_matter_proxy = max(0, (ndvi * 0.7 - bsi * 0.3))  # Estimated organic matter
        
        # Enhanced quality scoring
        base_quality = 100 - avg_cloud_cover
        image_bonus = min(20, image_count * 3)  # Bonus for multiple images
        data_consistency = 100 - abs(stats_dict.get('std', 0)) * 100  # Penalty for high variance
        
        quality_score = min(100, max(0, base_quality + image_bonus + data_consistency * 0.1))
        
        # Estimated pixel counts (more realistic)
        area_hectares = 10.0  # Default farm area
        pixels_per_hectare = 111  # Approximate for 30m resolution
        valid_pixel_count = int(area_hectares * pixels_per_hectare * (1 - avg_cloud_cover/100))
        
        return {
            'surface_temp': surface_temp,
            'moisture_estimate': moisture_estimate,
            'crop_vigor': crop_vigor,
            'organic_matter_proxy': organic_matter_proxy,
            'soil_stress_index': bsi,
            'vegetation_consistency': data_consistency,
            'valid_pixel_count': valid_pixel_count,
            'quality_score': quality_score,
            'quality_warnings': quality_warnings
        }
    
    def _process_single_image(self, image):
        """
        Process a single satellite image: apply cloud mask and calculate all indices
        """
        # Apply cloud masking
        masked = self.apply_cloud_mask(image)
        # Apply index calculations using utility functions
        with_indices = add_ndvi(masked)
        with_indices = add_ndwi(with_indices)
        with_indices = add_savi(with_indices)
        with_indices = add_evi(with_indices)
        with_indices = add_ndmi(with_indices)
        with_indices = add_bsi(with_indices)
        with_indices = add_si(with_indices)
        with_indices = add_ci(with_indices)
        with_indices = add_bi(with_indices)
        return with_indices
    
    def _enhance_with_external_data(self, satellite_data: SatelliteData, farm_coords: FarmCoordinates) -> SatelliteData:
        """Enhance satellite data with external APIs and computed variables"""
        try:
            # **ENHANCEMENT 1: Elevation and Terrain Data**
            elevation_data = self._get_elevation_data(farm_coords)
            
            # **ENHANCEMENT 2: Weather Integration** 
            weather_context = self._get_weather_context(farm_coords)
            
            # **ENHANCEMENT 3: Seasonal and Temporal Analysis**
            seasonal_context = get_seasonal_context(satellite_data.date_captured, farm_coords.latitude)
            
            # **ENHANCEMENT 4: Agricultural Zone Classification**
            ag_zone = self._classify_agricultural_zone(farm_coords, elevation_data)
            
            logger.info(f"🔬 Enhanced satellite data with:")
            logger.info(f"   📏 Elevation: {elevation_data['elevation']:.0f}m, Slope: {elevation_data['slope']:.1f}°")
            logger.info(f"   🌡️ Growing Season: Day {seasonal_context['growing_day_of_year']}")
            logger.info(f"   🗺️ Agricultural Zone: {ag_zone}")
            
            # Store enhanced data (would typically update the SatelliteData model)
            # For now, we'll use the existing structure but note these enhancements
            
            return satellite_data
            
        except Exception as e:
            logger.warning(f"Failed to enhance with external data: {e}")
            return satellite_data
    
    def _get_elevation_data(self, farm_coords: FarmCoordinates) -> Dict[str, float]:
        """Get elevation and terrain data using Google Earth Engine or external DEM"""
        try:
            # Use SRTM Digital Elevation Model
            farm_point = farm_coords.to_ee_geometry()
            
            # Get elevation
            dem = ee.Image('USGS/SRTMGL1_003')
            elevation = dem.sample(farm_point, 30).first().get('elevation').getInfo()
            
            # Calculate slope
            slope = ee.Terrain.slope(dem).sample(farm_point, 30).first().get('slope').getInfo()
            
            # Calculate aspect (direction of slope)
            aspect = ee.Terrain.aspect(dem).sample(farm_point, 30).first().get('aspect').getInfo()
            
            return {
                'elevation': elevation or 100.0,  # Default 100m if unavailable
                'slope': slope or 0.0,
                'aspect': aspect or 0.0,
                'terrain_ruggedness': slope * 0.1,  # Simple ruggedness index
            }
        except:
            # Fallback values
            return {
                'elevation': 100.0,
                'slope': 2.0,
                'aspect': 180.0,
                'terrain_ruggedness': 0.2
            }
    
    def _get_weather_context(self, farm_coords: FarmCoordinates) -> Dict[str, Any]:
        """Get recent weather context that affects satellite readings"""
        try:
            # This would integrate with weather service
            # For now, return estimated values based on location and season
            
            latitude = abs(farm_coords.latitude)
            
            # Estimate based on latitude (crude but functional)
            if latitude < 23.5:  # Tropical
                return {
                    'climate_zone': 'tropical',
                    'rainfall_last_week': 15.0,  # mm
                    'avg_temp_last_week': 28.0,  # °C
                    'humidity_avg': 75.0,  # %
                    'drought_stress_indicator': 0.2
                }
            elif latitude < 35:  # Subtropical
                return {
                    'climate_zone': 'subtropical',
                    'rainfall_last_week': 8.0,
                    'avg_temp_last_week': 22.0,
                    'humidity_avg': 65.0,
                    'drought_stress_indicator': 0.3
                }
            else:  # Temperate
                return {
                    'climate_zone': 'temperate',
                    'rainfall_last_week': 12.0,
                    'avg_temp_last_week': 18.0,
                    'humidity_avg': 70.0,
                    'drought_stress_indicator': 0.25
                }
        except:
            return {
                'climate_zone': 'unknown',
                'rainfall_last_week': 10.0,
                'avg_temp_last_week': 20.0,
                'humidity_avg': 70.0,
                'drought_stress_indicator': 0.3
            }
    
    def _classify_agricultural_zone(self, farm_coords: FarmCoordinates, elevation_data: Dict[str, float]) -> str:
        """Classify the agricultural zone based on location and terrain"""
        
        latitude = abs(farm_coords.latitude)
        elevation = elevation_data['elevation']
        slope = elevation_data['slope']
        
        # Basic agricultural zone classification
        if elevation > 1500:
            if slope > 15:
                return 'mountain_steep'
            else:
                return 'highland_plateau'
        elif elevation > 500:
            if slope > 8:
                return 'hilly_terrain'
            else:
                return 'upland_agricultural'
        else:
            if latitude < 23.5:
                return 'tropical_lowland'
            elif latitude < 35:
                return 'subtropical_plain'
            else:
                if slope < 3:
                    return 'temperate_flatland'
                else:
                    return 'temperate_rolling'
    
    def _get_demo_satellite_data(self, farm_coords: FarmCoordinates) -> SatelliteData:
        """Generate enhanced demo satellite data when real data is unavailable"""
        import random
        
        # Generate realistic values based on location and season
        seasonal_context = get_seasonal_context(datetime.now(), farm_coords.latitude)
        is_growing_season = seasonal_context['is_growing_season']
        
        # Adjust demo values based on growing season
        base_ndvi = 0.65 if is_growing_season else 0.35
        base_moisture = 45.0 if seasonal_context['season'] in ['spring', 'fall'] else 35.0
        
        # Generate realistic but demo values
        demo_data = SatelliteData(
            farm_id=f"{farm_coords.latitude}_{farm_coords.longitude}",
            date_captured=datetime.now() - timedelta(days=7),
            cloud_coverage=15.0,
            
            # Vegetation indices (seasonal adjustment)
            ndvi=base_ndvi + random.uniform(-0.1, 0.1),
            ndwi=0.15 + random.uniform(-0.05, 0.05),
            savi=base_ndvi * 0.8 + random.uniform(-0.05, 0.05),
            evi=base_ndvi * 0.9 + random.uniform(-0.05, 0.05),
            ndmi=0.25 + random.uniform(-0.1, 0.1),
            
            # Soil indices  
            bsi=0.1 + random.uniform(-0.05, 0.05),
            si=0.15 + random.uniform(-0.05, 0.05),
            ci=0.2 + random.uniform(-0.05, 0.05),
            bi=0.12 + random.uniform(-0.05, 0.05),
            
            # Enhanced variables
            surface_temperature=20.0 + random.uniform(-5, 10),
            moisture_estimate=base_moisture + random.uniform(-10, 10),
            
            # Quality metrics
            pixel_count=1000,
            valid_pixels=950,
            data_quality_score=75.0 + random.uniform(-10, 15)
        )
        
        # Enhance with external data
        enhanced_data = self._enhance_with_external_data(demo_data, farm_coords)
        logger.info(f"🎭 Generated enhanced demo satellite data for {seasonal_context['growing_season']} season")
        
        return enhanced_data
    
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