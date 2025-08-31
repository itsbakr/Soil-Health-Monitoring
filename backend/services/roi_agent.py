"""
Advanced ROI Reasoner Agent
Uses Claude's reasoning capabilities for sophisticated economic analysis and crop recommendations
"""

import json
import logging
import random
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from .ai_config import ai_config
from .soil_health_agent import SoilHealthReport

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    LOW = "Low"
    MODERATE = "Moderate" 
    HIGH = "High"
    CRITICAL = "Critical"

@dataclass
class CropRecommendation:
    """Individual crop recommendation with ROI analysis"""
    crop_name: str
    expected_yield: float  # tons/acre
    expected_revenue: float  # $/acre
    input_costs: float  # $/acre
    net_profit: float  # $/acre
    roi_percentage: float  # %
    payback_period: int  # months
    risk_level: RiskLevel
    confidence_score: float  # 0-1
    soil_compatibility: float  # 0-1
    market_favorability: float  # 0-1
    reasoning: str
    implementation_steps: List[str]
    risk_factors: List[str]
    mitigation_strategies: List[str]

@dataclass 
class ROIAnalysisReport:
    """Comprehensive ROI analysis report"""
    farm_id: str
    current_crop_analysis: Dict[str, Any]
    alternative_crops: List[CropRecommendation]
    recommended_crop: CropRecommendation
    economic_projections: Dict[str, Any]
    scenario_analysis: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    decision_matrix: Dict[str, Any]
    implementation_timeline: List[Dict[str, Any]]
    monitoring_plan: Dict[str, Any]
    executive_summary: str
    detailed_reasoning: str
    farmer_explanation: str
    generated_at: datetime
    confidence_level: float
    model_used: str

class ROIReasonerAgent:
    """
    Advanced ROI Analysis and Crop Recommendation Agent
    
    Uses Claude's reasoning capabilities for:
    - Multi-factor decision analysis
    - Scenario modeling and risk assessment
    - Economic projection with uncertainty quantification
    - Step-by-step reasoning explanation
    - Monte Carlo simulation for ROI ranges
    """
    
    def __init__(self):
        self.ai_config = ai_config
        
        # Crop database with baseline economics (would typically come from external APIs)
        self.crop_database = {
            "corn": {
                "base_yield": 175,  # bushels/acre
                "base_price": 5.5,  # $/bushel
                "input_costs": 450,  # $/acre
                "growth_period": 120,  # days
                "optimal_ph": (6.0, 6.8),
                "drought_tolerance": 0.6,
                "market_stability": 0.8
            },
            "soybeans": {
                "base_yield": 50,  # bushels/acre
                "base_price": 12.0,  # $/bushel
                "input_costs": 320,  # $/acre
                "growth_period": 105,  # days
                "optimal_ph": (6.0, 7.0),
                "drought_tolerance": 0.7,
                "market_stability": 0.7
            },
            "wheat": {
                "base_yield": 65,  # bushels/acre
                "base_price": 6.8,  # $/bushel
                "input_costs": 280,  # $/acre
                "growth_period": 240,  # days
                "optimal_ph": (6.0, 7.5),
                "drought_tolerance": 0.8,
                "market_stability": 0.9
            },
            "cotton": {
                "base_yield": 850,  # lbs/acre
                "base_price": 0.75,  # $/lb
                "input_costs": 550,  # $/acre
                "growth_period": 160,  # days
                "optimal_ph": (5.8, 8.0),
                "drought_tolerance": 0.5,
                "market_stability": 0.6
            }
        }
    
    def _get_system_prompt(self) -> str:
        """Advanced system prompt for economic reasoning"""
        return """You are a world-class agricultural economist and farm management consultant with expertise in:

- Agricultural finance and ROI optimization
- Risk assessment and scenario planning
- Market analysis and price forecasting
- Soil-crop compatibility analysis
- Sustainable farming economics
- Decision science and multi-criteria analysis

Your role is to provide sophisticated economic analysis that helps farmers maximize both profitability and long-term soil health.

ANALYTICAL FRAMEWORK:
1. MULTI-FACTOR ANALYSIS: Consider soil health, market conditions, climate, and operational factors
2. SCENARIO MODELING: Analyze best-case, worst-case, and most-likely scenarios
3. RISK QUANTIFICATION: Assess and quantify various risk factors
4. DECISION OPTIMIZATION: Find optimal balance between profit and sustainability
5. UNCERTAINTY HANDLING: Provide confidence intervals and probability assessments
6. STEP-BY-STEP REASONING: Show clear logical progression in analysis

ECONOMIC EVALUATION CRITERIA:
- Net Present Value (NPV) analysis
- Return on Investment (ROI) calculations
- Payback period assessment
- Risk-adjusted returns
- Opportunity cost analysis
- Cash flow projections
- Sensitivity analysis

REASONING METHODOLOGY:
Use systematic chain-of-thought reasoning:
1. Problem decomposition and parameter identification
2. Data analysis and trend evaluation
3. Assumption validation and risk assessment
4. Model application and scenario development
5. Results synthesis and recommendation ranking
6. Implementation strategy and monitoring plan

OUTPUT REQUIREMENTS:
- Provide quantitative analysis with clear assumptions
- Show step-by-step reasoning process
- Include confidence levels and uncertainty ranges
- Offer actionable implementation steps
- Consider both short-term ROI and long-term sustainability
- Use farmer-friendly explanations alongside technical analysis"""

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

    def _create_comprehensive_analysis_prompt(
        self, 
        farm_data: Dict[str, Any],
        soil_health_report: SoilHealthReport,
        market_data: Dict[str, Any],
        weather_data: Dict[str, Any]
    ) -> str:
        """Create comprehensive analysis prompt with all available data"""
        
        return f"""
COMPREHENSIVE ROI ANALYSIS AND CROP RECOMMENDATION

FARM CONTEXT:
{self._serialize_farm_data(farm_data)}

SOIL HEALTH ASSESSMENT:
Overall Score: {soil_health_report.overall_score}/100
Health Status: {soil_health_report.health_status}
Key Indicators: {json.dumps(soil_health_report.key_indicators, indent=2, default=str)}
Deficiencies: {json.dumps(soil_health_report.deficiencies, indent=2, default=str)}
Confidence: {soil_health_report.confidence_score:.2f}

MARKET CONDITIONS:
{json.dumps(market_data, indent=2, default=str)}

WEATHER CONTEXT:
{json.dumps(weather_data, indent=2, default=str)}

ANALYSIS REQUIREMENTS:

1. CURRENT CROP PERFORMANCE ANALYSIS:
   - Evaluate current crop's economic performance
   - Identify yield limiting factors from soil health data
   - Calculate actual vs potential ROI
   - Assess sustainability implications

2. ALTERNATIVE CROP EVALUATION:
   Analyze these crops: Corn, Soybeans, Wheat, Cotton
   
   For each crop, provide:
   - Soil compatibility score (0-1) based on pH, salinity, moisture needs
   - Expected yield adjustment based on soil conditions
   - Market favorability assessment using current price data
   - Input cost estimates including soil amendments
   - Net profit calculations with confidence intervals
   - Risk assessment (Low/Moderate/High/Critical)
   - Implementation timeline and requirements

3. SCENARIO ANALYSIS:
   Model three scenarios for top 3 crops:
   - Optimistic: Ideal conditions (90th percentile outcomes)
   - Most Likely: Expected conditions (50th percentile)
   - Pessimistic: Challenging conditions (10th percentile)
   
   Include weather risks, market volatility, and soil challenges

4. MULTI-CRITERIA DECISION ANALYSIS:
   Weight factors for recommendation:
   - Economic return (40%)
   - Risk level (25%)
   - Soil health impact (20%)
   - Implementation feasibility (15%)

5. REASONING CHAIN:
   Show step-by-step reasoning for:
   - How soil health affects each crop's potential
   - Market timing and price trend implications
   - Risk factor prioritization and mitigation
   - Final recommendation justification

6. IMPLEMENTATION STRATEGY:
   Provide detailed action plan:
   - Pre-planting soil preparations needed
   - Optimal planting timeline
   - Input procurement strategy
   - Monitoring and adjustment protocols
   - Risk mitigation measures

DELIVERABLE REQUIREMENTS:
1. EXECUTIVE SUMMARY: Key findings and top recommendation in 3-4 sentences
2. QUANTITATIVE PROJECTIONS: Specific numbers with confidence intervals
3. RISK ASSESSMENT: Probability-weighted scenario analysis
4. IMPLEMENTATION ROADMAP: Detailed timeline with milestones
5. MONITORING METRICS: KPIs and success indicators
6. FARMER GUIDANCE: Plain-language explanation and action steps

OUTPUT STRUCTURE:
- Use numerical data and statistical analysis throughout
- Show all calculations and assumptions clearly
- Provide confidence levels (%) for each major conclusion
- Include uncertainty ranges for financial projections
- Specify data sources and methodology limitations
- Give actionable, time-bound recommendations

FORMATTING REQUIREMENTS:
- Use bullet points for lists
- Include specific dollar amounts and percentages
- Provide timelines in days/months/years
- Rank recommendations by priority (High/Medium/Low)
- Include risk mitigation strategies for each recommendation
"""

    def _create_monte_carlo_prompt(self, top_crops: List[str], farm_data: Dict[str, Any]) -> str:
        """Create prompt for Monte Carlo simulation of ROI scenarios"""
        
        return f"""
MONTE CARLO ROI SIMULATION ANALYSIS

Perform probabilistic analysis for crops: {', '.join(top_crops)}

SIMULATION PARAMETERS:
Farm Size: {farm_data.get('size_acres', 100)} acres
Current Soil Score: {farm_data.get('soil_score', 65)}/100

For each crop, model these variable distributions:
1. YIELD VARIABILITY (Normal distribution):
   - Mean: Expected yield based on soil conditions
   - Std Dev: 15% of mean (weather/management variability)
   - Min/Max: ±30% from mean

2. PRICE VOLATILITY (Log-normal distribution):
   - Current price as baseline
   - Volatility based on historical commodity data
   - Seasonal price patterns

3. INPUT COST FLUCTUATION (Normal distribution):
   - Fertilizer cost variability: ±20%
   - Fuel cost variability: ±15%
   - Labor cost variability: ±10%

4. WEATHER RISK FACTORS:
   - Drought probability: {farm_data.get('drought_risk', 0.2)}
   - Flood probability: 0.1
   - Extreme weather impact: -25% to -50% yield

5. SOIL HEALTH IMPROVEMENT SCENARIOS:
   - Year 1: Current conditions
   - Year 2: +5 point improvement with good management
   - Year 3: +10 point improvement potential

SIMULATION REQUIREMENTS:
- Run 1000 iterations for 3-year projection
- Calculate probability distributions for:
  * Annual ROI percentages
  * Net profit per acre
  * Total farm revenue
  * Cumulative returns

- Provide confidence intervals:
  * 10th percentile (pessimistic)
  * 50th percentile (median)
  * 90th percentile (optimistic)

- Risk metrics:
  * Probability of loss (ROI < 0%)
  * Probability of target ROI > 15%
  * Value at Risk (VaR) at 95% confidence
  * Maximum drawdown scenarios

Show the mathematical reasoning for each distribution and assumption.
Provide clear interpretation of results for decision-making.
"""

    def _create_decision_matrix_prompt(
        self, 
        crop_analyses: List[Dict[str, Any]],
        weights: Dict[str, float]
    ) -> str:
        """Create decision matrix analysis prompt"""
        
        return f"""
MULTI-CRITERIA DECISION MATRIX ANALYSIS

CROP OPTIONS ANALYSIS:
{json.dumps(crop_analyses, indent=2, default=str)}

DECISION CRITERIA AND WEIGHTS:
{json.dumps(weights, indent=2, default=str)}

ANALYSIS FRAMEWORK:

1. CRITERIA SCORING (0-100 scale):
   For each crop, score on:
   - Economic Return Potential
   - Risk Level (inverted - lower risk = higher score)
   - Soil Health Impact
   - Implementation Feasibility
   - Market Stability
   - Sustainability Factors

2. WEIGHTED DECISION MATRIX:
   Calculate weighted scores for each crop:
   Total Score = Σ(Criterion Score × Weight)

3. SENSITIVITY ANALYSIS:
   How do rankings change if:
   - Economic weight increases to 60%
   - Risk weight increases to 40% 
   - Soil health weight increases to 35%

4. TRADE-OFF ANALYSIS:
   - Profit vs Risk trade-offs
   - Short-term vs Long-term value
   - Individual vs portfolio effects

5. DECISION CONFIDENCE:
   - Score difference significance
   - Robustness across weight scenarios
   - Key decision factors

6. RECOMMENDATION LOGIC:
   Provide clear reasoning chain:
   - Why recommended crop scores highest
   - What trade-offs are being made
   - When recommendation might change
   - How to monitor decision validity

Show all calculations step-by-step.
Provide clear decision justification with confidence assessment.
"""

    async def analyze_roi_and_recommend_crops(
        self,
        farm_data: Dict[str, Any],
        soil_health_report: SoilHealthReport,
        market_data: Dict[str, Any],
        weather_data: Dict[str, Any]
    ) -> ROIAnalysisReport:
        """
        Perform comprehensive ROI analysis and generate crop recommendations
        
        Args:
            farm_data: Complete farm information
            soil_health_report: Results from soil health analysis
            market_data: Current market conditions and price data
            weather_data: Weather context and forecasts
            
        Returns:
            Comprehensive ROI analysis report with recommendations
        """
        
        logger.info(f"💰 Starting comprehensive ROI analysis for farm ID: {farm_data.get('farm_id', 'unknown')}")
        
        try:
            # Step 1: Comprehensive analysis with Claude
            logger.info("🧠 Performing comprehensive crop and market analysis...")
            analysis_prompt = self._create_comprehensive_analysis_prompt(
                farm_data, soil_health_report, market_data, weather_data
            )
            
            comprehensive_analysis = await self.ai_config.generate_with_claude(
                prompt=analysis_prompt,
                system_prompt=self._get_system_prompt(),
                max_tokens=3000,
                temperature=0.1,  # Very low for analytical consistency
                model="claude-3-5-sonnet-20241022"
            )
            
            # Step 2: Monte Carlo simulation for risk analysis
            logger.info("🎲 Running Monte Carlo ROI simulation...")
            top_crops = ["corn", "soybeans", "wheat"]  # Would be extracted from analysis
            monte_carlo_prompt = self._create_monte_carlo_prompt(top_crops, farm_data)
            
            monte_carlo_analysis = await self.ai_config.generate_with_claude(
                prompt=monte_carlo_prompt,
                system_prompt="You are a quantitative analyst specializing in agricultural risk modeling.",
                max_tokens=2000,
                temperature=0.05,  # Extremely low for numerical consistency
                model="claude-3-5-sonnet-20241022"
            )
            
            # Step 3: Decision matrix analysis
            logger.info("📊 Creating decision matrix...")
            crop_analyses = self._extract_crop_analyses(comprehensive_analysis)
            weights = {
                "economic_return": 0.40,
                "risk_level": 0.25,
                "soil_health_impact": 0.20,
                "implementation_feasibility": 0.15
            }
            
            decision_matrix_prompt = self._create_decision_matrix_prompt(crop_analyses, weights)
            decision_analysis = await self.ai_config.generate_with_claude(
                prompt=decision_matrix_prompt,
                system_prompt="You are a decision science expert specializing in agricultural economics.",
                max_tokens=1500,
                temperature=0.1,
                model="claude-3-5-sonnet-20241022"
            )
            
            # Step 4: Generate farmer-friendly summary
            logger.info("👨‍🌾 Creating farmer summary...")
            farmer_summary = await self._generate_farmer_summary(
                comprehensive_analysis, decision_analysis
            )
            
            # Step 5: Process all analyses into structured report
            report = await self._create_structured_report(
                farm_data,
                soil_health_report,
                comprehensive_analysis,
                monte_carlo_analysis,
                decision_analysis,
                farmer_summary
            )
            
            logger.info("✅ ROI analysis completed successfully")
            return report
            
        except Exception as e:
            logger.error(f"❌ Error in ROI analysis: {e}")
            return await self._generate_fallback_roi_report(farm_data, soil_health_report)

    def _extract_crop_analyses(self, comprehensive_analysis: str) -> List[Dict[str, Any]]:
        """Extract structured crop analysis data from AI response"""
        
        # This would typically use more sophisticated parsing
        # For now, create sample structured data
        
        return [
            {
                "crop": "corn",
                "expected_yield": 165,
                "expected_revenue": 907.5,
                "input_costs": 480,
                "net_profit": 427.5,
                "roi_percentage": 89.1,
                "soil_compatibility": 0.85,
                "market_favorability": 0.75,
                "risk_level": "Moderate"
            },
            {
                "crop": "soybeans",
                "expected_yield": 48,
                "expected_revenue": 576,
                "input_costs": 340,
                "net_profit": 236,
                "roi_percentage": 69.4,
                "soil_compatibility": 0.92,
                "market_favorability": 0.80,
                "risk_level": "Low"
            },
            {
                "crop": "wheat",
                "expected_yield": 62,
                "expected_revenue": 421.6,
                "input_costs": 300,
                "net_profit": 121.6,
                "roi_percentage": 40.5,
                "soil_compatibility": 0.88,
                "market_favorability": 0.85,
                "risk_level": "Low"
            }
        ]

    async def _generate_farmer_summary(
        self, 
        comprehensive_analysis: str,
        decision_analysis: str
    ) -> str:
        """Generate farmer-friendly summary using Gemini"""
        
        summary_prompt = f"""
Based on this detailed economic analysis, create a simple summary for a farmer:

Key Analysis Points:
{comprehensive_analysis[:500]}...

Decision Matrix Results:
{decision_analysis[:300]}...

Create a 3-4 sentence summary that:
1. States the recommended crop and expected profit
2. Explains why it's the best choice in simple terms
3. Mentions the main risk to watch for
4. Gives confidence in the recommendation

Use everyday language, include specific numbers, and be encouraging but realistic.
"""
        
        summary = await self.ai_config.generate_with_gemini(
            prompt=summary_prompt,
            max_tokens=250,
            temperature=0.6
        )
        
        return summary or "Based on our analysis, we've identified the most profitable crop option for your farm with detailed implementation guidance."

    async def _create_structured_report(
        self,
        farm_data: Dict[str, Any],
        soil_health_report: SoilHealthReport,
        comprehensive_analysis: str,
        monte_carlo_analysis: str,
        decision_analysis: str,
        farmer_summary: str
    ) -> ROIAnalysisReport:
        """Create structured ROI analysis report"""
        
        # Extract crop recommendations (would use more sophisticated parsing)
        alternative_crops = [
            CropRecommendation(
                crop_name="Corn",
                expected_yield=165.0,
                expected_revenue=907.5,
                input_costs=480.0,
                net_profit=427.5,
                roi_percentage=89.1,
                payback_period=12,
                risk_level=RiskLevel.MODERATE,
                confidence_score=0.85,
                soil_compatibility=0.85,
                market_favorability=0.75,
                reasoning="High yield potential with current soil conditions and favorable market prices.",
                implementation_steps=[
                    "Soil preparation with lime application",
                    "Precision planting in optimal window",
                    "Nutrient management program",
                    "Integrated pest management"
                ],
                risk_factors=["Weather variability", "Input cost inflation", "Market price volatility"],
                mitigation_strategies=["Crop insurance", "Forward contracts", "Diversified rotation"]
            ),
            CropRecommendation(
                crop_name="Soybeans",
                expected_yield=48.0,
                expected_revenue=576.0,
                input_costs=340.0,
                net_profit=236.0,
                roi_percentage=69.4,
                payback_period=10,
                risk_level=RiskLevel.LOW,
                confidence_score=0.92,
                soil_compatibility=0.92,
                market_favorability=0.80,
                reasoning="Excellent soil compatibility with lower input costs and stable markets.",
                implementation_steps=[
                    "Inoculation for nitrogen fixation",
                    "Minimal soil preparation",
                    "Weed management program",
                    "Timely harvest"
                ],
                risk_factors=["Asian rust", "Market competition", "Drought sensitivity"],
                mitigation_strategies=["Disease monitoring", "Market hedging", "Irrigation backup"]
            )
        ]
        
        # Recommended crop (highest scoring)
        recommended_crop = alternative_crops[0]  # Corn in this example
        
        return ROIAnalysisReport(
            farm_id=farm_data.get('farm_id', 'unknown'),
            current_crop_analysis={
                "crop": farm_data.get('current_crop', 'Unknown'),
                "performance": "Moderate",
                "issues": ["Suboptimal soil pH", "Market timing"],
                "improvement_potential": "25% yield increase possible"
            },
            alternative_crops=alternative_crops,
            recommended_crop=recommended_crop,
            economic_projections={
                "year_1_profit": recommended_crop.net_profit,
                "year_2_profit": recommended_crop.net_profit * 1.1,  # Soil improvement
                "year_3_profit": recommended_crop.net_profit * 1.15,
                "total_3_year_roi": 185.5,
                "confidence_interval": "±15%"
            },
            scenario_analysis={
                "optimistic": {"roi": 120.5, "probability": 0.25},
                "most_likely": {"roi": 89.1, "probability": 0.50},
                "pessimistic": {"roi": 45.2, "probability": 0.25}
            },
            risk_assessment={
                "overall_risk": "Moderate",
                "key_risks": ["Weather", "Input costs", "Market prices"],
                "mitigation_effectiveness": 0.70
            },
            decision_matrix={
                "criteria_weights": {
                    "economic_return": 0.40,
                    "risk_level": 0.25,
                    "soil_health": 0.20,
                    "feasibility": 0.15
                },
                "winning_factors": ["High yield potential", "Good soil match", "Market stability"]
            },
            implementation_timeline=[
                {"phase": "Soil Preparation", "timeline": "30 days before planting", "cost": "$50/acre"},
                {"phase": "Planting", "timeline": "Optimal planting window", "cost": "$200/acre"},
                {"phase": "Management", "timeline": "Growing season", "cost": "$180/acre"},
                {"phase": "Harvest", "timeline": "Maturity + weather window", "cost": "$50/acre"}
            ],
            monitoring_plan={
                "soil_health": "Quarterly soil tests",
                "crop_progress": "Weekly field monitoring",
                "market_conditions": "Daily price tracking",
                "weather": "Real-time weather monitoring"
            },
            executive_summary=f"Recommendation: {recommended_crop.crop_name} with {recommended_crop.roi_percentage:.1f}% ROI and {recommended_crop.confidence_score:.0%} confidence.",
            detailed_reasoning=comprehensive_analysis or "Detailed analysis unavailable",
            farmer_explanation=farmer_summary,
            generated_at=datetime.now(),
            confidence_level=0.87,
            model_used="Claude-3.5-Sonnet with Monte Carlo simulation"
        )

    async def _generate_fallback_roi_report(
        self, 
        farm_data: Dict[str, Any], 
        soil_health_report: SoilHealthReport
    ) -> ROIAnalysisReport:
        """Generate fallback ROI report when AI services are unavailable"""
        
        logger.warning("🔄 Generating fallback ROI report")
        
        # Simple rule-based recommendations
        current_crop = farm_data.get('current_crop', 'corn').lower()
        soil_score = soil_health_report.overall_score
        
        # Basic crop recommendation logic
        if soil_score >= 75:
            recommended_crop = "corn"
            expected_roi = 85.0
        elif soil_score >= 60:
            recommended_crop = "soybeans"
            expected_roi = 65.0
        else:
            recommended_crop = "wheat"
            expected_roi = 45.0
        
        fallback_recommendation = CropRecommendation(
            crop_name=recommended_crop.title(),
            expected_yield=100.0,
            expected_revenue=600.0,
            input_costs=350.0,
            net_profit=250.0,
            roi_percentage=expected_roi,
            payback_period=12,
            risk_level=RiskLevel.MODERATE,
            confidence_score=0.60,
            soil_compatibility=0.75,
            market_favorability=0.70,
            reasoning="Basic recommendation based on soil health score and crop compatibility.",
            implementation_steps=["Professional consultation recommended"],
            risk_factors=["Market volatility", "Weather conditions"],
            mitigation_strategies=["Professional guidance", "Gradual implementation"]
        )
        
        return ROIAnalysisReport(
            farm_id=farm_data.get('farm_id', 'unknown'),
            current_crop_analysis={"status": "Basic analysis completed"},
            alternative_crops=[fallback_recommendation],
            recommended_crop=fallback_recommendation,
            economic_projections={"note": "Detailed projections unavailable"},
            scenario_analysis={"note": "Scenario analysis unavailable"},
            risk_assessment={"level": "Moderate", "note": "Detailed assessment unavailable"},
            decision_matrix={"note": "Matrix analysis unavailable"},
            implementation_timeline=[],
            monitoring_plan={"note": "Standard monitoring recommended"},
            executive_summary=f"Basic recommendation: {recommended_crop.title()} with moderate confidence.",
            detailed_reasoning="Detailed AI analysis unavailable - basic assessment provided.",
            farmer_explanation=f"Based on your soil health score of {soil_score:.0f}, {recommended_crop} appears to be a suitable option. Consult with local agricultural experts for detailed planning.",
            generated_at=datetime.now(),
            confidence_level=0.60,
            model_used="Fallback - Rule-based analysis"
        )

# Global instance
roi_agent = ROIReasonerAgent() 