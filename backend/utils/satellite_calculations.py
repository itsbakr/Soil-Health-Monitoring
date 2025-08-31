"""
Satellite Data Processing Utilities

This module contains utility functions for processing satellite data,
coordinate transformations, and statistical calculations.
"""

import math
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import ee


@dataclass
class PixelInfo:
    """Information about satellite pixels covering a farm area"""
    pixel_count: int
    coverage_area_hectares: float
    center_coordinates: Tuple[float, float]  # (lat, lon)
    corner_coordinates: List[Tuple[float, float]]  # [(lat, lon), ...]


def calculate_farm_pixels(latitude: float, longitude: float, area_hectares: float) -> PixelInfo:
    """
    Calculate how many Landsat pixels (30m x 30m) cover a farm area
    
    Args:
        latitude: Farm center latitude
        longitude: Farm center longitude
        area_hectares: Farm area in hectares
        
    Returns:
        PixelInfo object with pixel count and coordinates
    """
    # Landsat pixel size is 30m x 30m = 900 m² = 0.09 hectares
    pixel_area_hectares = 0.09
    pixel_count = math.ceil(area_hectares / pixel_area_hectares)
    
    # Calculate approximate coverage area (actual pixels might be slightly larger)
    coverage_area = pixel_count * pixel_area_hectares
    
    # For simplicity, assume farm is roughly circular
    # Calculate radius to determine corner coordinates
    farm_radius_m = math.sqrt(area_hectares * 10000 / math.pi)
    
    # Convert radius from meters to degrees (rough approximation)
    lat_degree_m = 111320  # meters per degree latitude
    lon_degree_m = 111320 * math.cos(math.radians(latitude))  # varies with latitude
    
    radius_lat = farm_radius_m / lat_degree_m
    radius_lon = farm_radius_m / lon_degree_m
    
    # Calculate corner coordinates (simple bounding box)
    corners = [
        (latitude + radius_lat, longitude - radius_lon),  # NW
        (latitude + radius_lat, longitude + radius_lon),  # NE
        (latitude - radius_lat, longitude + radius_lon),  # SE
        (latitude - radius_lat, longitude - radius_lon),  # SW
    ]
    
    return PixelInfo(
        pixel_count=pixel_count,
        coverage_area_hectares=coverage_area,
        center_coordinates=(latitude, longitude),
        corner_coordinates=corners
    )


def meters_to_degrees(meters: float, latitude: float) -> Tuple[float, float]:
    """
    Convert meters to degrees at a given latitude
    
    Args:
        meters: Distance in meters
        latitude: Latitude for longitude calculation
        
    Returns:
        Tuple of (lat_degrees, lon_degrees)
    """
    lat_degree_m = 111320  # meters per degree latitude (constant)
    lon_degree_m = 111320 * math.cos(math.radians(latitude))  # varies with latitude
    
    lat_degrees = meters / lat_degree_m
    lon_degrees = meters / lon_degree_m
    
    return (lat_degrees, lon_degrees)


def degrees_to_meters(lat_degrees: float, lon_degrees: float, latitude: float) -> float:
    """
    Convert degree differences to meters at a given latitude
    
    Args:
        lat_degrees: Latitude difference in degrees
        lon_degrees: Longitude difference in degrees
        latitude: Reference latitude
        
    Returns:
        Distance in meters
    """
    lat_degree_m = 111320
    lon_degree_m = 111320 * math.cos(math.radians(latitude))
    
    lat_meters = lat_degrees * lat_degree_m
    lon_meters = lon_degrees * lon_degree_m
    
    # Calculate Euclidean distance
    return math.sqrt(lat_meters**2 + lon_meters**2)


def calculate_ndvi_trend(ndvi_values: List[float], dates: List[datetime]) -> Dict[str, float]:
    """
    Calculate NDVI trend analysis
    
    Args:
        ndvi_values: List of NDVI values over time
        dates: Corresponding dates
        
    Returns:
        Dictionary with trend statistics
    """
    if len(ndvi_values) < 2:
        return {
            "trend": 0.0,
            "average": ndvi_values[0] if ndvi_values else 0.0,
            "improvement": 0.0
        }
    
    # Simple linear trend calculation
    n = len(ndvi_values)
    x_values = list(range(n))  # Time series indices
    
    # Calculate means
    x_mean = sum(x_values) / n
    y_mean = sum(ndvi_values) / n
    
    # Calculate slope (trend)
    numerator = sum((x_values[i] - x_mean) * (ndvi_values[i] - y_mean) for i in range(n))
    denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
    
    trend = numerator / denominator if denominator != 0 else 0.0
    
    # Calculate improvement percentage
    if ndvi_values[0] != 0:
        improvement = ((ndvi_values[-1] - ndvi_values[0]) / abs(ndvi_values[0])) * 100
    else:
        improvement = 0.0
    
    return {
        "trend": round(trend, 4),
        "average": round(y_mean, 3),
        "improvement": round(improvement, 1)
    }


def classify_vegetation_health(ndvi: float) -> Dict[str, Any]:
    """
    Classify vegetation health based on NDVI value
    
    Args:
        ndvi: NDVI value (-1 to 1)
        
    Returns:
        Dictionary with classification and recommendations
    """
    if ndvi >= 0.6:
        classification = "Excellent"
        color = "green"
        description = "Very healthy vegetation with dense green cover"
        recommendations = ["Maintain current practices", "Monitor for optimal harvest timing"]
    elif ndvi >= 0.4:
        classification = "Good"
        color = "lightgreen"
        description = "Healthy vegetation with good growth"
        recommendations = ["Continue monitoring", "Consider nutrient optimization"]
    elif ndvi >= 0.2:
        classification = "Moderate"
        color = "yellow"
        description = "Moderate vegetation health, some stress indicators"
        recommendations = ["Check soil moisture", "Consider fertilization", "Monitor for pests"]
    elif ndvi >= 0.1:
        classification = "Poor"
        color = "orange"
        description = "Stressed vegetation, intervention needed"
        recommendations = ["Immediate soil analysis", "Check irrigation", "Pest/disease inspection"]
    else:
        classification = "Critical"
        color = "red"
        description = "Very poor vegetation health or bare soil"
        recommendations = ["Urgent intervention required", "Soil rehabilitation", "Expert consultation"]
    
    return {
        "classification": classification,
        "color": color,
        "description": description,
        "recommendations": recommendations,
        "score": min(100, max(0, (ndvi + 1) * 50))  # Convert -1,1 to 0,100
    }


def calculate_soil_salinity_level(si_value: float) -> Dict[str, Any]:
    """
    Estimate soil salinity level from Salinity Index
    
    Args:
        si_value: Salinity Index value
        
    Returns:
        Dictionary with salinity classification
    """
    # These thresholds are simplified and should be calibrated with ground truth data
    if si_value <= 1.2:
        level = "Low"
        description = "Normal salinity levels, suitable for most crops"
        impact = "No negative impact expected"
        color = "green"
    elif si_value <= 2.0:
        level = "Moderate"
        description = "Slightly elevated salinity, monitor sensitive crops"
        impact = "May affect salt-sensitive crops"
        color = "yellow"
    elif si_value <= 3.0:
        level = "High"
        description = "High salinity levels, crop selection important"
        impact = "Significant impact on crop yields"
        color = "orange"
    else:
        level = "Very High"
        description = "Excessive salinity, soil treatment needed"
        impact = "Severe limitation for crop production"
        color = "red"
    
    return {
        "level": level,
        "description": description,
        "impact": impact,
        "color": color,
        "value": round(si_value, 3)
    }


def estimate_soil_moisture(ndmi: float) -> Dict[str, Any]:
    """
    Estimate soil moisture from NDMI (Normalized Difference Moisture Index)
    
    Args:
        ndmi: NDMI value (-1 to 1)
        
    Returns:
        Dictionary with moisture classification
    """
    # Convert NDMI to percentage (simplified)
    moisture_percent = max(0, min(100, (ndmi + 1) * 50))
    
    if moisture_percent >= 60:
        level = "High"
        description = "Adequate to high soil moisture"
        status = "Optimal for crop growth"
        color = "blue"
    elif moisture_percent >= 40:
        level = "Moderate"
        description = "Moderate soil moisture levels"
        status = "Good for most crops"
        color = "lightblue"
    elif moisture_percent >= 20:
        level = "Low"
        description = "Low soil moisture, irrigation recommended"
        status = "May stress sensitive crops"
        color = "yellow"
    else:
        level = "Very Low"
        description = "Very low soil moisture, immediate action needed"
        status = "Crop stress likely"
        color = "red"
    
    return {
        "level": level,
        "percentage": round(moisture_percent, 1),
        "description": description,
        "status": status,
        "color": color
    }


def calculate_temporal_variance(values: List[float]) -> Dict[str, float]:
    """
    Calculate temporal variance and stability metrics
    
    Args:
        values: List of values over time
        
    Returns:
        Dictionary with variance statistics
    """
    if len(values) < 2:
        return {"variance": 0.0, "std_dev": 0.0, "stability": 100.0}
    
    n = len(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / (n - 1)
    std_dev = math.sqrt(variance)
    
    # Stability score (lower variance = higher stability)
    if mean != 0:
        cv = (std_dev / abs(mean)) * 100  # Coefficient of variation
        stability = max(0, 100 - cv)
    else:
        stability = 0.0
    
    return {
        "variance": round(variance, 4),
        "std_dev": round(std_dev, 3),
        "stability": round(stability, 1)
    } 

def add_ndvi(image: ee.Image) -> ee.Image:
    """Add NDVI band to image (NIR - Red) / (NIR + Red)"""
    nir = image.select('SR_B5')
    red = image.select('SR_B4')
    ndvi_numerator = nir.subtract(red)
    ndvi_denominator = nir.add(red)
    ndvi_safe = ndvi_denominator.where(ndvi_denominator.eq(0), 1)
    ndvi = ndvi_numerator.divide(ndvi_safe).rename('NDVI')
    ndvi = ndvi.updateMask(ndvi_denominator.neq(0))
    return image.addBands(ndvi)

def add_ndwi(image: ee.Image) -> ee.Image:
    """Add NDWI band to image (Green - NIR) / (Green + NIR)"""
    green = image.select('SR_B3')
    nir = image.select('SR_B5')
    ndwi = green.subtract(nir).divide(green.add(nir)).rename('NDWI')
    return image.addBands(ndwi)

def add_savi(image: ee.Image, L: float = 0.5) -> ee.Image:
    """Add SAVI band to image ((NIR - Red) / (NIR + Red + L)) * (1 + L)"""
    nir = image.select('SR_B5')
    red = image.select('SR_B4')
    savi = nir.subtract(red).divide(nir.add(red).add(L)).multiply(1 + L).rename('SAVI')
    return image.addBands(savi)

def add_evi(image: ee.Image) -> ee.Image:
    """Add EVI band to image (NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1) * 2.5"""
    nir = image.select('SR_B5')
    red = image.select('SR_B4')
    blue = image.select('SR_B2')
    evi = nir.subtract(red).divide(
        nir.add(red.multiply(6)).subtract(blue.multiply(7.5)).add(1)
    ).multiply(2.5).rename('EVI')
    return image.addBands(evi)

def add_ndmi(image: ee.Image) -> ee.Image:
    """Add NDMI band to image (NIR - SWIR1) / (NIR + SWIR1)"""
    nir = image.select('SR_B5')
    swir1 = image.select('SR_B6')
    ndmi = nir.subtract(swir1).divide(nir.add(swir1)).rename('NDMI')
    return image.addBands(ndmi)

def add_bsi(image: ee.Image) -> ee.Image:
    """Add BSI band to image ((SWIR1 + Red) - (NIR + Blue)) / ((SWIR1 + Red) + (NIR + Blue))"""
    swir1 = image.select('SR_B6')
    red = image.select('SR_B4')
    nir = image.select('SR_B5')
    blue = image.select('SR_B2')
    bsi = swir1.add(red).subtract(nir).subtract(blue).divide(
        swir1.add(red).add(nir).add(blue)
    ).rename('BSI')
    return image.addBands(bsi)

def add_si(image: ee.Image) -> ee.Image:
    """Add SI (Salinity Index) band to image (Green * Red) / Blue"""
    green = image.select('SR_B3')
    red = image.select('SR_B4')
    blue = image.select('SR_B2')
    si = green.multiply(red).divide(blue).rename('SI')
    return image.addBands(si)

def add_ci(image: ee.Image) -> ee.Image:
    """Add CI (Coloration Index) band to image (Red - Green) / (Red + Green)"""
    red = image.select('SR_B4')
    green = image.select('SR_B3')
    ci = red.subtract(green).divide(red.add(green)).rename('CI')
    return image.addBands(ci)

def add_bi(image: ee.Image) -> ee.Image:
    """Add BI (Brightness Index) band to image (Blue + Green + Red) / 3"""
    blue = image.select('SR_B2')
    green = image.select('SR_B3')
    red = image.select('SR_B4')
    bi = blue.add(green).add(red).divide(3).rename('BI')
    return image.addBands(bi) 