"""
Zone Calculations Utility

Provides per-zone statistical calculations for spatial analysis.
"""

import math
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ZoneStatistics:
    """Statistical summary for a zone"""
    mean: float
    std_dev: float
    min_val: float
    max_val: float
    median: float
    valid_pixels: int
    total_pixels: int
    quality_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "mean": round(self.mean, 4),
            "std_dev": round(self.std_dev, 4),
            "min": round(self.min_val, 4),
            "max": round(self.max_val, 4),
            "median": round(self.median, 4),
            "valid_pixels": self.valid_pixels,
            "total_pixels": self.total_pixels,
            "quality_score": round(self.quality_score, 1)
        }


def calculate_zone_statistics(values: List[float]) -> ZoneStatistics:
    """
    Calculate comprehensive statistics for a zone.
    
    Args:
        values: List of pixel values for the zone
        
    Returns:
        ZoneStatistics object with statistical summary
    """
    if not values:
        return ZoneStatistics(
            mean=0.0, std_dev=0.0, min_val=0.0, max_val=0.0,
            median=0.0, valid_pixels=0, total_pixels=0, quality_score=0.0
        )
    
    # Filter out None and NaN values
    valid_values = [v for v in values if v is not None and not math.isnan(v)]
    
    if not valid_values:
        return ZoneStatistics(
            mean=0.0, std_dev=0.0, min_val=0.0, max_val=0.0,
            median=0.0, valid_pixels=0, total_pixels=len(values), quality_score=0.0
        )
    
    n = len(valid_values)
    mean = sum(valid_values) / n
    
    # Standard deviation
    if n > 1:
        variance = sum((x - mean) ** 2 for x in valid_values) / (n - 1)
        std_dev = math.sqrt(variance)
    else:
        std_dev = 0.0
    
    # Median
    sorted_values = sorted(valid_values)
    mid = n // 2
    if n % 2 == 0:
        median = (sorted_values[mid - 1] + sorted_values[mid]) / 2
    else:
        median = sorted_values[mid]
    
    # Quality score based on valid pixel ratio and consistency
    valid_ratio = n / len(values) if values else 0
    consistency = 1 - min(std_dev / abs(mean) if mean != 0 else 0, 1)
    quality_score = (valid_ratio * 0.6 + consistency * 0.4) * 100
    
    return ZoneStatistics(
        mean=mean,
        std_dev=std_dev,
        min_val=min(valid_values),
        max_val=max(valid_values),
        median=median,
        valid_pixels=n,
        total_pixels=len(values),
        quality_score=quality_score
    )


def calculate_zone_health_score(
    ndvi: float,
    ndwi: float,
    moisture: float,
    bsi: float = 0.0
) -> float:
    """
    Calculate overall health score for a zone.
    
    Args:
        ndvi: Normalized Difference Vegetation Index (-1 to 1)
        ndwi: Normalized Difference Water Index (-1 to 1)
        moisture: Moisture estimate (0-100)
        bsi: Bare Soil Index (lower is better)
        
    Returns:
        Health score (0-100)
    """
    # NDVI contribution (40% weight) - scale from -1,1 to 0,100
    ndvi_score = max(0, min(100, (ndvi + 1) * 50))
    
    # Moisture contribution (30% weight) - optimal is 40-60%
    if 40 <= moisture <= 60:
        moisture_score = 100
    elif moisture < 40:
        moisture_score = max(0, moisture * 2.5)  # Scale 0-40 to 0-100
    else:
        moisture_score = max(0, 100 - (moisture - 60) * 2.5)  # Penalty for excess
    
    # NDWI contribution (20% weight) - scale from -1,1 to 0,100
    ndwi_score = max(0, min(100, (ndwi + 0.5) * 100))  # Shift for water index
    
    # BSI contribution (10% weight) - lower is better
    bsi_score = max(0, min(100, 100 - (bsi + 1) * 50))
    
    # Weighted average
    health_score = (
        ndvi_score * 0.40 +
        moisture_score * 0.30 +
        ndwi_score * 0.20 +
        bsi_score * 0.10
    )
    
    return round(max(0, min(100, health_score)), 1)


def estimate_zone_moisture(ndmi: float, ndwi: float) -> float:
    """
    Estimate soil moisture percentage from spectral indices.
    
    Args:
        ndmi: Normalized Difference Moisture Index
        ndwi: Normalized Difference Water Index
        
    Returns:
        Estimated moisture percentage (0-100)
    """
    # Weighted combination of moisture indices
    # NDMI is more reliable for soil moisture, NDWI for surface water
    combined = ndmi * 0.7 + ndwi * 0.3
    
    # Scale from typical range (-0.5 to 0.5) to percentage
    moisture = (combined + 0.5) * 100
    
    return max(0, min(100, moisture))


def classify_zone_condition(
    health_score: float,
    ndvi: float,
    moisture: float
) -> Dict[str, Any]:
    """
    Classify zone condition with human-readable descriptions.
    
    Args:
        health_score: Zone health score (0-100)
        ndvi: NDVI value
        moisture: Moisture percentage
        
    Returns:
        Classification dictionary with status, description, and urgency
    """
    # Determine primary status
    if health_score >= 75:
        status = "healthy"
        emoji = "🟢"
        description = "This area is thriving"
        urgency = "low"
    elif health_score >= 55:
        status = "moderate"
        emoji = "🟡"
        description = "This area needs monitoring"
        urgency = "medium"
    elif health_score >= 35:
        status = "degraded"
        emoji = "🟠"
        description = "This area needs attention"
        urgency = "high"
    else:
        status = "critical"
        emoji = "🔴"
        description = "This area needs immediate action"
        urgency = "critical"
    
    # Add specific issues
    issues = []
    if ndvi < 0.3:
        issues.append("Low vegetation")
    if moisture < 25:
        issues.append("Dry soil")
    elif moisture > 75:
        issues.append("Excess moisture")
    
    return {
        "status": status,
        "emoji": emoji,
        "description": description,
        "urgency": urgency,
        "issues": issues,
        "health_score": health_score
    }


def generate_zone_action(
    zone_id: str,
    condition: Dict[str, Any],
    ndvi: float,
    moisture: float
) -> Optional[Dict[str, Any]]:
    """
    Generate actionable recommendation for a zone.
    
    Args:
        zone_id: Zone identifier
        condition: Zone condition classification
        ndvi: NDVI value
        moisture: Moisture percentage
        
    Returns:
        Action dictionary or None if no action needed
    """
    if condition["urgency"] == "low":
        return None
    
    actions = []
    
    # Moisture-based actions
    if moisture < 25:
        actions.append({
            "action": "irrigate",
            "description": f"Water zone {zone_id} within 3 days",
            "priority": "high" if moisture < 15 else "medium",
            "icon": "💧"
        })
    elif moisture > 75:
        actions.append({
            "action": "drainage",
            "description": f"Check drainage in zone {zone_id}",
            "priority": "medium",
            "icon": "🚰"
        })
    
    # Vegetation-based actions
    if ndvi < 0.2:
        actions.append({
            "action": "investigate",
            "description": f"Inspect zone {zone_id} for pest/disease",
            "priority": "high",
            "icon": "🔍"
        })
    elif ndvi < 0.35:
        actions.append({
            "action": "fertilize",
            "description": f"Consider fertilizing zone {zone_id}",
            "priority": "medium",
            "icon": "🌱"
        })
    
    if actions:
        # Return highest priority action
        actions.sort(key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x["priority"], 2))
        return actions[0]
    
    return None


def calculate_farm_overall_health(zone_scores: List[float], zone_areas: List[float] = None) -> float:
    """
    Calculate overall farm health from zone scores.
    
    Args:
        zone_scores: List of zone health scores
        zone_areas: Optional list of zone areas for weighted average
        
    Returns:
        Overall farm health score (0-100)
    """
    if not zone_scores:
        return 0.0
    
    if zone_areas and len(zone_areas) == len(zone_scores):
        # Weighted average by area
        total_area = sum(zone_areas)
        if total_area > 0:
            weighted_sum = sum(s * a for s, a in zip(zone_scores, zone_areas))
            return round(weighted_sum / total_area, 1)
    
    # Simple average
    return round(sum(zone_scores) / len(zone_scores), 1)


def calculate_spatial_variability(zone_scores: List[float]) -> Dict[str, float]:
    """
    Calculate spatial variability metrics across zones.
    
    Args:
        zone_scores: List of zone health scores
        
    Returns:
        Dictionary with variability metrics
    """
    if len(zone_scores) < 2:
        return {
            "coefficient_of_variation": 0.0,
            "range": 0.0,
            "uniformity_score": 100.0
        }
    
    mean = sum(zone_scores) / len(zone_scores)
    variance = sum((s - mean) ** 2 for s in zone_scores) / (len(zone_scores) - 1)
    std_dev = math.sqrt(variance)
    
    cv = (std_dev / mean * 100) if mean > 0 else 0
    score_range = max(zone_scores) - min(zone_scores)
    
    # Uniformity score: 100 = perfectly uniform, 0 = highly variable
    uniformity = max(0, 100 - cv)
    
    return {
        "coefficient_of_variation": round(cv, 1),
        "range": round(score_range, 1),
        "uniformity_score": round(uniformity, 1),
        "std_dev": round(std_dev, 1),
        "mean": round(mean, 1)
    }


def get_compass_direction(row: int, col: int, total_rows: int, total_cols: int) -> str:
    """
    Get compass direction for a zone position.
    
    Args:
        row: Zone row (0-indexed, 0 = north)
        col: Zone column (0-indexed, 0 = west)
        total_rows: Total number of rows
        total_cols: Total number of columns
        
    Returns:
        Compass direction string (e.g., "northeast", "center")
    """
    # Determine vertical position
    if total_rows == 1:
        v_pos = "center"
    elif row < total_rows / 3:
        v_pos = "north"
    elif row >= total_rows * 2 / 3:
        v_pos = "south"
    else:
        v_pos = "center"
    
    # Determine horizontal position
    if total_cols == 1:
        h_pos = "center"
    elif col < total_cols / 3:
        h_pos = "west"
    elif col >= total_cols * 2 / 3:
        h_pos = "east"
    else:
        h_pos = "center"
    
    # Combine
    if v_pos == "center" and h_pos == "center":
        return "center"
    elif v_pos == "center":
        return h_pos
    elif h_pos == "center":
        return v_pos
    else:
        return f"{v_pos}{h_pos}"


def format_zone_summary_for_farmer(
    problem_zones: List[Dict[str, Any]],
    overall_health: float
) -> str:
    """
    Create farmer-friendly summary of zone analysis.
    
    Args:
        problem_zones: List of problem zone data
        overall_health: Overall farm health score
        
    Returns:
        Human-readable summary string
    """
    if overall_health >= 75:
        status_text = "Your farm is healthy! 🌱"
    elif overall_health >= 55:
        status_text = "Your farm is doing okay, but some areas need attention."
    elif overall_health >= 35:
        status_text = "Several areas of your farm need care."
    else:
        status_text = "Your farm needs immediate attention."
    
    summary = f"{status_text}\n\nOverall Health: {overall_health}/100\n"
    
    if problem_zones:
        summary += f"\n⚠️ {len(problem_zones)} area(s) need attention:\n"
        for zone in problem_zones[:3]:  # Limit to top 3
            zone_id = zone.get("zone_id", "Unknown")
            health = zone.get("health_score", 0)
            issues = zone.get("issues", [])
            
            summary += f"\n• {zone_id} area (Health: {health}/100)"
            if issues:
                summary += f"\n  Issues: {', '.join(issues)}"
    else:
        summary += "\n✅ All areas of your farm are healthy!"
    
    return summary

