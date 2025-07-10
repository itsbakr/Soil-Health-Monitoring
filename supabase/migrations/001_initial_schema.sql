-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create farms table
CREATE TABLE public.farms (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    location_lat DECIMAL(10, 8) NOT NULL,
    location_lng DECIMAL(11, 8) NOT NULL,
    area_hectares DECIMAL(10, 4) NOT NULL CHECK (area_hectares > 0),
    crop_type VARCHAR(100) NOT NULL,
    planting_date DATE,
    harvest_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    
    CONSTRAINT valid_coordinates CHECK (
        location_lat >= -90 AND location_lat <= 90 AND
        location_lng >= -180 AND location_lng <= 180
    ),
    CONSTRAINT valid_dates CHECK (
        planting_date IS NULL OR harvest_date IS NULL OR harvest_date > planting_date
    )
);

-- Create soil health reports table
CREATE TABLE public.soil_health_reports (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    farm_id UUID NOT NULL REFERENCES public.farms(id) ON DELETE CASCADE,
    report_date TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    ph_level DECIMAL(3, 2) CHECK (ph_level >= 0 AND ph_level <= 14),
    salinity_level DECIMAL(8, 4) CHECK (salinity_level >= 0),
    moisture_content DECIMAL(5, 2) CHECK (moisture_content >= 0 AND moisture_content <= 100),
    temperature DECIMAL(5, 2),
    ndvi_score DECIMAL(4, 3) CHECK (ndvi_score >= -1 AND ndvi_score <= 1),
    health_score INTEGER NOT NULL CHECK (health_score >= 0 AND health_score <= 100),
    recommendations TEXT NOT NULL,
    ai_analysis TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Create crop recommendations table
CREATE TABLE public.crop_recommendations (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    farm_id UUID NOT NULL REFERENCES public.farms(id) ON DELETE CASCADE,
    crop_name VARCHAR(100) NOT NULL,
    expected_yield DECIMAL(10, 2) NOT NULL CHECK (expected_yield >= 0),
    estimated_revenue DECIMAL(12, 2) NOT NULL CHECK (estimated_revenue >= 0),
    estimated_costs DECIMAL(12, 2) NOT NULL CHECK (estimated_costs >= 0),
    roi_percentage DECIMAL(5, 2) NOT NULL,
    confidence_score INTEGER NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 100),
    reasoning TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc'::text, NOW());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for farms table
CREATE TRIGGER set_farms_updated_at
    BEFORE UPDATE ON public.farms
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

-- Create indexes for better performance
CREATE INDEX idx_farms_user_id ON public.farms(user_id);
CREATE INDEX idx_farms_created_at ON public.farms(created_at DESC);
CREATE INDEX idx_soil_health_reports_farm_id ON public.soil_health_reports(farm_id);
CREATE INDEX idx_soil_health_reports_report_date ON public.soil_health_reports(report_date DESC);
CREATE INDEX idx_crop_recommendations_farm_id ON public.crop_recommendations(farm_id);
CREATE INDEX idx_crop_recommendations_roi ON public.crop_recommendations(roi_percentage DESC);

-- Enable Row Level Security (RLS)
ALTER TABLE public.farms ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.soil_health_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.crop_recommendations ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for farms table
CREATE POLICY "Users can view their own farms" ON public.farms
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own farms" ON public.farms
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own farms" ON public.farms
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own farms" ON public.farms
    FOR DELETE USING (auth.uid() = user_id);

-- Create RLS policies for soil health reports table
CREATE POLICY "Users can view soil health reports for their farms" ON public.soil_health_reports
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.farms 
            WHERE farms.id = soil_health_reports.farm_id 
            AND farms.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert soil health reports for their farms" ON public.soil_health_reports
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.farms 
            WHERE farms.id = soil_health_reports.farm_id 
            AND farms.user_id = auth.uid()
        )
    );

-- Create RLS policies for crop recommendations table
CREATE POLICY "Users can view crop recommendations for their farms" ON public.crop_recommendations
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.farms 
            WHERE farms.id = crop_recommendations.farm_id 
            AND farms.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert crop recommendations for their farms" ON public.crop_recommendations
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.farms 
            WHERE farms.id = crop_recommendations.farm_id 
            AND farms.user_id = auth.uid()
        )
    );

-- Create a view for farm statistics (optional, for dashboard)
CREATE VIEW public.farm_stats AS
SELECT 
    f.id,
    f.user_id,
    f.name,
    f.area_hectares,
    f.crop_type,
    COUNT(shr.id) as total_reports,
    MAX(shr.report_date) as latest_report_date,
    AVG(shr.health_score) as avg_health_score,
    COUNT(cr.id) as total_recommendations,
    MAX(cr.roi_percentage) as best_roi_percentage
FROM public.farms f
LEFT JOIN public.soil_health_reports shr ON f.id = shr.farm_id
LEFT JOIN public.crop_recommendations cr ON f.id = cr.farm_id
GROUP BY f.id, f.user_id, f.name, f.area_hectares, f.crop_type;

-- Enable RLS for the view
ALTER VIEW public.farm_stats SET (security_invoker = true);

-- Insert some sample crop types for reference (optional)
CREATE TABLE public.crop_types (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL,
    growing_season_days INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Insert common crop types
INSERT INTO public.crop_types (name, category, growing_season_days) VALUES
('Rice', 'Grain', 120),
('Wheat', 'Grain', 90),
('Corn (Maize)', 'Grain', 100),
('Soybeans', 'Legume', 110),
('Potatoes', 'Root Vegetable', 80),
('Tomatoes', 'Fruit Vegetable', 75),
('Carrots', 'Root Vegetable', 70),
('Lettuce', 'Leafy Green', 45),
('Cabbage', 'Leafy Green', 90),
('Onions', 'Bulb Vegetable', 100);

-- Make crop_types table readable by all authenticated users
ALTER TABLE public.crop_types ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Crop types are viewable by all authenticated users" ON public.crop_types
    FOR SELECT USING (auth.role() = 'authenticated'); 