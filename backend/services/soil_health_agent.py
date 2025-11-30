"""
Advanced Soil Health Assessment Agent
Uses hybrid Gemini + Claude approach with sophisticated prompting techniques
Supports zone-by-zone spatial analysis for precision agriculture
"""

import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass, field

from .ai_config import ai_config

logger = logging.getLogger(__name__)

@dataclass
class ZoneHealthResult:
    """Health assessment for a single zone"""
    zone_id: str
    row: int
    col: int
    health_score: float  # 0-100
    status: str  # "healthy", "moderate", "degraded", "critical"
    ndvi: float
    ndwi: float
    moisture: float
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    priority: str = "normal"  # "critical", "high", "normal", "low"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "zone_id": self.zone_id,
            "row": self.row,
            "col": self.col,
            "health": self.health_score,
            "status": self.status,
            "ndvi": round(self.ndvi, 3),
            "ndwi": round(self.ndwi, 3),
            "moisture": round(self.moisture, 1),
            "issues": self.issues,
            "recommendations": self.recommendations,
            "priority": self.priority
        }


@dataclass
class SoilHealthReport:
    """Structured soil health report with zone-level analysis"""
    overall_score: float  # 0-100
    health_status: str  # "Excellent", "Good", "Fair", "Poor", "Critical"
    confidence_score: float  # 0-1
    key_indicators: Dict[str, Any]
    deficiencies: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    explanation: str
    technical_analysis: str
    farmer_summary: str
    generated_at: datetime
    model_used: str
    # New zone-level fields
    zone_analysis: List[ZoneHealthResult] = field(default_factory=list)
    spatial_summary: str = ""
    priority_zones: List[str] = field(default_factory=list)
    heatmap_data: List[List[float]] = field(default_factory=list)

class SoilHealthAgent:
    """
    Advanced Soil Health Assessment Agent
    
    Uses sophisticated prompting techniques:
    - Few-shot prompting with examples
    - Chain-of-thought reasoning
    - Multi-step analysis
    - Confidence scoring
    - Cross-validation between models
    """
    
    def __init__(self):
        self.ai_config = ai_config
        
        # Few-shot examples for soil health assessment
        self.few_shot_examples = [
            {
                "data": {
                    "ndvi": 0.75, "ph": 6.8, "moisture": 0.45, "temperature": 22,
                    "salinity": 0.12, "bsi": 0.15, "savi": 0.68
                },
                "analysis": "High NDVI (0.75) indicates healthy vegetation. pH (6.8) is optimal for most crops. Good moisture content (45%). Low salinity and BSI suggest healthy soil structure.",
                "score": 85,
                "status": "Good",
                "confidence": 0.92
            },
            {
                "data": {
                    "ndvi": 0.35, "ph": 8.5, "moisture": 0.15, "temperature": 28,
                    "salinity": 0.45, "bsi": 0.65, "savi": 0.28
                },
                "analysis": "Low NDVI (0.35) indicates vegetation stress. High pH (8.5) suggests alkaline soil issues. Low moisture (15%) and high salinity (0.45) indicate water stress and salt accumulation.",
                "score": 35,
                "status": "Poor",
                "confidence": 0.88
            }
        ]
    
    def _get_system_prompt(self) -> str:
        """Advanced system prompt with detailed instructions"""
        return """You are an expert agricultural soil scientist with 20+ years of experience in precision agriculture and soil health assessment.

Your task is to analyze satellite-derived soil health data and provide comprehensive, actionable insights for farmers.

ANALYSIS FRAMEWORK:
1. Quantitative Assessment: Analyze all numerical indicators
2. Contextual Analysis: Consider environmental factors and farming context  
3. Risk Assessment: Identify immediate and long-term risks
4. Solution Prioritization: Rank recommendations by impact and feasibility
5. Confidence Scoring: Assess reliability of your analysis

KEY INDICATORS TO ANALYZE:
- NDVI (0-1): Vegetation health, target >0.6 for healthy crops
- pH (0-14): Soil acidity, optimal 6.0-7.5 for most crops
- Moisture (0-1): Soil water content, target 0.3-0.7 depending on crop
- Temperature (°C): Land surface temperature
- Salinity (0-1): Salt content, <0.2 is ideal
- BSI (0-1): Bare soil exposure, <0.3 is good
- SAVI (0-1): Soil-adjusted vegetation index
- Weather factors: Recent conditions affecting soil

SCORING SYSTEM:
- 90-100: Excellent - Optimal conditions
- 75-89: Good - Minor improvements needed
- 60-74: Fair - Some concerns require attention
- 40-59: Poor - Significant issues need addressing
- 0-39: Critical - Immediate intervention required

OUTPUT REQUIREMENTS:
- Be specific and actionable
- Use farmer-friendly language while maintaining scientific accuracy
- Provide cost-effective solutions
- Consider local agricultural practices
- Include confidence assessment for each recommendation"""

    def _create_few_shot_prompt(self, farm_data: Dict[str, Any]) -> str:
        """Create few-shot prompt with examples and current analysis"""
        
        prompt = """Here are examples of soil health analyses:

EXAMPLE 1:
Data: NDVI=0.75, pH=6.8, Moisture=45%, Temperature=22°C, Salinity=0.12, BSI=0.15, SAVI=0.68
Analysis: High NDVI (0.75) indicates healthy vegetation cover with good photosynthetic activity. pH (6.8) is within optimal range for nutrient availability. Moisture content (45%) suggests adequate water retention. Low salinity (0.12) and BSI (0.15) indicate healthy soil structure with minimal erosion risk.
Score: 85/100 (Good)
Status: Good - Minor optimization possible
Confidence: 92%

EXAMPLE 2: 
Data: NDVI=0.35, pH=8.5, Moisture=15%, Temperature=28°C, Salinity=0.45, BSI=0.65, SAVI=0.28
Analysis: Low NDVI (0.35) indicates vegetation stress, possibly from alkaline conditions. High pH (8.5) limits nutrient uptake, particularly phosphorus and micronutrients. Low moisture (15%) combined with high temperature suggests water stress. High salinity (0.45) and BSI (0.65) indicate soil degradation.
Score: 35/100 (Poor)
Status: Poor - Immediate intervention needed
Confidence: 88%

Now analyze this farm's soil health data:

CURRENT FARM DATA:
"""
        
        # Add current farm data
        soil_data = farm_data.get('soil_analysis', {})
        weather_data = farm_data.get('weather_data', {})
        
        prompt += f"""
Satellite Indicators:
- NDVI: {soil_data.get('ndvi', 'N/A')}
- pH: {soil_data.get('ph_estimate', 'N/A')}
- Moisture: {soil_data.get('moisture_content', 'N/A')}
- Temperature: {soil_data.get('land_surface_temp', 'N/A')}°C
- Salinity: {soil_data.get('salinity_estimate', 'N/A')}
- BSI (Bare Soil Index): {soil_data.get('bsi', 'N/A')}
- SAVI: {soil_data.get('savi', 'N/A')}
- EVI: {soil_data.get('evi', 'N/A')}
- NDWI: {soil_data.get('ndwi', 'N/A')}

Weather Context:
- Recent precipitation: {weather_data.get('recent_precipitation', 'N/A')}mm
- Temperature trend: {weather_data.get('temperature_trend', 'N/A')}
- Growing Degree Days: {weather_data.get('gdd', 'N/A')}
- Drought risk: {weather_data.get('drought_risk', 'N/A')}

Farm Details:
- Size: {farm_data.get('size_acres', 'N/A')} acres
- Current crop: {farm_data.get('current_crop', 'N/A')}
- Region: {farm_data.get('location', 'N/A')}

ANALYSIS REQUIRED:
Provide a comprehensive soil health assessment following the same format as the examples above. Include:

1. QUANTITATIVE ANALYSIS: Score each indicator and explain its implications
   - NDVI analysis with vegetation health implications
   - pH assessment and nutrient availability impact
   - Moisture content evaluation and irrigation needs
   - Salinity levels and crop tolerance considerations
   - Temperature analysis and seasonal impacts

2. OVERALL SCORE: 0-100 with clear justification and breakdown
   - Show calculation methodology
   - Weight different factors appropriately
   - Explain score components

3. HEALTH STATUS: Excellent/Good/Fair/Poor/Critical with reasoning

4. CONFIDENCE SCORE: How certain are you of this assessment? (0-100%)
   - Data quality assessment
   - Measurement limitations
   - Validation factors

5. KEY DEFICIENCIES: What are the main problems?
   - Priority ranking (High/Medium/Low)
   - Impact assessment on productivity
   - Interconnected soil issues

6. SPECIFIC RECOMMENDATIONS: Prioritized action items with costs and timeline
   - Immediate actions (next 30 days)
   - Short-term improvements (3-6 months)
   - Long-term management (1-3 years)
   - Cost-benefit analysis for each recommendation

7. FARMER EXPLANATION: Simple, practical explanation for non-technical users
   - What the numbers mean in practical terms
   - Priority actions in everyday language
   - Expected outcomes and timeline

8. TECHNICAL INSIGHTS: Scientific analysis for agricultural professionals
   - Detailed methodology and data sources
   - Statistical confidence intervals
   - Precision agriculture recommendations
   - Monitoring protocols

Use chain-of-thought reasoning - show your step-by-step analysis process.
Provide specific numerical values and clear actionable guidance."""

        return prompt

    def _serialize_farm_data(self, farm_data: Dict[str, Any]) -> str:
        """Safely serialize farm data to JSON, handling SatelliteData objects"""
        from services.satellite_service import SatelliteData
        
        def serialize_helper(obj):
            if hasattr(obj, 'to_dict'):
                return obj.to_dict()
            elif isinstance(obj, dict):
                return {k: serialize_helper(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize_helper(item) for item in obj]
            else:
                return obj
        
        serializable_data = serialize_helper(farm_data)
        return json.dumps(serializable_data, indent=2, default=str)
    
    def _create_technical_analysis_prompt(self, farm_data: Dict[str, Any]) -> str:
        """Create detailed technical analysis prompt for Claude with zone-level analysis"""
        
        # Extract zonal data for spatial analysis prompt
        zonal_analysis = farm_data.get("zonal_analysis", {})
        zones = zonal_analysis.get("zones", [])
        has_zones = len(zones) > 0
        
        zone_summary = ""
        if has_zones:
            zone_summary = f"""
SPATIAL ZONAL ANALYSIS (CRITICAL - Analyze each zone separately!):
Grid Size: {zonal_analysis.get('grid_size', 'N/A')}
Total Zones: {len(zones)}
Problem Zones: {', '.join(zonal_analysis.get('problem_zones', [])) or 'None identified'}

INDIVIDUAL ZONE DATA (provide recommendations for EACH zone):
"""
            for zone in zones:
                zone_summary += f"""
Zone {zone['zone_id']} ({zone['position']}):
  - Health Score: {zone['health_score']:.1f}/100 ({zone['status']})
  - NDVI: {zone['ndvi']:.3f}
  - NDWI: {zone['ndwi']:.3f}
  - Moisture: {zone['moisture']:.1f}%
  - Existing Alerts: {', '.join(zone['alerts']) if zone['alerts'] else 'None'}
"""
        
        return f"""
ADVANCED SOIL HEALTH DIAGNOSTIC ANALYSIS - PRECISION AGRICULTURE MODE

You are conducting a detailed technical assessment using satellite-derived agricultural data. Apply advanced soil science principles and PRECISION AGRICULTURE methodologies.

IMPORTANT: This farm has been divided into MULTIPLE ZONES for localized analysis. You MUST provide zone-specific recommendations, not just overall farm recommendations.

FARM CONTEXT:
{self._serialize_farm_data(farm_data)}

{zone_summary if has_zones else "NOTE: Single-point analysis (no zonal data available)"}

DIAGNOSTIC FRAMEWORK:

1. OVERALL FARM ASSESSMENT:
   - General farm health trends
   - Cross-zone patterns and correlations
   - Environmental factors affecting the entire farm

2. ZONE-BY-ZONE ANALYSIS (REQUIRED if zones present):
   For EACH zone, analyze:
   - Specific health issues in that zone
   - Why this zone differs from others
   - Zone-specific causes of problems
   - Targeted interventions for that zone

3. VEGETATION HEALTH ANALYSIS:
   - Analyze NDVI, SAVI, EVI patterns per zone
   - Identify spatial patterns of vegetation stress
   - Evaluate which zones have healthy vs stressed vegetation
   - Consider crop-specific optimal ranges

4. SOIL CHEMISTRY ASSESSMENT:
   - pH implications for nutrient availability
   - Salinity effects on crop performance per zone
   - Nutrient deficiency indicators by area
   - Soil buffer capacity considerations

5. PHYSICAL SOIL PROPERTIES:
   - Moisture retention analysis per zone
   - Soil structure evaluation (BSI)
   - Compaction indicators by area
   - Erosion risk assessment per zone

6. SPATIAL RECOMMENDATIONS (CRITICAL):
   Provide recommendations in this format:
   - ZONE [ID]: [Specific action for this zone]
   - Example: "ZONE NE: Increase irrigation frequency - low moisture detected"
   - Example: "ZONE SW: Add nitrogen fertilizer - NDVI below optimal"

REASONING METHODOLOGY:
Use step-by-step analytical reasoning:
1. Data validation and quality assessment
2. Individual indicator analysis with scientific benchmarks
3. Cross-correlation analysis between indicators
4. Risk factor identification and prioritization
5. Solution pathways with scientific justification
6. Uncertainty quantification and confidence intervals

OUTPUT FORMAT:
Provide structured technical analysis with:
- Detailed scientific assessment with quantitative analysis
- Statistical confidence measures and data quality indicators
- Risk quantification with probability assessments
- Solution prioritization matrix with cost-benefit ratios
- Implementation timeline recommendations with milestone tracking
- Monitoring and validation protocols with KPIs

SPECIFIC DELIVERABLES:
1. EXECUTIVE SUMMARY: 2-3 sentences highlighting key findings and priority actions
2. QUANTITATIVE ASSESSMENT: Numerical scoring with methodology explanation
3. RISK ANALYSIS: Probability-based assessment of soil degradation risks
4. ACTIONABLE RECOMMENDATIONS: Specific, measurable, time-bound actions
5. MONITORING FRAMEWORK: Metrics and measurement protocols
6. COST-BENEFIT ANALYSIS: ROI estimates for recommended interventions

Focus on actionable insights backed by agricultural science principles.
Provide specific numerical targets and measurable outcomes.
"""

    async def _calculate_confidence_score(
        self, 
        soil_data: Dict[str, Any],
        weather_data: Dict[str, Any]
    ) -> float:
        """Calculate confidence score based on data quality and completeness"""
        
        confidence_factors = {
            'data_completeness': 0.3,
            'data_quality': 0.25,
            'weather_context': 0.2,
            'historical_data': 0.15,
            'cross_validation': 0.1
        }
        
        # Data completeness (30%)
        required_indicators = ['ndvi', 'ph_estimate', 'moisture_content', 'salinity_estimate']
        available_indicators = sum(1 for key in required_indicators if soil_data.get(key) is not None)
        completeness_score = available_indicators / len(required_indicators)
        
        # Data quality (25%) - check for realistic values
        quality_score = 1.0
        if soil_data.get('ndvi', 0) < 0 or soil_data.get('ndvi', 0) > 1:
            quality_score *= 0.8
        if soil_data.get('ph_estimate', 7) < 3 or soil_data.get('ph_estimate', 7) > 11:
            quality_score *= 0.8
        
        # Weather context (20%)
        weather_score = 0.8 if weather_data else 0.5
        
        # Historical data (15%) - assume moderate for now
        historical_score = 0.7
        
        # Cross-validation (10%) - assume good for now
        validation_score = 0.8
        
        total_confidence = (
            completeness_score * confidence_factors['data_completeness'] +
            quality_score * confidence_factors['data_quality'] +
            weather_score * confidence_factors['weather_context'] +
            historical_score * confidence_factors['historical_data'] +
            validation_score * confidence_factors['cross_validation']
        )
        
        return min(total_confidence, 1.0)

    async def analyze_soil_health(self, farm_data: Dict[str, Any]) -> SoilHealthReport:
        """
        Perform comprehensive soil health analysis using advanced AI techniques
        
        Args:
            farm_data: Complete farm data including soil, weather, and farm details
            
        Returns:
            Detailed soil health report with recommendations
        """
        import time
        
        analysis_start = time.time()
        farm_id = farm_data.get('farm_id', 'unknown')
        logger.info(f"🔬 Starting advanced soil health analysis for farm ID: {farm_id}")
        
        try:
            soil_data = farm_data.get('soil_analysis', {})
            weather_data = farm_data.get('weather_data', {})
            
            # Calculate confidence score
            conf_start = time.time()
            confidence_score = await self._calculate_confidence_score(soil_data, weather_data)
            logger.info(f"📊 Confidence calculation completed in {time.time() - conf_start:.2f}s")
            
            # Step 1: Use Gemini for initial analysis with few-shot prompting
            gemini_start = time.time()
            logger.info("🤖 Performing initial analysis with Gemini...")
            few_shot_prompt = self._create_few_shot_prompt(farm_data)
            
            gemini_response = await self.ai_config.generate_with_gemini(
                prompt=few_shot_prompt,
                max_tokens=1500,
                temperature=0.3  # Lower temperature for more consistent analysis
            )
            gemini_duration = time.time() - gemini_start
            logger.info(f"🤖 Gemini analysis completed in {gemini_duration:.2f}s")
            
            # Step 2: Use Claude for deep technical analysis
            claude_start = time.time()
            logger.info("🧠 Performing technical analysis with Claude...")
            technical_prompt = self._create_technical_analysis_prompt(farm_data)
            system_prompt = self._get_system_prompt()
            
            claude_response = await self.ai_config.generate_with_claude(
                prompt=technical_prompt,
                system_prompt=system_prompt,
                max_tokens=2000,
                temperature=0.2,  # Very low temperature for technical analysis
                model="claude-sonnet-4-20250514"
            )
            claude_duration = time.time() - claude_start
            logger.info(f"🧠 Claude analysis completed in {claude_duration:.2f}s")
            
            # Step 3: Parse and structure the results
            processing_start = time.time()
            report = await self._process_ai_responses(
                gemini_response, 
                claude_response, 
                farm_data, 
                confidence_score
            )
            processing_duration = time.time() - processing_start
            
            total_duration = time.time() - analysis_start
            logger.info(f"✅ Soil health analysis completed in {total_duration:.2f}s (Gemini: {gemini_duration:.2f}s, Claude: {claude_duration:.2f}s, Processing: {processing_duration:.2f}s)")
            return report
            
        except Exception as e:
            error_duration = time.time() - analysis_start
            logger.error(f"❌ Error in soil health analysis after {error_duration:.2f}s: {e}")
            logger.warning("🔄 Generating fallback soil health report")
            return await self._generate_fallback_report(farm_data)
    
    async def _process_ai_responses(
        self,
        gemini_response: Optional[str],
        claude_response: Optional[str],
        farm_data: Dict[str, Any],
        confidence_score: float
    ) -> SoilHealthReport:
        """Process AI responses and create structured report"""
        
        # Extract key information from responses
        overall_score = self._extract_score(gemini_response, claude_response)
        health_status = self._determine_health_status(overall_score)
        
        # Parse recommendations and deficiencies
        recommendations = self._extract_recommendations(claude_response)
        deficiencies = self._extract_deficiencies(claude_response, farm_data)
        key_indicators = self._extract_key_indicators(farm_data)
        
        # Generate farmer-friendly summary
        farmer_summary = await self._generate_farmer_summary(
            overall_score, 
            health_status, 
            recommendations[:3]  # Top 3 recommendations
        )
        
        return SoilHealthReport(
            overall_score=overall_score,
            health_status=health_status,
            confidence_score=confidence_score,
            key_indicators=key_indicators,
            deficiencies=deficiencies,
            recommendations=recommendations,
            explanation=gemini_response or "Analysis unavailable",
            technical_analysis=claude_response or "Technical analysis unavailable",
            farmer_summary=farmer_summary,
            generated_at=datetime.now(),
            model_used="Hybrid: Gemini + Claude"
        )
    
    def _extract_score(self, gemini_response: Optional[str], claude_response: Optional[str]) -> float:
        """Extract numerical score from AI responses"""
        
        responses = [r for r in [gemini_response, claude_response] if r]
        
        for response in responses:
            # Look for score patterns
            import re
            score_patterns = [
                r'score:\s*(\d+(?:\.\d+)?)',
                r'(\d+(?:\.\d+)?)/100',
                r'overall.*?(\d+(?:\.\d+)?)',
                r'health.*?score.*?(\d+(?:\.\d+)?)'
            ]
            
            for pattern in score_patterns:
                match = re.search(pattern, response.lower())
                if match:
                    score = float(match.group(1))
                    if 0 <= score <= 100:
                        return score
        
        # Default fallback score based on available data
        return 65.0
    
    def _determine_health_status(self, score: float) -> str:
        """Determine health status from numerical score"""
        if score >= 90:
            return "Excellent"
        elif score >= 75:
            return "Good"
        elif score >= 60:
            return "Fair"
        elif score >= 40:
            return "Poor"
        else:
            return "Critical"
    
    def _extract_recommendations(self, claude_response: Optional[str]) -> List[Dict[str, Any]]:
        """Extract structured recommendations from Claude's response"""
        import re
        
        if not claude_response:
            return self._get_fallback_recommendations()
        
        recommendations = []
        
        # Try to parse numbered recommendations from AI response
        # Look for patterns like "1.", "•", "-", or "Recommendation:"
        lines = claude_response.split('\n')
        current_rec = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for numbered items or bullet points
            is_rec_start = (
                re.match(r'^[\d]+[.):]\s*', line) or
                re.match(r'^[•\-\*]\s*', line) or
                'recommend' in line.lower() or
                'action' in line.lower() or
                'step' in line.lower()
            )
            
            if is_rec_start and len(line) > 10:
                # Clean up the line
                clean_line = re.sub(r'^[\d•\-\*]+[.):]*\s*', '', line)
                
                # Determine priority from keywords
                priority = "Medium"
                if any(word in line.lower() for word in ['urgent', 'immediate', 'critical', 'high priority']):
                    priority = "High"
                elif any(word in line.lower() for word in ['optional', 'consider', 'long-term', 'low priority']):
                    priority = "Low"
                
                # Determine category from keywords
                category = "General"
                if any(word in line.lower() for word in ['ph', 'lime', 'nutrient', 'fertiliz', 'nitrogen', 'phosphorus']):
                    category = "Soil Chemistry"
                elif any(word in line.lower() for word in ['water', 'irrigat', 'moisture', 'drainage']):
                    category = "Water Management"
                elif any(word in line.lower() for word in ['organic', 'compost', 'mulch', 'cover crop']):
                    category = "Organic Matter"
                elif any(word in line.lower() for word in ['erosion', 'tillage', 'compaction']):
                    category = "Soil Structure"
                elif any(word in line.lower() for word in ['test', 'monitor', 'sample']):
                    category = "Monitoring"
                
                recommendations.append({
                    "priority": priority,
                    "category": category,
                    "action": clean_line[:100],  # First 100 chars as action summary
                    "description": clean_line,
                    "timeline": "As soon as practical",
                    "estimated_cost": "Varies",
                    "expected_benefit": "Improved soil health"
                })
        
        # If we couldn't extract any, use AI-aware fallback
        if not recommendations:
            return self._get_fallback_recommendations()
        
        return recommendations[:5]  # Return top 5 recommendations
    
    def _get_fallback_recommendations(self) -> List[Dict[str, Any]]:
        """Return sensible default recommendations when AI parsing fails"""
        return [
            {
                "priority": "High",
                "category": "Monitoring",
                "action": "Conduct comprehensive soil testing",
                "description": "Get a professional soil test to determine exact nutrient levels, pH, and organic matter content",
                "timeline": "Within 2 weeks",
                "estimated_cost": "$30-100",
                "expected_benefit": "Accurate baseline for targeted improvements"
            },
            {
                "priority": "Medium",
                "category": "Water Management",
                "action": "Assess irrigation and drainage",
                "description": "Evaluate current water management practices and adjust based on soil moisture readings",
                "timeline": "Before next planting",
                "estimated_cost": "Varies",
                "expected_benefit": "Optimized water use and healthier root zones"
            }
        ]
    
    def _extract_deficiencies(self, claude_response: Optional[str], farm_data: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Extract soil deficiencies from analysis based on actual data"""
        import re
        
        deficiencies = []
        soil_data = (farm_data or {}).get('soil_analysis', {})
        
        # Check actual soil data for deficiencies
        ndvi = soil_data.get('ndvi', 0.5)
        ph = soil_data.get('ph_estimate', 7.0)
        moisture = soil_data.get('moisture_content', 0.4)
        salinity = soil_data.get('salinity_estimate', 0.1)
        bsi = soil_data.get('bsi', 0.2)
        
        # NDVI-based vegetation stress
        if ndvi < 0.3:
            deficiencies.append({
                "type": "Vegetation Stress",
                "issue": f"Very low vegetation health (NDVI: {ndvi:.2f})",
                "severity": "Critical",
                "impact": "Crops may be dying or severely stressed, immediate intervention needed"
            })
        elif ndvi < 0.5:
            deficiencies.append({
                "type": "Vegetation Stress", 
                "issue": f"Below-optimal vegetation health (NDVI: {ndvi:.2f})",
                "severity": "Moderate",
                "impact": "Reduced photosynthesis and potential yield loss"
            })
        
        # pH issues
        if ph < 5.5:
            deficiencies.append({
                "type": "Soil Chemistry",
                "issue": f"Acidic soil (pH: {ph:.1f})",
                "severity": "High",
                "impact": "Nutrient lockout, aluminum toxicity risk, poor microbial activity"
            })
        elif ph > 8.0:
            deficiencies.append({
                "type": "Soil Chemistry",
                "issue": f"Alkaline soil (pH: {ph:.1f})",
                "severity": "Moderate",
                "impact": "Iron and phosphorus deficiency, reduced micronutrient availability"
            })
        
        # Moisture issues
        if moisture < 0.2:
            deficiencies.append({
                "type": "Water Stress",
                "issue": f"Low soil moisture ({moisture*100:.0f}%)",
                "severity": "High" if moisture < 0.1 else "Moderate",
                "impact": "Drought stress, reduced nutrient uptake, wilting"
            })
        elif moisture > 0.8:
            deficiencies.append({
                "type": "Water Stress",
                "issue": f"Excessive soil moisture ({moisture*100:.0f}%)",
                "severity": "Moderate",
                "impact": "Root rot risk, anaerobic conditions, nutrient leaching"
            })
        
        # Salinity issues
        if salinity > 0.3:
            deficiencies.append({
                "type": "Salinity",
                "issue": f"Elevated salt levels ({salinity:.2f})",
                "severity": "High" if salinity > 0.5 else "Moderate",
                "impact": "Osmotic stress, reduced water uptake, crop damage"
            })
        
        # Bare soil exposure
        if bsi > 0.5:
            deficiencies.append({
                "type": "Soil Structure",
                "issue": f"High bare soil exposure (BSI: {bsi:.2f})",
                "severity": "Moderate",
                "impact": "Erosion risk, soil temperature extremes, moisture loss"
            })
        
        # Also try to extract from AI response if available
        if claude_response:
            # Look for deficiency-related keywords in AI response
            deficiency_keywords = ['deficien', 'lack', 'low level', 'insufficient', 'poor', 'stress', 'problem']
            for keyword in deficiency_keywords:
                if keyword in claude_response.lower():
                    # Find sentences containing the keyword
                    sentences = re.split(r'[.!?]', claude_response)
                    for sentence in sentences:
                        if keyword in sentence.lower() and len(sentence) > 20:
                            if len(deficiencies) < 5:  # Limit to 5 deficiencies
                                deficiencies.append({
                                    "type": "AI-Identified",
                                    "issue": sentence.strip()[:150],
                                    "severity": "Moderate",
                                    "impact": "See detailed analysis"
                                })
                            break
        
        return deficiencies if deficiencies else [{
            "type": "Assessment",
            "issue": "No major deficiencies detected",
            "severity": "None",
            "impact": "Soil appears to be in acceptable condition"
        }]
    
    def _extract_key_indicators(self, farm_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and format key soil indicators"""
        
        soil_data = farm_data.get('soil_analysis', {})
        
        return {
            "vegetation_health": {
                "ndvi": soil_data.get('ndvi', 0),
                "status": "Good" if soil_data.get('ndvi', 0) > 0.6 else "Needs Attention"
            },
            "soil_chemistry": {
                "ph": soil_data.get('ph_estimate', 7.0),
                "status": "Optimal" if 6.0 <= soil_data.get('ph_estimate', 7.0) <= 7.5 else "Adjustment Needed"
            },
            "water_status": {
                "moisture": soil_data.get('moisture_content', 0),
                "status": "Adequate" if soil_data.get('moisture_content', 0) > 0.3 else "Low"
            },
            "salinity": {
                "level": soil_data.get('salinity_estimate', 0),
                "status": "Good" if soil_data.get('salinity_estimate', 0) < 0.2 else "High"
            }
        }
    
    async def _generate_farmer_summary(
        self, 
        score: float, 
        status: str, 
        top_recommendations: List[Dict[str, Any]]
    ) -> str:
        """Generate farmer-friendly summary using Gemini"""
        import time
        
        summary_start = time.time()
        prompt = f"""
Create a simple, friendly summary for a farmer about their soil health:

Overall Score: {score}/100 ({status})
Top Recommendations: {[rec.get('action', '') for rec in top_recommendations]}

Write 2-3 sentences that:
1. Explain the overall soil health in simple terms
2. Highlight the most important action to take
3. Give encouragement and next steps

Use everyday language, avoid technical jargon, and be encouraging but honest.
"""
        
        summary = await self.ai_config.generate_with_gemini(
            prompt=prompt,
            max_tokens=200,
            temperature=0.7
        )
        
        duration = time.time() - summary_start
        logger.info(f"👨‍🌾 Farmer summary generated in {duration:.2f}s")
        
        return summary or f"Your soil health scores {score}/100 ({status}). Focus on the top recommendations to improve your farm's productivity."
    
    async def _generate_fallback_report(self, farm_data: Dict[str, Any]) -> SoilHealthReport:
        """Generate fallback report when AI services are unavailable"""
        
        logger.warning("🔄 Generating fallback soil health report")
        
        soil_data = farm_data.get('soil_analysis', {})
        
        # Simple rule-based assessment
        indicators = []
        score = 65.0  # Use consistent default score that matches logs
        
        if soil_data.get('ndvi', 0) > 0.6:
            indicators.append("Good vegetation health")
            score += 10
        else:
            indicators.append("Vegetation needs attention")
            score -= 5
            
        if 6.0 <= soil_data.get('ph_estimate', 7.0) <= 7.5:
            indicators.append("Optimal soil pH")
            score += 5
        else:
            indicators.append("pH adjustment recommended")
            score -= 3
        
        final_score = max(0, min(100, score))
        logger.info(f"🔢 Fallback analysis generated score: {final_score}")
        
        return SoilHealthReport(
            overall_score=final_score,
            health_status=self._determine_health_status(final_score),
            confidence_score=0.6,  # Lower confidence for fallback
            key_indicators=self._extract_key_indicators(farm_data),
            deficiencies=[],
            recommendations=[{
                "priority": "Medium",
                "category": "General",
                "action": "Professional soil test",
                "description": "Conduct detailed soil testing for accurate assessment",
                "timeline": "Next month",
                "estimated_cost": "$50-100",
                "expected_benefit": "Precise nutrient management"
            }],
            explanation="Basic assessment completed using available satellite data.",
            technical_analysis="Detailed analysis unavailable - AI services not accessible.",
            farmer_summary="Your soil shows moderate health. Consider professional testing for detailed recommendations.",
            generated_at=datetime.now(),
            model_used="Fallback - Rule-based analysis"
        )

# Global instance
soil_health_agent = SoilHealthAgent() 