"""
Admin Router for B2B Partner Dashboard

Provides endpoints for organizational administrators to:
- View aggregate farm statistics
- Monitor enrolled farms across their organization
- Generate impact reports
- Access bulk operations
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import logging

from routers.auth import get_current_user_id

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================
# Enums and Models
# ============================================

class FarmHealthStatus(str, Enum):
    HEALTHY = "healthy"
    MODERATE = "moderate"
    DEGRADED = "degraded"
    CRITICAL = "critical"


class OrganizationStats(BaseModel):
    total_farms: int = Field(..., description="Total number of enrolled farms")
    total_area_hectares: float = Field(..., description="Total area in hectares")
    average_health: float = Field(..., description="Average health score across all farms")
    healthy_farms: int = Field(..., description="Farms with health score >= 75")
    at_risk_farms: int = Field(..., description="Farms with health score 35-74")
    critical_farms: int = Field(..., description="Farms with health score < 35")
    recent_analyses: int = Field(..., description="Analyses completed in last 7 days")
    problem_zones_detected: int = Field(..., description="Total problem zones identified")
    improvement_rate: float = Field(..., description="Percentage of farms showing improvement")


class FarmSummary(BaseModel):
    id: str
    name: str
    owner_name: str
    owner_email: Optional[str]
    area_hectares: float
    crop_type: str
    health_score: float
    health_status: FarmHealthStatus
    problem_zones: int
    last_analysis: Optional[datetime]
    trend: str = Field(..., description="improving, stable, or declining")
    location_lat: float
    location_lng: float


class OrganizationOverview(BaseModel):
    organization_id: str
    organization_name: str
    stats: OrganizationStats
    health_distribution: Dict[str, int]
    regional_breakdown: List[Dict[str, Any]]
    recent_alerts: List[Dict[str, Any]]


# ============================================
# Demo Data Functions
# ============================================

def get_demo_stats() -> OrganizationStats:
    """Generate demo statistics for preview"""
    return OrganizationStats(
        total_farms=247,
        total_area_hectares=3842.5,
        average_health=68.3,
        healthy_farms=142,
        at_risk_farms=78,
        critical_farms=27,
        recent_analyses=156,
        problem_zones_detected=89,
        improvement_rate=23.5
    )


def get_demo_farms() -> List[FarmSummary]:
    """Generate demo farm list for preview"""
    return [
        FarmSummary(
            id="farm-001",
            name="Valley Farm",
            owner_name="John Martinez",
            owner_email="john@example.com",
            area_hectares=45.2,
            crop_type="Corn",
            health_score=82.0,
            health_status=FarmHealthStatus.HEALTHY,
            problem_zones=0,
            last_analysis=datetime.now() - timedelta(days=1),
            trend="improving",
            location_lat=40.7128,
            location_lng=-74.0060
        ),
        FarmSummary(
            id="farm-002",
            name="Sunrise Fields",
            owner_name="Maria Garcia",
            owner_email="maria@example.com",
            area_hectares=32.8,
            crop_type="Soybeans",
            health_score=65.0,
            health_status=FarmHealthStatus.MODERATE,
            problem_zones=2,
            last_analysis=datetime.now() - timedelta(days=2),
            trend="stable",
            location_lat=40.7589,
            location_lng=-73.9851
        ),
        FarmSummary(
            id="farm-003",
            name="Green Acres",
            owner_name="David Kim",
            owner_email="david@example.com",
            area_hectares=28.5,
            crop_type="Wheat",
            health_score=45.0,
            health_status=FarmHealthStatus.DEGRADED,
            problem_zones=5,
            last_analysis=datetime.now() - timedelta(days=2),
            trend="declining",
            location_lat=40.6892,
            location_lng=-74.0445
        ),
        FarmSummary(
            id="farm-004",
            name="River Bend",
            owner_name="James Wilson",
            owner_email="james@example.com",
            area_hectares=18.3,
            crop_type="Vegetables",
            health_score=32.0,
            health_status=FarmHealthStatus.CRITICAL,
            problem_zones=8,
            last_analysis=datetime.now() - timedelta(days=4),
            trend="declining",
            location_lat=40.7282,
            location_lng=-73.7949
        ),
    ]


# ============================================
# API Endpoints
# ============================================

@router.get("/overview", response_model=OrganizationOverview)
async def get_organization_overview(
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get comprehensive overview of organization's farm portfolio.
    
    Returns aggregate statistics, health distribution, and recent alerts.
    """
    # TODO: Replace with actual database queries based on user's organization
    
    stats = get_demo_stats()
    
    return OrganizationOverview(
        organization_id="org-demo",
        organization_name="Demo Agricultural Cooperative",
        stats=stats,
        health_distribution={
            "healthy": stats.healthy_farms,
            "moderate": 51,
            "degraded": stats.at_risk_farms - 51,
            "critical": stats.critical_farms
        },
        regional_breakdown=[
            {"region": "North District", "farms": 89, "avg_health": 72.5},
            {"region": "South District", "farms": 78, "avg_health": 65.2},
            {"region": "East District", "farms": 45, "avg_health": 68.8},
            {"region": "West District", "farms": 35, "avg_health": 62.1}
        ],
        recent_alerts=[
            {
                "type": "critical",
                "farm_id": "farm-004",
                "farm_name": "River Bend",
                "message": "Critical soil degradation detected in 8 zones",
                "timestamp": datetime.now() - timedelta(hours=2)
            },
            {
                "type": "warning",
                "farm_id": "farm-003",
                "farm_name": "Green Acres",
                "message": "Health score dropped 12 points since last analysis",
                "timestamp": datetime.now() - timedelta(hours=6)
            }
        ]
    )


@router.get("/farms", response_model=List[FarmSummary])
async def list_organization_farms(
    status_filter: Optional[FarmHealthStatus] = None,
    sort_by: str = "health_score",
    sort_order: str = "asc",
    limit: int = 50,
    offset: int = 0,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    List all farms in the organization with filtering and sorting.
    
    - **status_filter**: Filter by health status
    - **sort_by**: Field to sort by (health_score, area_hectares, name)
    - **sort_order**: asc or desc
    """
    farms = get_demo_farms()
    
    # Apply status filter
    if status_filter:
        farms = [f for f in farms if f.health_status == status_filter]
    
    # Sort
    reverse = sort_order == "desc"
    if sort_by == "health_score":
        farms.sort(key=lambda x: x.health_score, reverse=reverse)
    elif sort_by == "area_hectares":
        farms.sort(key=lambda x: x.area_hectares, reverse=reverse)
    elif sort_by == "name":
        farms.sort(key=lambda x: x.name, reverse=reverse)
    
    # Pagination
    return farms[offset:offset + limit]


@router.get("/farms/{farm_id}", response_model=FarmSummary)
async def get_farm_details(
    farm_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get detailed information about a specific farm.
    """
    farms = get_demo_farms()
    
    for farm in farms:
        if farm.id == farm_id:
            return farm
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Farm not found"
    )


@router.get("/stats", response_model=OrganizationStats)
async def get_organization_stats(
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get aggregate statistics for the organization.
    """
    return get_demo_stats()


@router.get("/trends")
async def get_health_trends(
    period: str = "30d",
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get health score trends over time.
    
    - **period**: Time period (7d, 30d, 90d, 1y)
    """
    # Demo trend data
    return {
        "period": period,
        "data_points": [
            {"date": "2024-01-01", "average_health": 65.2, "critical_farms": 32},
            {"date": "2024-01-08", "average_health": 66.1, "critical_farms": 30},
            {"date": "2024-01-15", "average_health": 67.5, "critical_farms": 28},
            {"date": "2024-01-22", "average_health": 68.3, "critical_farms": 27}
        ],
        "summary": {
            "health_change": "+3.1",
            "critical_change": "-5",
            "trend": "improving"
        }
    }


@router.get("/alerts")
async def get_active_alerts(
    severity: Optional[str] = None,
    limit: int = 20,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get active alerts for farms requiring attention.
    
    - **severity**: Filter by severity (critical, warning, info)
    """
    alerts = [
        {
            "id": "alert-001",
            "severity": "critical",
            "farm_id": "farm-004",
            "farm_name": "River Bend",
            "zone_id": "NE",
            "message": "Critical soil degradation detected - NDVI dropped below 0.2",
            "recommendation": "Immediate soil testing recommended",
            "created_at": datetime.now() - timedelta(hours=2)
        },
        {
            "id": "alert-002",
            "severity": "warning",
            "farm_id": "farm-003",
            "farm_name": "Green Acres",
            "zone_id": "SW",
            "message": "Low moisture levels detected in southwest zone",
            "recommendation": "Consider irrigation adjustment",
            "created_at": datetime.now() - timedelta(hours=6)
        },
        {
            "id": "alert-003",
            "severity": "info",
            "farm_id": "farm-002",
            "farm_name": "Sunrise Fields",
            "zone_id": None,
            "message": "New analysis available",
            "recommendation": "Review latest soil health report",
            "created_at": datetime.now() - timedelta(hours=12)
        }
    ]
    
    if severity:
        alerts = [a for a in alerts if a["severity"] == severity]
    
    return alerts[:limit]


@router.post("/export/report")
async def generate_impact_report(
    format: str = "pdf",
    include_farms: bool = True,
    include_recommendations: bool = True,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Generate an impact report for the organization.
    
    - **format**: Export format (pdf, csv, xlsx)
    - **include_farms**: Include detailed farm data
    - **include_recommendations**: Include AI recommendations
    """
    # TODO: Implement actual report generation
    
    return {
        "status": "generating",
        "report_id": "report-" + datetime.now().strftime("%Y%m%d%H%M%S"),
        "estimated_completion": datetime.now() + timedelta(minutes=2),
        "download_url": None,  # Will be populated when ready
        "message": "Report generation started. You will be notified when ready."
    }


@router.get("/bulk/analyze")
async def bulk_analyze_farms(
    farm_ids: Optional[str] = None,
    status_filter: Optional[FarmHealthStatus] = None,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Trigger bulk analysis for multiple farms.
    
    - **farm_ids**: Comma-separated farm IDs (analyzes all if not provided)
    - **status_filter**: Only analyze farms with this status
    """
    # Parse farm IDs
    target_farms = []
    if farm_ids:
        target_farms = farm_ids.split(",")
    
    return {
        "status": "queued",
        "farms_queued": len(target_farms) if target_farms else "all",
        "estimated_completion": datetime.now() + timedelta(minutes=15),
        "message": "Bulk analysis has been queued. Results will be available in the dashboard."
    }

