# 🚀 LARMMS Deployment Guide

This guide covers deploying the LARMMS platform to production environments.

## 📋 Pre-Deployment Checklist

### 1. Environment Variables
- [ ] All required API keys configured
- [ ] Database credentials set
- [ ] CORS origins updated for production domains
- [ ] Secret keys generated (minimum 32 characters)

### 2. Database Setup
- [ ] Supabase project created
- [ ] Database migrations applied
- [ ] Row Level Security (RLS) policies configured
- [ ] Backup strategy implemented

### 3. API Keys & Limits
- [ ] Production API keys obtained (not development keys)
- [ ] Rate limits and quotas reviewed
- [ ] Billing alerts configured
- [ ] API key rotation schedule planned

## 🌐 Frontend Deployment (Vercel)

### Method 1: GitHub Integration (Recommended)

1. **Connect Repository**
   ```bash
   # Push to GitHub first
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Vercel Setup**
   - Go to [vercel.com](https://vercel.com)
   - Import your GitHub repository
   - Select `frontend` as root directory

3. **Environment Variables**
   ```bash
   # In Vercel dashboard, add these variables:
   NEXT_PUBLIC_SUPABASE_URL=your_production_supabase_url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_production_anon_key
   NEXT_PUBLIC_API_URL=https://your-backend-domain.com
   NODE_ENV=production
   ```

4. **Deploy**
   - Vercel will automatically deploy on pushes to main branch

### Method 2: Manual Deployment

```bash
cd frontend
npm run build
npx vercel --prod
```

## 🖥️ Backend Deployment

### Option A: Railway (Recommended)

1. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   railway login
   ```

2. **Initialize Project**
   ```bash
   cd backend
   railway init
   railway add postgresql  # If you need a separate DB
   ```

3. **Set Environment Variables**
   ```bash
   railway variables set SUPABASE_URL=your_production_url
   railway variables set SUPABASE_ANON_KEY=your_production_key
   railway variables set OPENWEATHERMAP_API_KEY=your_key
   # Add all other variables from env.template
   ```

4. **Deploy**
   ```bash
   railway up
   ```

### Option B: Fly.io

1. **Install Fly CLI**
   ```bash
   # Install flyctl
   curl -L https://fly.io/install.sh | sh
   flyctl auth login
   ```

2. **Create Fly App**
   ```bash
   cd backend
   flyctl apps create your-app-name
   ```

3. **Configure fly.toml**
   ```toml
   app = "your-app-name"
   kill_signal = "SIGINT"
   kill_timeout = 5
   processes = []

   [env]
     PORT = "8000"

   [experimental]
     auto_rollback = true

   [[services]]
     http_checks = []
     internal_port = 8000
     processes = ["app"]
     protocol = "tcp"
     script_checks = []
     [services.concurrency]
       hard_limit = 25
       soft_limit = 20
       type = "connections"

     [[services.ports]]
       force_https = true
       handlers = ["http"]
       port = 80

     [[services.ports]]
       handlers = ["tls", "http"]
       port = 443

     [[services.tcp_checks]]
       grace_period = "1s"
       interval = "15s"
       restart_limit = 0
       timeout = "2s"
   ```

4. **Set Secrets**
   ```bash
   flyctl secrets set SUPABASE_URL=your_production_url
   flyctl secrets set SUPABASE_ANON_KEY=your_production_key
   # Add all other secrets
   ```

5. **Deploy**
   ```bash
   flyctl deploy
   ```

### Option C: Docker + Cloud Run

1. **Create Dockerfile**
   ```dockerfile
   FROM python:3.11-slim

   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY . .
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

2. **Build and Deploy**
   ```bash
   # Build image
   docker build -t larmms-backend .

   # Deploy to Google Cloud Run
   gcloud run deploy larmms-backend \
     --image gcr.io/your-project/larmms-backend \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

## 🗄️ Database Production Setup

### Supabase Configuration

1. **Create Production Project**
   - Go to [supabase.com](https://supabase.com)
   - Create new project (not the same as development)
   - Choose appropriate pricing tier

2. **Run Migrations**
   ```bash
   # Install Supabase CLI
   npm install -g supabase

   # Link to production project
   supabase link --project-ref your-production-project-ref

   # Push migrations
   supabase db push
   ```

3. **Configure RLS Policies**
   ```sql
   -- Enable RLS on all tables
   ALTER TABLE farms ENABLE ROW LEVEL SECURITY;
   ALTER TABLE soil_health_reports ENABLE ROW LEVEL SECURITY;
   ALTER TABLE roi_analysis_reports ENABLE ROW LEVEL SECURITY;

   -- Example policy for farms table
   CREATE POLICY "Users can view own farms" ON farms
     FOR SELECT USING (auth.uid() = user_id);

   CREATE POLICY "Users can insert own farms" ON farms
     FOR INSERT WITH CHECK (auth.uid() = user_id);
   ```

4. **Set Up Backups**
   - Enable automatic backups in Supabase dashboard
   - Configure backup retention period
   - Test restore procedures

## 📊 Monitoring & Analytics

### 1. Application Monitoring

**Sentry Integration**
```bash
# Install Sentry
npm install @sentry/nextjs @sentry/python

# Frontend: next.config.js
const { withSentryConfig } = require('@sentry/nextjs');
module.exports = withSentryConfig(nextConfig, sentryWebpackPluginOptions);

# Backend: main.py
import sentry_sdk
sentry_sdk.init(dsn="your-sentry-dsn")
```

**Uptime Monitoring**
- Set up monitors on [UptimeRobot](https://uptimerobot.com)
- Monitor both frontend and backend endpoints
- Configure alert notifications

### 2. Performance Monitoring

**Vercel Analytics**
```bash
# Install Vercel Analytics
npm install @vercel/analytics

# Add to app layout
import { Analytics } from '@vercel/analytics/react';
export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  );
}
```

### 3. API Monitoring

```python
# Backend: Add to main.py
from fastapi import Request
import time

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

## 🔒 Security Configuration

### 1. CORS Setup
```python
# backend/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://www.yourdomain.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. Rate Limiting
```python
# Install slowapi
pip install slowapi

# Add to main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/analysis/soil-health")
@limiter.limit("5/minute")
async def analyze_soil_health(request: Request):
    # Your endpoint logic
```

### 3. Environment Security
```bash
# Use secrets management
# Never commit .env files
# Rotate API keys regularly
# Use different keys for dev/staging/prod
```

## 📈 Scaling Considerations

### 1. Database Scaling
- **Supabase Pro**: Handles moderate traffic
- **Connection Pooling**: Configure pgBouncer
- **Read Replicas**: For read-heavy workloads

### 2. API Scaling
- **Vertical Scaling**: Increase instance size
- **Horizontal Scaling**: Multiple instances with load balancer
- **Caching**: Implement Redis for frequently accessed data

### 3. CDN Configuration
```bash
# Vercel automatically provides CDN
# For custom setup, use CloudFlare:
# - Configure DNS
# - Enable caching rules
# - Set up SSL certificates
```

## 🚨 Troubleshooting

### Common Issues

1. **Environment Variables Not Loading**
   ```bash
   # Check variable names (case sensitive)
   # Ensure no extra spaces
   # Restart services after changes
   ```

2. **CORS Errors**
   ```python
   # Update allowed origins
   # Check request methods
   # Verify credentials settings
   ```

3. **Database Connection Issues**
   ```bash
   # Check connection string format
   # Verify firewall settings
   # Test connection manually
   ```

4. **API Rate Limits**
   ```bash
   # Check API quotas
   # Implement caching
   # Add retry logic with exponential backoff
   ```

## 📝 Post-Deployment Tasks

### 1. Testing
- [ ] Smoke tests on all major features
- [ ] Performance testing under load
- [ ] Security scanning
- [ ] Mobile responsiveness check

### 2. Documentation
- [ ] Update API documentation
- [ ] Create user guides
- [ ] Document deployment process
- [ ] Update monitoring runbooks

### 3. Monitoring Setup
- [ ] Configure alerts
- [ ] Set up log aggregation
- [ ] Create dashboards
- [ ] Test backup/restore procedures

---

**Remember**: Always test deployments in a staging environment first! 🛡️ 