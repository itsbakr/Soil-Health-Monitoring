"""
Unit Tests for Spatial Grid System

Tests:
- Grid generation based on farm size
- Zone calculations
- Coordinate transformations
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.spatial_grid import (
    FarmGrid, 
    ZoneGeometry, 
    ZoneAnalysisResult,
    ZoneStatus,
    calculate_zone_health_status,
    identify_problem_zones,
    create_heatmap_data,
    generate_zone_recommendations
)


class TestFarmGrid:
    """Test farm grid generation"""
    
    def test_small_farm_2x2_grid(self):
        """Test that small farms (<2 ha) get 2x2 grid"""
        grid = FarmGrid(
            center_lat=41.8781,
            center_lng=-87.6298,
            area_hectares=1.5
        )
        
        assert len(grid.zones) == 4  # 2x2 = 4 zones
        assert grid.grid_size == (2, 2)
    
    def test_medium_farm_3x3_grid(self):
        """Test that medium farms (2-10 ha) get 3x3 grid"""
        grid = FarmGrid(
            center_lat=41.8781,
            center_lng=-87.6298,
            area_hectares=5.0
        )
        
        assert len(grid.zones) == 9  # 3x3 = 9 zones
        assert grid.grid_size == (3, 3)
    
    def test_large_farm_4x4_grid(self):
        """Test that large farms (10-50 ha) get 4x4 grid"""
        grid = FarmGrid(
            center_lat=41.8781,
            center_lng=-87.6298,
            area_hectares=25.0
        )
        
        assert len(grid.zones) == 16  # 4x4 = 16 zones
        assert grid.grid_size == (4, 4)
    
    def test_very_large_farm_5x5_grid(self):
        """Test that very large farms (50+ ha) get 5x5 grid"""
        grid = FarmGrid(
            center_lat=41.8781,
            center_lng=-87.6298,
            area_hectares=100.0
        )
        
        assert len(grid.zones) == 25  # 5x5 = 25 zones
        assert grid.grid_size == (5, 5)
    
    def test_zone_ids_unique(self):
        """Test that all zone IDs are unique"""
        grid = FarmGrid(
            center_lat=41.8781,
            center_lng=-87.6298,
            area_hectares=25.0
        )
        
        zone_ids = [z.zone_id for z in grid.zones]
        
        assert len(zone_ids) == len(set(zone_ids))
    
    def test_zone_coordinates_valid(self):
        """Test that zone coordinates are within valid ranges"""
        grid = FarmGrid(
            center_lat=41.8781,
            center_lng=-87.6298,
            area_hectares=10.0
        )
        
        for zone in grid.zones:
            # Latitude should be valid
            assert -90 <= zone.center_lat <= 90
            assert -90 <= zone.bounds['south'] <= 90
            assert -90 <= zone.bounds['north'] <= 90
            
            # Longitude should be valid
            assert -180 <= zone.center_lng <= 180
            assert -180 <= zone.bounds['west'] <= 180
            assert -180 <= zone.bounds['east'] <= 180
            
            # Min should be less than max
            assert zone.bounds['south'] < zone.bounds['north']
            assert zone.bounds['west'] < zone.bounds['east']
    
    def test_zones_cover_farm_area(self):
        """Test that zones collectively cover the farm area"""
        area_hectares = 16.0
        grid = FarmGrid(
            center_lat=41.8781,
            center_lng=-87.6298,
            area_hectares=area_hectares
        )
        
        # Total zone area should approximately equal farm area
        total_zone_area = sum(z.area_hectares for z in grid.zones)
        
        # Allow some tolerance for rounding
        assert abs(total_zone_area - area_hectares) < 0.01
    
    def test_get_zone_by_id(self):
        """Test that get_zone_by_id returns correct zone"""
        grid = FarmGrid(
            center_lat=41.8781,
            center_lng=-87.6298,
            area_hectares=5.0  # 3x3 grid
        )
        
        zone = grid.get_zone_by_id("NW")
        assert zone is not None
        assert zone.zone_id == "NW"
        
        # Non-existent zone
        assert grid.get_zone_by_id("XYZ") is None
    
    def test_zones_centered_around_farm_center(self):
        """Test that zones are centered around the farm center"""
        center_lat = 41.8781
        center_lng = -87.6298
        
        grid = FarmGrid(
            center_lat=center_lat,
            center_lng=center_lng,
            area_hectares=16.0  # 4x4 grid
        )
        
        # Average center of all zones should be close to farm center
        avg_lat = sum(z.center_lat for z in grid.zones) / len(grid.zones)
        avg_lng = sum(z.center_lng for z in grid.zones) / len(grid.zones)
        
        # Allow small tolerance
        assert abs(avg_lat - center_lat) < 0.001
        assert abs(avg_lng - center_lng) < 0.001


class TestZoneGeometry:
    """Test ZoneGeometry dataclass"""
    
    def test_zone_creation(self):
        """Test creating a ZoneGeometry instance"""
        zone = ZoneGeometry(
            zone_id="NW",
            row=0,
            col=0,
            center_lat=41.8781,
            center_lng=-87.6298,
            bounds={
                "north": 41.881,
                "south": 41.875,
                "east": -87.628,
                "west": -87.632
            },
            area_hectares=1.5
        )
        
        assert zone.zone_id == "NW"
        assert zone.center_lat == 41.8781
        assert zone.center_lng == -87.6298
        assert zone.area_hectares == 1.5
    
    def test_zone_to_dict(self):
        """Test Zone to_dict method"""
        zone = ZoneGeometry(
            zone_id="NW",
            row=0,
            col=0,
            center_lat=41.8781,
            center_lng=-87.6298,
            bounds={"north": 41.881, "south": 41.875, "east": -87.628, "west": -87.632},
            area_hectares=1.5
        )
        
        d = zone.to_dict()
        assert d["zone_id"] == "NW"
        assert d["center"]["lat"] == 41.8781


class TestZoneHealth:
    """Test zone health calculation functions"""
    
    def test_calculate_zone_health_status_healthy(self):
        """Test healthy status for high scores"""
        assert calculate_zone_health_status(85) == ZoneStatus.HEALTHY
        assert calculate_zone_health_status(75) == ZoneStatus.HEALTHY
    
    def test_calculate_zone_health_status_moderate(self):
        """Test moderate status"""
        assert calculate_zone_health_status(65) == ZoneStatus.MODERATE
        assert calculate_zone_health_status(55) == ZoneStatus.MODERATE
    
    def test_calculate_zone_health_status_degraded(self):
        """Test degraded status"""
        assert calculate_zone_health_status(45) == ZoneStatus.DEGRADED
        assert calculate_zone_health_status(35) == ZoneStatus.DEGRADED
    
    def test_calculate_zone_health_status_critical(self):
        """Test critical status for low scores"""
        assert calculate_zone_health_status(25) == ZoneStatus.CRITICAL
        assert calculate_zone_health_status(0) == ZoneStatus.CRITICAL


class TestZoneRecommendations:
    """Test zone recommendation generation"""
    
    def test_low_ndvi_generates_alerts(self):
        """Test that low NDVI generates appropriate alerts"""
        alerts, recommendations = generate_zone_recommendations(
            zone_id="NW",
            health_score=30,
            ndvi=0.15,
            moisture=50
        )
        
        assert len(alerts) > 0
        assert any("vegetation" in a.lower() for a in alerts)
    
    def test_low_moisture_generates_alerts(self):
        """Test that low moisture generates irrigation recommendations"""
        alerts, recommendations = generate_zone_recommendations(
            zone_id="NE",
            health_score=50,
            ndvi=0.5,
            moisture=15
        )
        
        assert len(alerts) > 0
        assert any("moisture" in a.lower() for a in alerts)
        assert any("irrigation" in r.lower() for r in recommendations)
    
    def test_high_moisture_generates_alerts(self):
        """Test that high moisture generates drainage recommendations"""
        alerts, recommendations = generate_zone_recommendations(
            zone_id="SE",
            health_score=60,
            ndvi=0.6,
            moisture=85
        )
        
        assert any("excess" in a.lower() for a in alerts)
        assert any("drainage" in r.lower() for r in recommendations)


class TestHeatmap:
    """Test heatmap data creation"""
    
    def test_create_heatmap_data(self):
        """Test heatmap data creation from zones"""
        zones = [
            ZoneAnalysisResult(
                zone_id="NW", row=0, col=0, health_score=85,
                status=ZoneStatus.HEALTHY, ndvi=0.7, ndwi=0.3, moisture=50
            ),
            ZoneAnalysisResult(
                zone_id="NE", row=0, col=1, health_score=45,
                status=ZoneStatus.DEGRADED, ndvi=0.3, ndwi=0.2, moisture=30
            ),
            ZoneAnalysisResult(
                zone_id="SW", row=1, col=0, health_score=75,
                status=ZoneStatus.HEALTHY, ndvi=0.6, ndwi=0.3, moisture=55
            ),
            ZoneAnalysisResult(
                zone_id="SE", row=1, col=1, health_score=65,
                status=ZoneStatus.MODERATE, ndvi=0.5, ndwi=0.25, moisture=45
            ),
        ]
        
        heatmap = create_heatmap_data(zones, (2, 2))
        
        assert len(heatmap) == 2
        assert len(heatmap[0]) == 2
        assert heatmap[0][0] == 85  # NW
        assert heatmap[0][1] == 45  # NE
        assert heatmap[1][0] == 75  # SW
        assert heatmap[1][1] == 65  # SE


class TestProblemZones:
    """Test problem zone identification"""
    
    def test_identify_problem_zones(self):
        """Test identification of problem zones below threshold"""
        zones = [
            ZoneAnalysisResult(
                zone_id="NW", row=0, col=0, health_score=85,
                status=ZoneStatus.HEALTHY, ndvi=0.7, ndwi=0.3, moisture=50
            ),
            ZoneAnalysisResult(
                zone_id="NE", row=0, col=1, health_score=45,
                status=ZoneStatus.DEGRADED, ndvi=0.3, ndwi=0.2, moisture=30
            ),
            ZoneAnalysisResult(
                zone_id="SW", row=1, col=0, health_score=35,
                status=ZoneStatus.DEGRADED, ndvi=0.2, ndwi=0.15, moisture=25
            ),
        ]
        
        problems = identify_problem_zones(zones, threshold=55)
        
        assert len(problems) == 2
        assert "NE" in problems
        assert "SW" in problems
        assert "NW" not in problems


class TestGridEdgeCases:
    """Test edge cases for grid generation"""
    
    def test_minimum_farm_size(self):
        """Test grid generation for minimum farm size"""
        grid = FarmGrid(
            center_lat=41.8781,
            center_lng=-87.6298,
            area_hectares=0.01  # Very small
        )
        
        # Should still generate a valid grid (minimum enforced to 0.1 ha)
        assert len(grid.zones) >= 4
    
    def test_equator_location(self):
        """Test grid generation at equator"""
        grid = FarmGrid(
            center_lat=0.0,
            center_lng=0.0,
            area_hectares=10.0
        )
        
        # Should generate valid grid
        assert len(grid.zones) >= 9
        
        # Zones should be centered around equator
        for zone in grid.zones:
            assert -1 < zone.center_lat < 1
    
    def test_high_latitude_location(self):
        """Test grid generation at high latitude"""
        grid = FarmGrid(
            center_lat=60.0,  # Northern location
            center_lng=0.0,
            area_hectares=10.0
        )
        
        # Should generate valid grid
        assert len(grid.zones) >= 9
        
        # All zones should be in valid lat range
        for zone in grid.zones:
            assert -90 <= zone.center_lat <= 90
    
    def test_near_180_longitude(self):
        """Test grid generation near international date line"""
        grid = FarmGrid(
            center_lat=0.0,
            center_lng=179.0,  # Near date line
            area_hectares=5.0
        )
        
        # Should generate valid grid
        assert len(grid.zones) >= 9

