"""
Spatial Grid System for Farm Zone Analysis

This module provides functionality to:
- Auto-generate grid zones based on farm size
- Create zone geometries for satellite analysis
- Support precision agriculture with zone-specific recommendations
"""

import math
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ZoneStatus(str, Enum):
    """Health status for a zone"""
    HEALTHY = "healthy"
    MODERATE = "moderate"
    DEGRADED = "degraded"
    CRITICAL = "critical"


class SatelliteSource(str, Enum):
    """Satellite data sources with their resolutions"""
    SENTINEL_2 = "COPERNICUS/S2_SR_HARMONIZED"  # 10m resolution
    LANDSAT_8 = "LANDSAT/LC08/C02/T1_L2"  # 30m resolution
    LANDSAT_9 = "LANDSAT/LC09/C02/T1_L2"  # 30m resolution


@dataclass
class ZoneGeometry:
    """Represents a single zone's geometry"""
    zone_id: str
    row: int
    col: int
    center_lat: float
    center_lng: float
    bounds: Dict[str, float]  # {north, south, east, west}
    area_hectares: float
    
    def to_ee_geometry(self):
        """Convert to Earth Engine geometry"""
        import ee
        return ee.Geometry.Rectangle([
            self.bounds['west'],
            self.bounds['south'],
            self.bounds['east'],
            self.bounds['north']
        ])
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "zone_id": self.zone_id,
            "row": self.row,
            "col": self.col,
            "center": {"lat": self.center_lat, "lng": self.center_lng},
            "bounds": self.bounds,
            "area_hectares": self.area_hectares
        }


@dataclass
class ZoneAnalysisResult:
    """Analysis result for a single zone"""
    zone_id: str
    row: int
    col: int
    health_score: float  # 0-100
    status: ZoneStatus
    ndvi: float
    ndwi: float
    moisture: float
    alerts: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    data_quality: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "zone_id": self.zone_id,
            "row": self.row,
            "col": self.col,
            "health": self.health_score,
            "status": self.status.value,
            "ndvi": round(self.ndvi, 3),
            "ndwi": round(self.ndwi, 3),
            "moisture": round(self.moisture, 1),
            "alerts": self.alerts,
            "recommendations": self.recommendations,
            "data_quality": round(self.data_quality, 1)
        }


@dataclass
class FarmGridAnalysis:
    """Complete grid analysis for a farm"""
    farm_id: str
    center_lat: float
    center_lng: float
    area_hectares: float
    grid_size: Tuple[int, int]  # (rows, cols)
    satellite_source: SatelliteSource
    resolution_meters: int
    overall_health: float
    zones: List[ZoneAnalysisResult]
    problem_zones: List[str]
    heatmap_data: List[List[float]]
    analysis_timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "farm_id": self.farm_id,
            "center": {"lat": self.center_lat, "lng": self.center_lng},
            "area_hectares": self.area_hectares,
            "grid_size": {"rows": self.grid_size[0], "cols": self.grid_size[1]},
            "satellite_source": self.satellite_source.value,
            "resolution_meters": self.resolution_meters,
            "overall_health": round(self.overall_health, 1),
            "zones": [z.to_dict() for z in self.zones],
            "problem_zones": self.problem_zones,
            "heatmap_data": self.heatmap_data,
            "analysis_timestamp": self.analysis_timestamp
        }


class FarmGrid:
    """
    Spatial grid system for farm zone analysis.
    
    Auto-generates appropriate grid based on farm size:
    - < 2 ha: 2x2 grid (4 zones) using Sentinel-2 (10m)
    - 2-10 ha: 3x3 grid (9 zones) using Sentinel-2 (10m)
    - 10-50 ha: 4x4 grid (16 zones) using Landsat (30m)
    - 50+ ha: 5x5 grid (25 zones) using Landsat (30m)
    """
    
    # Grid configuration based on farm size
    GRID_CONFIG = [
        {"max_hectares": 2, "grid": (2, 2), "satellite": SatelliteSource.SENTINEL_2, "resolution": 10},
        {"max_hectares": 10, "grid": (3, 3), "satellite": SatelliteSource.SENTINEL_2, "resolution": 10},
        {"max_hectares": 50, "grid": (4, 4), "satellite": SatelliteSource.LANDSAT_8, "resolution": 30},
        {"max_hectares": float('inf'), "grid": (5, 5), "satellite": SatelliteSource.LANDSAT_8, "resolution": 30},
    ]
    
    # Zone naming convention (compass-based for intuitive understanding)
    ZONE_NAMES_2x2 = [["NW", "NE"], ["SW", "SE"]]
    ZONE_NAMES_3x3 = [["NW", "N", "NE"], ["W", "C", "E"], ["SW", "S", "SE"]]
    ZONE_NAMES_4x4 = [
        ["NW1", "NW2", "NE1", "NE2"],
        ["NW3", "NW4", "NE3", "NE4"],
        ["SW1", "SW2", "SE1", "SE2"],
        ["SW3", "SW4", "SE3", "SE4"]
    ]
    ZONE_NAMES_5x5 = [
        ["NW1", "NW2", "N1", "NE1", "NE2"],
        ["NW3", "NW4", "N2", "NE3", "NE4"],
        ["W1", "W2", "C", "E1", "E2"],
        ["SW1", "SW2", "S1", "SE1", "SE2"],
        ["SW3", "SW4", "S2", "SE3", "SE4"]
    ]
    
    def __init__(self, center_lat: float, center_lng: float, area_hectares: float):
        """
        Initialize farm grid.
        
        Args:
            center_lat: Farm center latitude
            center_lng: Farm center longitude
            area_hectares: Total farm area in hectares
        """
        self.center_lat = center_lat
        self.center_lng = center_lng
        self.area_hectares = max(0.1, area_hectares)  # Minimum 0.1 ha
        
        # Determine grid configuration
        self.config = self._get_grid_config()
        self.grid_size = self.config["grid"]
        self.satellite_source = self.config["satellite"]
        self.resolution = self.config["resolution"]
        
        # Generate zone geometries
        self.zones: List[ZoneGeometry] = self._generate_zones()
        
        logger.info(
            f"🗺️ Created {self.grid_size[0]}x{self.grid_size[1]} grid for "
            f"{self.area_hectares:.1f} ha farm using {self.satellite_source.name}"
        )
    
    def _get_grid_config(self) -> Dict[str, Any]:
        """Get appropriate grid configuration based on farm size"""
        for config in self.GRID_CONFIG:
            if self.area_hectares <= config["max_hectares"]:
                return config
        return self.GRID_CONFIG[-1]
    
    def _get_zone_names(self) -> List[List[str]]:
        """Get zone naming grid based on grid size"""
        rows, cols = self.grid_size
        if rows == 2 and cols == 2:
            return self.ZONE_NAMES_2x2
        elif rows == 3 and cols == 3:
            return self.ZONE_NAMES_3x3
        elif rows == 4 and cols == 4:
            return self.ZONE_NAMES_4x4
        elif rows == 5 and cols == 5:
            return self.ZONE_NAMES_5x5
        else:
            # Generate generic names for custom grids
            return [[f"R{r}C{c}" for c in range(cols)] for r in range(rows)]
    
    def _generate_zones(self) -> List[ZoneGeometry]:
        """Generate zone geometries covering the farm area"""
        zones = []
        rows, cols = self.grid_size
        zone_names = self._get_zone_names()
        
        # Calculate farm dimensions (assuming roughly square for simplicity)
        # Area = side^2, so side = sqrt(area)
        farm_side_m = math.sqrt(self.area_hectares * 10000)  # Convert ha to m²
        
        # Convert to degrees (approximate)
        lat_degree_m = 111320  # meters per degree latitude
        lng_degree_m = 111320 * math.cos(math.radians(self.center_lat))
        
        farm_half_lat = (farm_side_m / 2) / lat_degree_m
        farm_half_lng = (farm_side_m / 2) / lng_degree_m
        
        # Calculate zone dimensions
        zone_height = (farm_half_lat * 2) / rows
        zone_width = (farm_half_lng * 2) / cols
        zone_area = self.area_hectares / (rows * cols)
        
        # Generate zones from top-left (NW) to bottom-right (SE)
        for row in range(rows):
            for col in range(cols):
                # Calculate zone bounds
                north = self.center_lat + farm_half_lat - (row * zone_height)
                south = north - zone_height
                west = self.center_lng - farm_half_lng + (col * zone_width)
                east = west + zone_width
                
                # Calculate zone center
                zone_center_lat = (north + south) / 2
                zone_center_lng = (east + west) / 2
                
                zone = ZoneGeometry(
                    zone_id=zone_names[row][col],
                    row=row,
                    col=col,
                    center_lat=zone_center_lat,
                    center_lng=zone_center_lng,
                    bounds={
                        "north": north,
                        "south": south,
                        "east": east,
                        "west": west
                    },
                    area_hectares=zone_area
                )
                zones.append(zone)
        
        return zones
    
    def get_zone_by_id(self, zone_id: str) -> Optional[ZoneGeometry]:
        """Get a specific zone by its ID"""
        for zone in self.zones:
            if zone.zone_id == zone_id:
                return zone
        return None
    
    def get_zone_at_position(self, row: int, col: int) -> Optional[ZoneGeometry]:
        """Get zone at specific grid position"""
        for zone in self.zones:
            if zone.row == row and zone.col == col:
                return zone
        return None
    
    def get_all_zone_geometries(self) -> List[Dict[str, Any]]:
        """Get all zone geometries as dictionaries"""
        return [zone.to_dict() for zone in self.zones]
    
    def get_optimal_satellite_collection(self) -> str:
        """Get the optimal satellite collection ID for this farm size"""
        return self.satellite_source.value
    
    def get_resolution(self) -> int:
        """Get the satellite resolution in meters"""
        return self.resolution
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert grid to dictionary representation"""
        return {
            "center": {"lat": self.center_lat, "lng": self.center_lng},
            "area_hectares": self.area_hectares,
            "grid_size": {"rows": self.grid_size[0], "cols": self.grid_size[1]},
            "satellite_source": self.satellite_source.value,
            "resolution_meters": self.resolution,
            "total_zones": len(self.zones),
            "zones": self.get_all_zone_geometries()
        }


def get_optimal_satellite(area_hectares: float) -> Tuple[str, int]:
    """
    Get optimal satellite source based on farm area.
    
    Args:
        area_hectares: Farm area in hectares
        
    Returns:
        Tuple of (satellite_collection_id, resolution_meters)
    """
    if area_hectares < 10:
        return (SatelliteSource.SENTINEL_2.value, 10)
    return (SatelliteSource.LANDSAT_8.value, 30)


def calculate_zone_health_status(health_score: float) -> ZoneStatus:
    """
    Determine zone health status from score.
    
    Args:
        health_score: Health score (0-100)
        
    Returns:
        ZoneStatus enum value
    """
    if health_score >= 75:
        return ZoneStatus.HEALTHY
    elif health_score >= 55:
        return ZoneStatus.MODERATE
    elif health_score >= 35:
        return ZoneStatus.DEGRADED
    else:
        return ZoneStatus.CRITICAL


def generate_zone_recommendations(
    zone_id: str,
    health_score: float,
    ndvi: float,
    moisture: float
) -> Tuple[List[str], List[str]]:
    """
    Generate alerts and recommendations for a zone.
    
    Args:
        zone_id: Zone identifier
        health_score: Zone health score
        ndvi: NDVI value
        moisture: Moisture percentage
        
    Returns:
        Tuple of (alerts, recommendations)
    """
    alerts = []
    recommendations = []
    
    # NDVI-based alerts
    if ndvi < 0.2:
        alerts.append(f"Critical vegetation stress in {zone_id}")
        recommendations.append("Investigate for pest damage or disease")
        recommendations.append("Consider soil testing for this area")
    elif ndvi < 0.4:
        alerts.append(f"Low vegetation health in {zone_id}")
        recommendations.append("Monitor closely for improvement")
    
    # Moisture-based alerts
    if moisture < 20:
        alerts.append(f"Very low soil moisture in {zone_id}")
        recommendations.append("Prioritize irrigation for this zone")
    elif moisture < 35:
        alerts.append(f"Low moisture in {zone_id}")
        recommendations.append("Consider targeted watering")
    elif moisture > 80:
        alerts.append(f"Excess moisture in {zone_id}")
        recommendations.append("Check drainage in this area")
    
    # Overall health recommendations
    if health_score < 40:
        recommendations.append("This zone needs immediate attention")
    elif health_score < 60:
        recommendations.append("Monitor this zone weekly")
    
    return alerts, recommendations


def create_heatmap_data(zones: List[ZoneAnalysisResult], grid_size: Tuple[int, int]) -> List[List[float]]:
    """
    Create 2D heatmap data from zone analysis results.
    
    Args:
        zones: List of zone analysis results
        grid_size: (rows, cols) tuple
        
    Returns:
        2D list of health scores for heatmap visualization
    """
    rows, cols = grid_size
    heatmap = [[0.0 for _ in range(cols)] for _ in range(rows)]
    
    for zone in zones:
        if 0 <= zone.row < rows and 0 <= zone.col < cols:
            heatmap[zone.row][zone.col] = zone.health_score
    
    return heatmap


def identify_problem_zones(zones: List[ZoneAnalysisResult], threshold: float = 55.0) -> List[str]:
    """
    Identify zones with health scores below threshold.
    
    Args:
        zones: List of zone analysis results
        threshold: Health score threshold (default 55)
        
    Returns:
        List of problem zone IDs
    """
    return [zone.zone_id for zone in zones if zone.health_score < threshold]

