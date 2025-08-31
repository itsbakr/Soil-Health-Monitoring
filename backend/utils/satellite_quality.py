from datetime import datetime
from typing import Dict, Any, List

def interpret_ndvi_status(ndvi: float, seasonal_context: Dict[str, Any]) -> str:
    """Interpret NDVI value in context of season and growing period"""
    growing = seasonal_context.get('is_growing_season', True)
    if not growing and ndvi < 0.2:
        return 'expected_low'  # Dormant season, low NDVI is normal
    if growing and ndvi < 0.2:
        return 'unexpected_low'  # Growing season, low NDVI is abnormal
    return 'normal'

def validate_data_quality(satellite_data) -> List[str]:
    """Check for data quality issues and return a list of warnings"""
    issues = []
    if satellite_data.pixel_count < 100:
        issues.append('Low pixel count')
    if satellite_data.valid_pixels / max(satellite_data.pixel_count, 1) < 0.5:
        issues.append('Low valid pixel ratio')
    if abs(satellite_data.ndvi) < 0.05 and getattr(satellite_data, 'ndvi_status', 'normal') == 'unexpected_low':
        issues.append('NDVI unexpectedly low during growing season')
    if satellite_data.data_quality_score < 60:
        issues.append('Overall data quality score is low')
    if satellite_data.cloud_coverage > 50:
        issues.append('High cloud coverage')
    return issues

def get_seasonal_context(capture_date: datetime, latitude: float) -> Dict[str, Any]:
    """Calculate seasonal and temporal context for agricultural analysis"""
    day_of_year = capture_date.timetuple().tm_yday
    is_northern = latitude >= 0
    if not is_northern:
        day_of_year = (day_of_year + 182) % 365
    if 60 <= day_of_year <= 150:
        season = 'spring'
        growing_season = 'planting'
    elif 151 <= day_of_year <= 243:
        season = 'summer'
        growing_season = 'growing'
    elif 244 <= day_of_year <= 334:
        season = 'fall'
        growing_season = 'harvest'
    else:
        season = 'winter'
        growing_season = 'dormant'
    optimal_planting_start = 75 if is_northern else 258
    optimal_harvest_start = 258 if is_northern else 75
    return {
        'season': season,
        'growing_season': growing_season,
        'day_of_year': day_of_year,
        'growing_day_of_year': day_of_year,
        'days_since_optimal_planting': abs(day_of_year - optimal_planting_start),
        'days_until_harvest': abs(optimal_harvest_start - day_of_year),
        'is_growing_season': growing_season in ['planting', 'growing'],
        'hemisphere': 'northern' if is_northern else 'southern'
    } 