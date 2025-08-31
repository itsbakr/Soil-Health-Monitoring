# 🧪 LARMMS Farm Analysis Test Suite

Comprehensive unit tests for the LARMMS agricultural analysis platform using **real farm data** (no mocks).

## 🌱 Test Scenarios

### Good Soil Health Farms
1. **Black Gold Acres (Iowa)** - Expected: 90-100% soil health
   - Premium Mollisols soil
   - High organic matter (4.2%)
   - Optimal pH (6.5)
   - Conservation practices

2. **Golden Prairie Farm (Midwest)** - Expected: 85-95% soil health
   - Mollisols soil type
   - Good organic matter (3.8%)
   - Balanced pH (6.8)
   - No-till practices

### Poor Soil Health Farms
3. **Degraded Land (California)** - Expected: 20-40% soil health
   - Entisols soil type
   - Low organic matter (0.8%)
   - High pH (8.5)
   - Conventional tillage

4. **Severely Degraded Land (Texas)** - Expected: 10-30% soil health
   - Aridisols soil type
   - Very low organic matter (0.3%)
   - Very high pH (9.2)
   - Heavy tillage, monoculture

## 🧪 Test Coverage

### Individual Service Tests
- **Satellite Service**: Real satellite data collection
- **Weather Service**: Real weather data retrieval
- **Soil Health Agent**: AI-powered soil analysis
- **ROI Agent**: Economic analysis and crop recommendations
- **Crop Price Service**: Real market data

### Integration Tests
- **Full Pipeline**: Complete analysis workflow
- **ROI Analysis**: Economic analysis with different soil conditions
- **Data Integration**: Cross-service data flow

## 🚀 Running Tests

### Quick Test Run
```bash
cd backend
python run_tests.py
```

### Using pytest
```bash
cd backend
pytest tests/test_farm_analysis.py -v
```

### With Coverage
```bash
cd backend
pytest tests/test_farm_analysis.py --cov=services --cov-report=html
```

## 📊 Test Data

### Farm Parameters Tested
- **Coordinates**: Real GPS coordinates from different regions
- **Soil Types**: Mollisols, Alfisols, Entisols, Aridisols
- **Management Practices**: No-till, conventional tillage, conservation
- **Crop Rotations**: 3-year rotation, 2-year rotation, monoculture
- **Irrigation**: Rain-fed, center pivot, drip, flood
- **Organic Matter**: 0.3% to 4.2%
- **pH Levels**: 6.5 to 9.2

### Expected Outcomes
- **Excellent Soil**: ≥80% health score, "Excellent" status
- **Good Soil**: ≥60% health score, "Good" status  
- **Poor Soil**: <50% health score, "Poor" status
- **Critical Soil**: <30% health score, "Critical" status

## 🔍 Test Assertions

### Soil Health Tests
- Score ranges match expected soil conditions
- Health status classification is correct
- Confidence scores are reasonable (>60% for good data)
- Deficiencies and recommendations are identified

### ROI Analysis Tests
- Crop recommendations are generated
- ROI percentages are positive
- Confidence scores are reasonable
- Market data integration works

### Integration Tests
- All services work together
- Data flows correctly between services
- No data loss in pipeline
- Error handling works properly

## ⚠️ Important Notes

1. **Real Data**: These tests use real API calls to satellite, weather, and market services
2. **API Keys**: Ensure all required API keys are configured
3. **Internet**: Tests require internet connection for external services
4. **Time**: Tests may take 5-10 minutes due to real API calls
5. **Cost**: Some APIs may have usage costs

## 🐛 Troubleshooting

### Common Issues
- **API Key Errors**: Check environment variables
- **Network Errors**: Verify internet connection
- **Timeout Errors**: Some APIs may be slow, increase timeouts
- **Import Errors**: Ensure all dependencies are installed

### Debug Mode
```bash
cd backend
python -m pytest tests/test_farm_analysis.py -v -s --tb=long
```

## 📈 Performance Expectations

- **Satellite Data**: 10-30 seconds per location
- **Weather Data**: 2-5 seconds per location
- **Soil Analysis**: 20-60 seconds per farm
- **ROI Analysis**: 30-90 seconds per farm
- **Full Pipeline**: 2-5 minutes per farm

## 🎯 Success Criteria

All tests should pass with:
- ✅ Real data collection working
- ✅ AI analysis producing reasonable results
- ✅ Soil health scores matching expectations
- ✅ ROI analysis generating recommendations
- ✅ Integration between all services
- ✅ Error handling for edge cases 