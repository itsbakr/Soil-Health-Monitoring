#!/usr/bin/env python3
"""
Test Runner for Farm Analysis
Executes comprehensive tests using real farm data
"""

import asyncio
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tests.test_farm_analysis import TestFarmAnalysis


async def run_tests():
    """Run all farm analysis tests"""
    print("🧪 LARMMS Farm Analysis Test Suite")
    print("=" * 60)
    print(f"📅 Test Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🌱 Testing with Real Farm Data (No Mocks)")
    print("=" * 60)
    
    # Initialize test instance
    test_instance = TestFarmAnalysis()
    
    # Test results tracking
    test_results = []
    total_tests = 7
    passed_tests = 0
    
    try:
        # Test 1: Excellent Soil Health Farm
        print("\n1️⃣ Testing Excellent Soil Health Farm...")
        try:
            await test_instance.test_excellent_soil_health_farm(
                test_instance.soil_health_agent(),
                test_instance.satellite_service(),
                test_instance.weather_service()
            )
            print("✅ Test 1 PASSED")
            test_results.append(("Excellent Soil Health", "PASSED"))
            passed_tests += 1
        except Exception as e:
            print(f"❌ Test 1 FAILED: {str(e)}")
            test_results.append(("Excellent Soil Health", "FAILED", str(e)))
        
        # Test 2: Good Soil Health Farm
        print("\n2️⃣ Testing Good Soil Health Farm...")
        try:
            await test_instance.test_good_soil_health_farm(
                test_instance.soil_health_agent(),
                test_instance.satellite_service(),
                test_instance.weather_service()
            )
            print("✅ Test 2 PASSED")
            test_results.append(("Good Soil Health", "PASSED"))
            passed_tests += 1
        except Exception as e:
            print(f"❌ Test 2 FAILED: {str(e)}")
            test_results.append(("Good Soil Health", "FAILED", str(e)))
        
        # Test 3: Poor Soil Health Farm
        print("\n3️⃣ Testing Poor Soil Health Farm...")
        try:
            await test_instance.test_poor_soil_health_farm(
                test_instance.soil_health_agent(),
                test_instance.satellite_service(),
                test_instance.weather_service()
            )
            print("✅ Test 3 PASSED")
            test_results.append(("Poor Soil Health", "PASSED"))
            passed_tests += 1
        except Exception as e:
            print(f"❌ Test 3 FAILED: {str(e)}")
            test_results.append(("Poor Soil Health", "FAILED", str(e)))
        
        # Test 4: Critical Soil Health Farm
        print("\n4️⃣ Testing Critical Soil Health Farm...")
        try:
            await test_instance.test_critical_soil_health_farm(
                test_instance.soil_health_agent(),
                test_instance.satellite_service(),
                test_instance.weather_service()
            )
            print("✅ Test 4 PASSED")
            test_results.append(("Critical Soil Health", "PASSED"))
            passed_tests += 1
        except Exception as e:
            print(f"❌ Test 4 FAILED: {str(e)}")
            test_results.append(("Critical Soil Health", "FAILED", str(e)))
        
        # Test 5: ROI Analysis with Excellent Soil
        print("\n5️⃣ Testing ROI Analysis with Excellent Soil...")
        try:
            await test_instance.test_roi_analysis_excellent_soil(
                test_instance.roi_agent(),
                test_instance.soil_health_agent(),
                test_instance.crop_price_service()
            )
            print("✅ Test 5 PASSED")
            test_results.append(("ROI Analysis (Excellent Soil)", "PASSED"))
            passed_tests += 1
        except Exception as e:
            print(f"❌ Test 5 FAILED: {str(e)}")
            test_results.append(("ROI Analysis (Excellent Soil)", "FAILED", str(e)))
        
        # Test 6: ROI Analysis with Poor Soil
        print("\n6️⃣ Testing ROI Analysis with Poor Soil...")
        try:
            await test_instance.test_roi_analysis_poor_soil(
                test_instance.roi_agent(),
                test_instance.soil_health_agent(),
                test_instance.crop_price_service()
            )
            print("✅ Test 6 PASSED")
            test_results.append(("ROI Analysis (Poor Soil)", "PASSED"))
            passed_tests += 1
        except Exception as e:
            print(f"❌ Test 6 FAILED: {str(e)}")
            test_results.append(("ROI Analysis (Poor Soil)", "FAILED", str(e)))
        
        # Test 7: Full Analysis Pipeline
        print("\n7️⃣ Testing Full Analysis Pipeline...")
        try:
            await test_instance.test_full_analysis_pipeline(
                test_instance.soil_health_agent(),
                test_instance.roi_agent(),
                test_instance.satellite_service(),
                test_instance.weather_service(),
                test_instance.crop_price_service()
            )
            print("✅ Test 7 PASSED")
            test_results.append(("Full Analysis Pipeline", "PASSED"))
            passed_tests += 1
        except Exception as e:
            print(f"❌ Test 7 FAILED: {str(e)}")
            test_results.append(("Full Analysis Pipeline", "FAILED", str(e)))
        
    except Exception as e:
        print(f"❌ Test suite failed with error: {str(e)}")
        return False
    
    # Print test summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print()
    
    print("📋 DETAILED RESULTS:")
    print("-" * 60)
    for i, (test_name, status, *error) in enumerate(test_results, 1):
        if status == "PASSED":
            print(f"{i}. ✅ {test_name}: {status}")
        else:
            print(f"{i}. ❌ {test_name}: {status}")
            if error:
                print(f"   Error: {error[0]}")
    
    print("\n" + "=" * 60)
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Your farm analysis system is working perfectly!")
        return True
    else:
        print(f"⚠️  {total_tests - passed_tests} test(s) failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(run_tests())
    
    # Exit with appropriate code
    sys.exit(0 if success else 1) 