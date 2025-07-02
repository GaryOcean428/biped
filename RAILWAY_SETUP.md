# Railway Deployment Setup Guide for Biped Platform

## 🚀 Current Status
The Biped platform is ready for deployment with all necessary configuration files in place.

## 📋 Pre-Deployment Checklist

### ✅ Files Already Created
- `railway.toml` - Main deployment configuration
- `backend/Procfile` - Process definition for Railway
- `backend/runtime.txt` - Python version specification
- `backend/requirements.txt` - Python dependencies with gunicorn
- `DEPLOYMENT.md` - Complete deployment documentation

### 🔧 Railway Project Setup Steps

#### 1. **Connect GitHub Repository**
- Ensure your Railway project is connected to the GitHub repository
- Railway will automatically detect the `railway.toml` configuration
- The platform will use Nixpacks builder as specified in the config

#### 2. **Add PostgreSQL Database Service**
- Add a PostgreSQL service to your Railway project
- Railway will automatically provide `DATABASE_URL` environment variable
- The database will be accessible via `${{Postgres.DATABASE_URL}}`

#### 3. **Configure Environment Variables**
Based on Railway documentation, you need to set these variables in your Railway project dashboard:

**Core Application Variables:**
```
SECRET_KEY=your-production-secret-key-here
FLASK_ENV=production
FLASK_DEBUG=false
```

**Stripe Payment Variables:**
```
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

**AI API Keys:**
```
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-api03-...
GROQ_API_KEY=gsk_...
PERPLEXITY_API_KEY=pplx-...
XAI_API_KEY=xai-...
GOOGLE_API_KEY=AIzaSy...
GEMINI_API_KEY=AIzaSy...
```

**Search API Keys:**
```
BING_SEARCH_API_KEY=...
SERPER_API_KEY=...
TAVILY_API_KEY=tvly-...
HUGGINGFACE_TOKEN=hf_...
```

**OAuth Configuration:**
```
GITHUB_TOKEN=ghp_...
GITHUB_CLIENT_ID=Ov23li...
GOOGLE_CLIENT_ID=425089133667-...
GOOGLE_CLIENT_SECRET=GOCSPX-...
```

#### 4. **Important Railway Configuration Notes**

**From Railway Documentation:**
- Variables create "staged changes" that must be deployed
- Use the "Seal" feature for sensitive variables (they become write-only)
- Railway provides auto-complete for variable references
- Configuration in `railway.toml` overrides dashboard settings

**Build Configuration:**
- Railway will use Nixpacks builder
- Build command: `cd backend && pip install -r requirements.txt`
- Start command: `cd backend && python -m gunicorn --bind 0.0.0.0:$PORT src.main:app`

**Health Check:**
- Path: `/api/health`
- Timeout: 300 seconds
- Railway will monitor this endpoint

#### 5. **Deployment Process**

1. **Push to GitHub** (Already Done ✅)
   - All code is committed and pushed to main branch
   - Railway will detect changes automatically

2. **Set Environment Variables**
   - Go to your Railway project dashboard
   - Navigate to Variables tab
   - Add all required environment variables
   - Consider sealing sensitive variables for security

3. **Deploy**
   - Railway will automatically deploy when variables are set
   - Monitor deployment logs for any issues
   - Check health endpoint once deployed

4. **Generate Public Domain**
   - Go to Settings → Networking
   - Click "Generate Domain" for public access
   - Custom domain can be configured later

#### 6. **Post-Deployment Verification**

**Check These Endpoints:**
- `https://your-domain.railway.app/` - Main homepage
- `https://your-domain.railway.app/api/health` - Health check
- `https://your-domain.railway.app/admin.html` - Admin dashboard
- `https://your-domain.railway.app/mobile.html` - Mobile PWA

**Verify Features:**
- Admin login (username: admin, password: admin123)
- API endpoints responding correctly
- Database connectivity
- Static file serving

#### 7. **Common Railway Pitfalls to Avoid**

**Based on Railway Documentation:**
- Don't hardcode secrets in code (use environment variables)
- Ensure your app binds to `0.0.0.0:$PORT` (already configured)
- Use gunicorn for production (already configured)
- Set proper health check endpoint (already configured)
- Monitor deployment logs for build/runtime errors

**Environment Variable Best Practices:**
- Use Railway's "Seal" feature for production secrets
- Reference shared variables with `${{shared.VARIABLE_NAME}}`
- Use staged changes workflow for variable updates
- Test with `railway run` locally before deploying

#### 8. **Monitoring and Maintenance**

**Railway Provides:**
- Automatic scaling (configured: 1-10 replicas)
- Health monitoring (configured: 30s intervals)
- Deployment logs and metrics
- Automatic restarts on failure

**Custom Monitoring:**
- `/api/analytics/metrics/current` - Platform metrics
- `/api/analytics/platform-health` - Health scoring
- Built-in logging and error tracking

## 🔄 Next Steps

1. **Set Environment Variables** in Railway dashboard
2. **Monitor Deployment** logs for successful startup
3. **Test All Features** using the verification checklist
4. **Configure Custom Domain** if needed
5. **Set up Monitoring** and alerts

## 🆘 Troubleshooting

**If Deployment Fails:**
1. Check Railway deployment logs
2. Verify all environment variables are set
3. Ensure PostgreSQL service is running
4. Check health endpoint response
5. Review `railway.toml` configuration

**Common Issues:**
- Missing environment variables
- Database connection errors
- Port binding issues (should use Railway's $PORT)
- Health check failures

The platform is fully configured and ready for Railway deployment! 🚀

