from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

from routers.auth import get_current_user_id

router = APIRouter()

# Enums
class CropType(str, Enum):
    RICE = "rice"
    CORN = "corn"
    WHEAT = "wheat"
    SOYBEANS = "soybeans"
    VEGETABLES = "vegetables"
    OTHER = "other"

class FarmUnit(str, Enum):
    ACRES = "acres"
    HECTARES = "hectares"

# Pydantic models
class FarmLocation(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Farm latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Farm longitude")

class FarmCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Farm name")
    location: FarmLocation
    size: float = Field(..., gt=0, description="Farm size")
    unit: FarmUnit = Field(..., description="Size unit (acres or hectares)")
    current_crop: CropType
    previous_crop_1: Optional[CropType] = None
    previous_crop_2: Optional[CropType] = None
    planned_harvest_date: datetime
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")

class FarmUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    size: Optional[float] = Field(None, gt=0)
    unit: Optional[FarmUnit] = None
    current_crop: Optional[CropType] = None
    previous_crop_1: Optional[CropType] = None
    previous_crop_2: Optional[CropType] = None
    planned_harvest_date: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=500)

class FarmResponse(BaseModel):
    id: str
    name: str
    location: FarmLocation
    size: float
    unit: FarmUnit
    current_crop: CropType
    previous_crop_1: Optional[CropType]
    previous_crop_2: Optional[CropType]
    planned_harvest_date: datetime
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_analysis_date: Optional[datetime]
    soil_health_status: Optional[str]  # excellent, good, fair, poor

@router.post("/", response_model=FarmResponse, status_code=status.HTTP_201_CREATED)
async def create_farm(
    farm_data: FarmCreate,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Create a new farm for the authenticated user
    
    - **name**: Farm name
    - **location**: Latitude and longitude coordinates
    - **size**: Farm size in acres or hectares
    - **current_crop**: Currently planted crop
    - **previous_crop_1**: Most recent previous crop
    - **previous_crop_2**: Second most recent previous crop
    - **planned_harvest_date**: Expected harvest date
    """
    # TODO: Implement farm creation in Supabase
    # For now, return a placeholder response
    return {
        "id": "farm-placeholder-id",
        "name": farm_data.name,
        "location": farm_data.location,
        "size": farm_data.size,
        "unit": farm_data.unit,
        "current_crop": farm_data.current_crop,
        "previous_crop_1": farm_data.previous_crop_1,
        "previous_crop_2": farm_data.previous_crop_2,
        "planned_harvest_date": farm_data.planned_harvest_date,
        "notes": farm_data.notes,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "last_analysis_date": None,
        "soil_health_status": None
    }

@router.get("/", response_model=List[FarmResponse])
async def get_user_farms(current_user_id: str = Depends(get_current_user_id)):
    """
    Get all farms for the authenticated user
    """
    # TODO: Implement farm retrieval from Supabase
    # For now, return placeholder data
    return [
        {
            "id": "farm-1",
            "name": "North Field",
            "location": {"latitude": 40.7128, "longitude": -74.0060},
            "size": 50.0,
            "unit": "acres",
            "current_crop": "corn",
            "previous_crop_1": "soybeans",
            "previous_crop_2": "wheat",
            "planned_harvest_date": datetime(2024, 9, 15),
            "notes": "Main production field",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_analysis_date": datetime(2024, 1, 15),
            "soil_health_status": "good"
        }
    ]

@router.get("/{farm_id}", response_model=FarmResponse)
async def get_farm(
    farm_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get a specific farm by ID
    """
    # TODO: Implement farm retrieval by ID from Supabase
    # TODO: Verify farm ownership
    return {
        "id": farm_id,
        "name": "North Field",
        "location": {"latitude": 40.7128, "longitude": -74.0060},
        "size": 50.0,
        "unit": "acres",
        "current_crop": "corn",
        "previous_crop_1": "soybeans",
        "previous_crop_2": "wheat",
        "planned_harvest_date": datetime(2024, 9, 15),
        "notes": "Main production field",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "last_analysis_date": datetime(2024, 1, 15),
        "soil_health_status": "good"
    }

@router.put("/{farm_id}", response_model=FarmResponse)
async def update_farm(
    farm_id: str,
    farm_data: FarmUpdate,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Update a specific farm
    """
    # TODO: Implement farm update in Supabase
    # TODO: Verify farm ownership
    return {
        "id": farm_id,
        "name": farm_data.name or "Updated Farm",
        "location": {"latitude": 40.7128, "longitude": -74.0060},
        "size": farm_data.size or 50.0,
        "unit": farm_data.unit or "acres",
        "current_crop": farm_data.current_crop or "corn",
        "previous_crop_1": farm_data.previous_crop_1,
        "previous_crop_2": farm_data.previous_crop_2,
        "planned_harvest_date": farm_data.planned_harvest_date or datetime(2024, 9, 15),
        "notes": farm_data.notes,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "last_analysis_date": datetime(2024, 1, 15),
        "soil_health_status": "good"
    }

@router.delete("/{farm_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_farm(
    farm_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Delete a specific farm
    """
    # TODO: Implement farm deletion in Supabase
    # TODO: Verify farm ownership
    # TODO: Consider soft delete to preserve historical data
    pass 