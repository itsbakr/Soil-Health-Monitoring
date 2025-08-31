#!/usr/bin/env python3
"""
Quick test to verify the satellite service works with FarmCoordinates
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.satellite_service import SatelliteService, FarmCoordinates

async def test_satellite_service():
    """Test satellite service with proper FarmCoordinates"""
    print("🧪 Quick Satellite Service Test")
    print("=" * 40)
    
    # Initialize satellite service
    satellite_service = SatelliteService()
    
    # Create farm coordinates for Iowa (good soil health location)
    farm_coords = FarmCoordinates(
        latitude=41.8781,
        longitude=-93.0977,
        area_hectares=300 * 0.404686  # 300 acres to hectares
    )
    
    print(f"📍 Testing location: {farm_coords.latitude:.4f}, {farm_coords.longitude:.4f}")
    print(f"🌾 Farm area: {farm_coords.area_hectares:.1f} hectares")
    
    try:
        # Test satellite data collection
        print("📡 Collecting satellite data...")
        satellite_data = satellite_service.get_farm_satellite_data(farm_coords)
        
        if satellite_data:
            print("✅ Satellite data collected successfully!")
            print(f"   📊 NDVI: {satellite_data.ndvi:.3f}")
            print(f"   🌡️ Surface Temperature: {satellite_data.surface_temperature:.1f}°C")
            print(f"   💧 Moisture Estimate: {satellite_data.moisture_estimate:.3f}")
            print(f"   ☁️ Cloud Coverage: {satellite_data.cloud_coverage:.1f}%")
            print(f"   📈 Data Quality Score: {satellite_data.data_quality_score:.1f}%")
            print(f"   📅 Date Captured: {satellite_data.date_captured}")
        else:
            print("❌ No satellite data returned")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_satellite_service()) 