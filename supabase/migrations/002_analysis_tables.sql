-- Migration: 002_analysis_tables.sql
-- Description: Add tables for soil health analyses and zone-based analysis results
-- Author: SoilGuard Team
-- Date: 2024

-- =====================================================
-- SOIL HEALTH ANALYSES TABLE
-- Stores the results of AI-powered soil health analysis
-- =====================================================

CREATE TABLE IF NOT EXISTS soil_health_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Analysis status tracking
    status VARCHAR(20) NOT NULL DEFAULT 'pending' 
        CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    
    -- Overall metrics
    overall_health DECIMAL(5,2),
    confidence_score DECIMAL(5,2),
    
    -- Satellite data source info
    satellite_source VARCHAR(100),
    resolution_meters INTEGER,
    data_quality_score DECIMAL(5,2),
    
    -- Zone-based analysis results (JSONB for flexibility)
    zone_data JSONB,
    problem_zones TEXT[],
    heatmap_data JSONB,
    
    -- Raw satellite indices
    ndvi DECIMAL(5,4),
    ndwi DECIMAL(5,4),
    ndmi DECIMAL(5,4),
    bsi DECIMAL(5,4),
    savi DECIMAL(5,4),
    evi DECIMAL(5,4),
    
    -- AI-generated insights
    ai_summary TEXT,
    recommendations JSONB,
    risk_factors JSONB,
    
    -- Weather context at time of analysis
    weather_context JSONB,
    
    -- Timestamps
    analysis_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    
    -- Error tracking
    error_message TEXT
);

-- =====================================================
-- ROI ANALYSES TABLE
-- Stores ROI and crop recommendation analysis results
-- =====================================================

CREATE TABLE IF NOT EXISTS roi_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Analysis status tracking
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    
    -- Current crop analysis
    current_crop VARCHAR(100),
    current_crop_roi JSONB,
    
    -- Alternative crop recommendations
    recommendations JSONB,
    
    -- Market data context
    market_data JSONB,
    price_trends JSONB,
    
    -- Risk assessment
    risk_assessment JSONB,
    weather_impact JSONB,
    
    -- AI-generated insights
    ai_summary TEXT,
    strategic_advice TEXT,
    
    -- Financial projections
    projected_revenue DECIMAL(12,2),
    projected_costs DECIMAL(12,2),
    projected_profit DECIMAL(12,2),
    
    -- Timestamps
    analysis_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    
    -- Error tracking
    error_message TEXT
);

-- =====================================================
-- ZONE ANALYSIS HISTORY TABLE
-- Tracks individual zone analysis results over time
-- =====================================================

CREATE TABLE IF NOT EXISTS zone_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    soil_health_analysis_id UUID NOT NULL REFERENCES soil_health_analyses(id) ON DELETE CASCADE,
    farm_id UUID NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
    
    -- Zone identification
    zone_id VARCHAR(20) NOT NULL,
    zone_row INTEGER NOT NULL,
    zone_col INTEGER NOT NULL,
    
    -- Zone geometry
    center_lat DECIMAL(10,7) NOT NULL,
    center_lng DECIMAL(10,7) NOT NULL,
    bounds JSONB NOT NULL,
    area_hectares DECIMAL(10,4),
    
    -- Health metrics
    health_score DECIMAL(5,2),
    status VARCHAR(20) CHECK (status IN ('healthy', 'moderate', 'degraded', 'critical')),
    
    -- Spectral indices
    ndvi DECIMAL(5,4),
    ndwi DECIMAL(5,4),
    ndmi DECIMAL(5,4),
    moisture DECIMAL(5,2),
    
    -- Alerts and recommendations
    alerts TEXT[],
    recommendations TEXT[],
    
    -- Data quality
    data_quality DECIMAL(5,2),
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Soil health analyses indexes
CREATE INDEX IF NOT EXISTS idx_soil_health_farm_id ON soil_health_analyses(farm_id);
CREATE INDEX IF NOT EXISTS idx_soil_health_user_id ON soil_health_analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_soil_health_status ON soil_health_analyses(status);
CREATE INDEX IF NOT EXISTS idx_soil_health_created_at ON soil_health_analyses(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_soil_health_analysis_date ON soil_health_analyses(analysis_date DESC);

-- ROI analyses indexes
CREATE INDEX IF NOT EXISTS idx_roi_farm_id ON roi_analyses(farm_id);
CREATE INDEX IF NOT EXISTS idx_roi_user_id ON roi_analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_roi_status ON roi_analyses(status);
CREATE INDEX IF NOT EXISTS idx_roi_created_at ON roi_analyses(created_at DESC);

-- Zone analyses indexes
CREATE INDEX IF NOT EXISTS idx_zone_analysis_id ON zone_analyses(soil_health_analysis_id);
CREATE INDEX IF NOT EXISTS idx_zone_farm_id ON zone_analyses(farm_id);
CREATE INDEX IF NOT EXISTS idx_zone_health ON zone_analyses(health_score);

-- =====================================================
-- ROW LEVEL SECURITY (RLS)
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE soil_health_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE roi_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE zone_analyses ENABLE ROW LEVEL SECURITY;

-- Soil health analyses policies
CREATE POLICY "Users can view their own soil health analyses"
    ON soil_health_analyses FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own soil health analyses"
    ON soil_health_analyses FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own soil health analyses"
    ON soil_health_analyses FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own soil health analyses"
    ON soil_health_analyses FOR DELETE
    USING (auth.uid() = user_id);

-- ROI analyses policies
CREATE POLICY "Users can view their own roi analyses"
    ON roi_analyses FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own roi analyses"
    ON roi_analyses FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own roi analyses"
    ON roi_analyses FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own roi analyses"
    ON roi_analyses FOR DELETE
    USING (auth.uid() = user_id);

-- Zone analyses policies (join through soil_health_analyses)
CREATE POLICY "Users can view their own zone analyses"
    ON zone_analyses FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM soil_health_analyses sha
            WHERE sha.id = zone_analyses.soil_health_analysis_id
            AND sha.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert zone analyses for their analyses"
    ON zone_analyses FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM soil_health_analyses sha
            WHERE sha.id = zone_analyses.soil_health_analysis_id
            AND sha.user_id = auth.uid()
        )
    );

-- =====================================================
-- UPDATED_AT TRIGGERS
-- Uses handle_updated_at() function from 001_initial_schema.sql
-- =====================================================

CREATE TRIGGER update_soil_health_analyses_updated_at
    BEFORE UPDATE ON soil_health_analyses
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

CREATE TRIGGER update_roi_analyses_updated_at
    BEFORE UPDATE ON roi_analyses
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

-- =====================================================
-- VIEWS FOR DASHBOARD AGGREGATIONS
-- =====================================================

-- Latest analysis per farm view
CREATE OR REPLACE VIEW latest_farm_analyses AS
SELECT DISTINCT ON (farm_id)
    sha.id,
    sha.farm_id,
    sha.user_id,
    sha.overall_health,
    sha.status,
    sha.zone_data,
    sha.problem_zones,
    sha.ai_summary,
    sha.created_at,
    f.name as farm_name,
    f.crop_type,
    f.area_hectares
FROM soil_health_analyses sha
JOIN farms f ON f.id = sha.farm_id
WHERE sha.status = 'completed'
ORDER BY farm_id, sha.created_at DESC;

-- Farm health summary view
CREATE OR REPLACE VIEW farm_health_summary AS
SELECT
    f.id as farm_id,
    f.name as farm_name,
    f.user_id,
    f.area_hectares,
    f.crop_type,
    COUNT(sha.id) as total_analyses,
    AVG(sha.overall_health) as avg_health,
    MAX(sha.created_at) as last_analysis,
    COALESCE(
        (SELECT overall_health FROM soil_health_analyses 
         WHERE farm_id = f.id AND status = 'completed' 
         ORDER BY created_at DESC LIMIT 1),
        0
    ) as current_health
FROM farms f
LEFT JOIN soil_health_analyses sha ON sha.farm_id = f.id AND sha.status = 'completed'
GROUP BY f.id, f.name, f.user_id, f.area_hectares, f.crop_type;

-- =====================================================
-- COMMENTS FOR DOCUMENTATION
-- =====================================================

COMMENT ON TABLE soil_health_analyses IS 'Stores AI-powered soil health analysis results with zone-level data';
COMMENT ON TABLE roi_analyses IS 'Stores ROI and crop recommendation analysis results';
COMMENT ON TABLE zone_analyses IS 'Stores individual zone analysis results for spatial analysis';

COMMENT ON COLUMN soil_health_analyses.zone_data IS 'JSONB array of zone analysis results with health scores, alerts, and recommendations';
COMMENT ON COLUMN soil_health_analyses.heatmap_data IS '2D array of health scores for heatmap visualization';
COMMENT ON COLUMN soil_health_analyses.problem_zones IS 'Array of zone IDs that need attention (health < 55)';

