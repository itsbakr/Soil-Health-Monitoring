# SoilGuard - Soil Health Monitoring & Agricultural ROI Platform

A comprehensive agricultural platform that combines satellite data analysis, weather monitoring, and market intelligence to help farmers optimize soil health and maximize ROI through data-driven decision making.

## 🌟 Features

### Core Analysis
- **🛰️ Satellite Data Analysis**: Google Earth Engine integration for vegetation and soil health monitoring
- **🌦️ Weather Intelligence**: Real-time weather data with agricultural indices (GDD, drought risk, frost alerts)
- **📈 Market Analysis**: Crop price monitoring and market sentiment analysis
- **🤖 AI-Powered Insights**: Intelligent soil health assessment and crop recommendations using Gemini & Claude
- **📊 Comprehensive Dashboard**: Interactive farm management with real-time analytics
- **🔄 Real-time Updates**: Automated monitoring with alert systems

### 🆕 Spatial Zone Analysis
- **🗺️ Dynamic Grid System**: Auto-generates analysis zones based on farm size
  - < 2 ha: 2×2 grid (4 zones) using Sentinel-2 (10m resolution)
  - 2-10 ha: 3×3 grid (9 zones) using Sentinel-2 (10m resolution)
  - 10-50 ha: 4×4 grid (16 zones) using Landsat (30m resolution)
  - 50+ ha: 5×5 grid (25 zones) using Landsat (30m resolution)
- **🎯 Zone-Level Recommendations**: AI agents provide specific actions for each problem zone
- **🔥 Interactive Health Map**: Satellite imagery overlay with color-coded zones showing exactly WHERE problems are

### 🆕 Analysis History & Persistence
- **💾 Database Storage**: All soil health and ROI analyses are saved to Supabase
- **📜 Analysis History**: View and compare past analyses for trend tracking
- **🔍 Historical Insights**: Click any past analysis to view full details
- **📊 Trend Analysis**: Track farm health improvements over time

## 🛠️ Tech Stack

**Frontend:**
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- React Components

**Backend:**
- FastAPI (Python)
- Supabase (Database & Auth)
- Google Earth Engine API
- OpenWeatherMap API
- Various commodity price APIs

**AI & Analysis:**
- Google Gemini API
- Anthropic Claude API
- Custom satellite data processing
- Agricultural algorithms

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/larmms.git
cd larmms
```

### 2. Environment Setup

Copy the environment template and configure your API keys:

```bash
cp env.template .env
# Edit .env with your actual API keys (see API Setup section below)
```

### 3. Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 5. Database Setup

```bash
# Run Supabase migrations
supabase db push
```

## 🔑 API Setup Guide

### Required APIs

#### 1. Supabase (Required) 
**Purpose**: Database, Authentication, Real-time subscriptions

**Setup Steps:**
1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Go to Settings → API
4. Copy your Project URL and API keys

**Environment Variables:**
```bash
NEXT_PUBLIC_SUPABASE_URL=your_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

**Cost**: Free tier (up to 50MB database, 100MB file storage)

---

### Optional APIs (Graceful Fallbacks Available)

#### 2. Google Earth Engine (Optional)
**Purpose**: Satellite imagery analysis for soil and vegetation monitoring

**Setup Steps:**
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable Earth Engine API
4. Set up authentication:
   ```bash
   pip install earthengine-api
   earthengine authenticate
   ```

**Environment Variables:**
```bash
GOOGLE_CLOUD_PROJECT_ID=your_project_id
```

**Cost**: Free for research/non-commercial (25,000 API calls/day)

#### 3. OpenWeatherMap (Optional)
**Purpose**: Weather data and agricultural forecasting

**Setup Steps:**
1. Go to [OpenWeatherMap](https://openweathermap.org/api)
2. Sign up for free account
3. Generate API key

**Environment Variables:**
```bash
OPENWEATHERMAP_API_KEY=your_api_key
```

**Cost**: Free tier (1,000 calls/day), $40/month for 100k calls

#### 4. Commodity Price APIs (Optional) - Multiple Free Tiers Available

**4a. Alpha Vantage** (RECOMMENDED)
- Website: [alphavantage.co](https://www.alphavantage.co/support/#api-key)
- Cost: **25 requests/day FREE**, then $49.99/month unlimited
- Perfect for development and light production use
- Variable: `ALPHA_VANTAGE_API_KEY`

**4b. Twelve Data** (Best Free Tier)
- Website: [twelvedata.com/pricing](https://twelvedata.com/pricing)
- Cost: **800 requests/day FREE**, excellent coverage
- Variable: `TWELVE_DATA_API_KEY`

**4c. Financial Modeling Prep**
- Website: [financialmodelingprep.com](https://financialmodelingprep.com/developer/docs)
- Cost: **250 requests/day FREE**
- Variable: `FMP_API_KEY`

**4d. Commodities API** (Paid Only)
- Website: [commodities-api.com](https://commodities-api.com)
- Cost: 7-day free trial only, then $49.99/month minimum
- Variable: `COMMODITIES_API_KEY`

#### 5. AI APIs (Optional)

**5a. Google Gemini**
- Website: [Google AI Studio](https://console.cloud.google.com/apis/credentials)
- Cost: Free tier (15 requests/minute), pay-per-use beyond
- Variable: `GOOGLE_GEMINI_API_KEY`

**5b. Anthropic Claude**
- Website: [console.anthropic.com](https://console.anthropic.com)
- Cost: Pay-per-use ($3/million input tokens)
- Variable: `ANTHROPIC_API_KEY`

**5c. OpenAI**
- Website: [platform.openai.com](https://platform.openai.com/api-keys)
- Cost: Pay-per-use ($0.50-$20/million tokens depending on model)
- Variable: `OPENAI_API_KEY`

## 💰 Cost Breakdown

### Free Tier (Recommended for Development)
- **Supabase**: Free
- **Google Earth Engine**: Free (research use)
- **OpenWeatherMap**: Free (1k calls/day)
- **All other APIs**: Demo data fallbacks
- **Total**: $0/month

### Production Tier (Recommended for Live Usage)
- **Supabase Pro**: $25/month
- **OpenWeatherMap**: $40/month (100k calls)
- **Alpha Vantage**: $49.99/month OR use free tier (25 calls/day)
- **AI APIs**: ~$10-50/month (depending on usage)
- **Total**: ~$75-165/month (or ~$75/month with free commodity API tier)

## 🏗️ Project Structure

```
SoilGuard/
├── frontend/                    # Next.js frontend application
│   ├── src/
│   │   ├── app/                # App router pages
│   │   │   └── dashboard/      # Farm management pages
│   │   ├── components/
│   │   │   ├── Analysis/       # SoilHealthDisplay, ROIDisplay, AnalysisHistory, ZoneMapOverlay
│   │   │   ├── Map/            # Interactive maps and location picker
│   │   │   └── FarmerDashboard/# Health gauges, action cards, zone alerts
│   │   └── lib/                # API client, Supabase config, utilities
├── backend/                    # FastAPI backend application
│   ├── routers/
│   │   ├── analysis.py        # Soil health, ROI, zonal analysis endpoints + history
│   │   ├── farms.py           # Farm CRUD operations
│   │   └── auth.py            # Authentication endpoints
│   ├── services/
│   │   ├── satellite_service.py    # Google Earth Engine integration
│   │   ├── spatial_grid.py         # 🆕 Dynamic zone grid generation
│   │   ├── soil_health_agent.py    # AI soil analysis with zone recommendations
│   │   ├── roi_agent.py            # AI crop ROI analysis
│   │   └── ai_config.py            # Gemini + Claude configuration
│   ├── utils/
│   │   ├── database.py             # 🆕 Supabase client for persistence
│   │   └── satellite_calculations.py
│   └── requirements.txt
├── supabase/
│   └── migrations/
│       ├── 001_initial_schema.sql      # Users, farms tables
│       └── 002_analysis_tables.sql     # 🆕 soil_health_analyses, roi_analyses tables
├── backend/env.example         # Backend environment template
├── frontend/env.example        # Frontend environment template
└── README.md
```

## 🧪 Testing the Platform

### 1. Check Service Status
```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/analysis/status
```

### 2. Test Farm Creation
1. Open http://localhost:3000
2. Register/Login
3. Add a new farm with pin drop location
4. View satellite analysis

### 3. Test Analysis Pipeline
The platform automatically processes:
- Satellite vegetation indices (NDVI, NDWI, SAVI, EVI, etc.)
- Zone-based health scoring (dynamic grid based on farm size)
- Weather risk assessment
- Market price analysis
- AI-powered recommendations with zone-specific actions

### 4. Test Analysis History
1. Run a complete analysis on a farm
2. Expand the "Analysis History" section on the farm page
3. View past analyses and click to see full details
4. Compare trends over time

## 🚀 Deployment

### Frontend (Vercel)
```bash
# Deploy to Vercel
npm run build
vercel --prod
```

### Backend (Railway/Fly.io)
```bash
# Deploy to Railway
railway login
railway init
railway up
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request



**Built with ❤️ for sustainable agriculture and data-driven farming** 
