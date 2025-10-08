# 🚂 Railway Deployment Guide - Persimmon RAG API

**Complete step-by-step guide to deploy Persimmon RAG API to Railway.**

This guide assumes you're starting from scratch. Follow each step carefully.

---

## 📋 Prerequisites

Before starting, ensure you have:

- [x] **Railway account** - [Sign up here](https://railway.app)
- [x] **Supabase account** - [Sign up here](https://supabase.com)
- [x] **API keys** ready:
  - Anthropic (Claude)
  - Google Gemini
  - OpenAI
- [x] **Node.js** installed (for Railway CLI)
- [x] **Git** installed and repository cloned

---

## 🗄️ Phase 1: Supabase Database Setup

### Step 1.1: Create Supabase Project

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Click **"New Project"**
3. Fill in details:
   - **Name:** `persimmon-rag-api` (or your choice)
   - **Database Password:** Generate strong password (save it!)
   - **Region:** Choose closest to your users
4. Click **"Create new project"**
5. Wait 2-3 minutes for provisioning

### Step 1.2: Enable pgvector Extension

1. In Supabase project, go to **SQL Editor**
2. Click **"New Query"**
3. Run this command:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

4. Click **"Run"** (should see "Success" message)

### Step 1.3: Run Database Migration

1. Open `migrations/000_initial_schema.sql` in this repository
2. Copy the entire SQL content
3. In Supabase SQL Editor, click **"New Query"**
4. Paste the SQL content
5. Click **"Run"** (takes ~10 seconds)
6. Verify success message appears

### Step 1.4: Verify Database Setup

Run this query in SQL Editor to verify tables:

```sql
SELECT
    tablename,
    rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('sources', 'summaries', 'collections', 'tags', 'webhooks')
ORDER BY tablename;
```

Expected result: 5 tables with `rowsecurity = true`

### Step 1.5: Get Supabase Credentials

1. In Supabase project, go to **Settings** → **API**
2. Copy these values (you'll need them for Railway):
   - **Project URL** → `SUPABASE_URL`
   - **anon public** key → `SUPABASE_KEY`
   - **service_role** key → `SUPABASE_SERVICE_KEY` ⚠️ Keep secret!

---

## 🔑 Phase 2: Get API Keys

### Step 2.1: Anthropic (Claude)

1. Go to [Anthropic Console](https://console.anthropic.com)
2. Sign up or log in
3. Click **"API Keys"**
4. Click **"Create Key"**
5. Copy the key (format: `sk-ant-...`)

**Cost:** $3-15 per 1M tokens (used for summaries)

### Step 2.2: Google Gemini

1. Go to [Google AI Studio](https://ai.google.dev)
2. Sign in with Google account
3. Click **"Get API Key"**
4. Create new API key
5. Copy the key

**Cost:** FREE! (1500 requests/day)

### Step 2.3: OpenAI

1. Go to [OpenAI Platform](https://platform.openai.com)
2. Sign up or log in
3. Click **"API Keys"** in sidebar
4. Click **"Create new secret key"**
5. Copy the key (format: `sk-...`)

**Cost:** $0.02 per 1M tokens (fallback embeddings only)

### Step 2.4: Generate Secrets

Run these commands to generate secure secrets:

**On macOS/Linux:**
```bash
# JWT Secret
openssl rand -base64 48

# Webhook Secret
openssl rand -base64 48
```

**On Windows (PowerShell):**
```powershell
# JWT Secret
[Convert]::ToBase64String((1..48 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))

# Webhook Secret
[Convert]::ToBase64String((1..48 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))
```

**Or use Python:**
```bash
poetry run python -c "import secrets; print('JWT_SECRET:', secrets.token_urlsafe(48)); print('WEBHOOK_SECRET:', secrets.token_urlsafe(48))"
```

**Save these secrets!** You'll need them for Railway.

---

## 🚂 Phase 3: Railway Setup & Deployment

### Step 3.1: Install Railway CLI

**Using npm:**
```bash
npm install -g @railway/cli
```

**Verify installation:**
```bash
railway --version
```

Expected output: `Railway CLI vX.X.X`

### Step 3.2: Login to Railway

```bash
railway login
```

This opens browser for authentication. Click **"Authorize"**.

### Step 3.3: Initialize Railway Project

**Navigate to project directory:**
```bash
cd persimmon-rag-api
```

**Initialize Railway project:**
```bash
railway init
```

You'll be prompted:
- **"Create a new project or link to existing?"** → Select **"Create new project"**
- **"What would you like to name your project?"** → Enter: `persimmon-rag-api`
- **"Which environment?"** → Select **"production"**

### Step 3.4: Add Redis Service

Redis is required for rate limiting.

```bash
railway add
```

- Select **"Redis"**
- Wait for provisioning (~30 seconds)

Redis will automatically set `REDIS_URL` environment variable.

### Step 3.5: Set Environment Variables

**Option A: Using Railway Dashboard (Recommended)**

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Select your project `persimmon-rag-api`
3. Click on your service (not Redis)
4. Click **"Variables"** tab
5. Click **"+ New Variable"** for each:

```bash
# Supabase (from Step 1.5)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# AI APIs (from Step 2.1-2.3)
ANTHROPIC_API_KEY=sk-ant-api03-...
GOOGLE_GEMINI_API_KEY=AIzaSyD...
OPENAI_API_KEY=sk-proj-...

# Security (from Step 2.4)
JWT_SECRET=<your-generated-secret-48-chars>
WEBHOOK_SECRET=<your-generated-secret-48-chars>

# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
ALLOWED_ORIGINS=https://your-frontend-domain.com

# Redis (should already be set by Railway)
REDIS_URL=redis://default:...@redis.railway.internal:6379
```

**Option B: Using Railway CLI**

```bash
# Supabase
railway variables set SUPABASE_URL="https://xxxxx.supabase.co"
railway variables set SUPABASE_KEY="your-key"
railway variables set SUPABASE_SERVICE_KEY="your-service-key"

# AI APIs
railway variables set ANTHROPIC_API_KEY="sk-ant-..."
railway variables set GOOGLE_GEMINI_API_KEY="AIzaSyD..."
railway variables set OPENAI_API_KEY="sk-proj-..."

# Security
railway variables set JWT_SECRET="your-generated-secret"
railway variables set WEBHOOK_SECRET="your-generated-secret"

# Application
railway variables set ENVIRONMENT="production"
railway variables set LOG_LEVEL="INFO"
railway variables set ALLOWED_ORIGINS="https://your-frontend-domain.com"
```

**Verify variables are set:**
```bash
railway variables
```

### Step 3.6: Deploy to Railway

**Deploy the application:**
```bash
railway up
```

This will:
1. Upload your code to Railway
2. Build Docker container
3. Install dependencies (via Poetry)
4. Start the application
5. Assign a public URL

**Watch deployment logs:**
```bash
railway logs
```

Look for:
```
starting_application environment=production port=XXXX
```

**Deployment takes 2-5 minutes.**

### Step 3.7: Get Your Deployment URL

**Option 1: CLI**
```bash
railway open
```

This opens your deployed API in browser.

**Option 2: Dashboard**
1. Go to Railway Dashboard
2. Click on your service
3. Click **"Settings"**
4. See **"Domains"** section
5. Copy the Railway-provided URL: `https://persimmon-rag-api-production.up.railway.app`

**Save this URL!** You'll need it for API testing and frontend configuration.

---

## ✅ Phase 4: Verify Deployment

### Step 4.1: Test Health Endpoint

```bash
curl https://your-app.railway.app/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "environment": "production"
}
```

If you get an error:
- Check Railway logs: `railway logs`
- Verify environment variables are set
- Check database connection

### Step 4.2: Test API Documentation

Open in browser:
```
https://your-app.railway.app/docs
```

You should see Swagger UI with all API endpoints.

### Step 4.3: Test Authentication Flow

**Get a JWT token from Supabase:**

1. Go to Supabase Dashboard → Authentication → Users
2. Create a test user (or use existing)
3. Use Supabase Auth API to get JWT token:

```bash
curl -X POST 'https://YOUR_SUPABASE_URL/auth/v1/token?grant_type=password' \
  -H "apikey: YOUR_SUPABASE_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "your-password"
  }'
```

Save the `access_token` from response.

### Step 4.4: Test API Endpoints

**Create a source:**
```bash
export TOKEN="your-jwt-token-here"
export API_URL="https://your-app.railway.app"

curl -X POST "$API_URL/api/v1/sources" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Article",
    "content_type": "text",
    "original_content": "This is a test article about machine learning and AI.",
    "summary_text": "Test article about ML and AI",
    "key_actions": ["Learn ML", "Explore AI"],
    "key_topics": ["machine learning", "artificial intelligence"],
    "word_count": 10
  }'
```

**Expected:** 201 response with created source

**Search sources:**
```bash
curl -X POST "$API_URL/api/v1/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning",
    "mode": "hybrid",
    "limit": 5
  }'
```

**Expected:** 200 response with search results

**Generate embedding:**
```bash
curl -X POST "$API_URL/api/v1/embeddings/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "test query about AI",
    "type": "query"
  }'
```

**Expected:** 200 response with embedding vector

### Step 4.5: Monitor Logs

```bash
railway logs --follow
```

Watch for:
- ✅ No errors
- ✅ Successful API calls
- ✅ Structured JSON logs
- ✅ "embedding_success" with provider="gemini" (FREE!)

---

## 🔧 Phase 5: Configuration & Optimization

### Step 5.1: Configure Custom Domain (Optional)

1. Railway Dashboard → Your Service → Settings → Domains
2. Click **"Custom Domain"**
3. Enter your domain (e.g., `api.yourdomain.com`)
4. Add CNAME record to your DNS:
   - **Name:** `api`
   - **Value:** `your-app.railway.app`
5. Wait for DNS propagation (5-60 minutes)
6. Update `ALLOWED_ORIGINS` to include your custom domain

### Step 5.2: Set Up Monitoring

**UptimeRobot (Free):**
1. Sign up at [UptimeRobot](https://uptimerobot.com)
2. Add monitor:
   - **Type:** HTTPS
   - **URL:** `https://your-app.railway.app/health`
   - **Interval:** 5 minutes
3. Configure alerts (email, SMS, Slack)

**Railway Metrics:**
1. Railway Dashboard → Your Service → Metrics
2. Monitor:
   - CPU usage
   - Memory usage
   - Request count
   - Error rate

### Step 5.3: Enable Error Tracking (Optional)

**Sentry:**
1. Sign up at [Sentry.io](https://sentry.io)
2. Create new project (Python)
3. Get DSN
4. Set Railway variable:
   ```bash
   railway variables set SENTRY_DSN="your-sentry-dsn"
   ```
5. Redeploy:
   ```bash
   railway up
   ```

### Step 5.4: Configure CORS for Frontend

Update `ALLOWED_ORIGINS` to include your frontend domain:

```bash
railway variables set ALLOWED_ORIGINS="https://your-frontend.com,https://app.your-frontend.com"
```

Or use comma-separated list in Railway Dashboard.

---

## 📊 Phase 6: Cost Optimization

### Current Costs

**Infrastructure:**
- Railway Hobby Plan: $5/month
  - 512 MB RAM
  - 1 GB Disk
  - Shared CPU
- Railway Redis: Included in Hobby Plan

**AI APIs (per user/month):**
- Google Gemini: $0.00 (FREE - 1500/day)
- OpenAI (fallback): ~$0.01-0.02
- Anthropic Claude: ~$0.10-0.30
- **Target: $0.50/user/month**

### Cost Monitoring

**Railway:**
```bash
railway status
# Shows usage and billing info
```

**AI APIs:**
- Monitor structured logs for API usage
- Check provider dashboards monthly
- Set up billing alerts

### Optimization Tips

1. **Use Gemini for embeddings** (FREE!)
   - Primary provider in code
   - OpenAI only as fallback

2. **Cache AI responses**
   - Avoid re-generating same summaries
   - Store embeddings in database

3. **Batch operations**
   - Use `/embeddings/batch` for multiple texts
   - Reduces API overhead

4. **Rate limiting**
   - Already configured per user
   - Prevents abuse and cost spikes

---

## 🚨 Troubleshooting

### Issue: Deployment Fails

**Check logs:**
```bash
railway logs
```

**Common causes:**
- Missing environment variables
- Invalid API keys
- Poetry dependency conflicts

**Solution:**
1. Verify all variables are set: `railway variables`
2. Check pyproject.toml is valid: `poetry check`
3. Redeploy: `railway up`

### Issue: Health Check Fails

**Test locally first:**
```bash
poetry run uvicorn app.main:app --reload
curl http://localhost:8000/health
```

**If local works but Railway fails:**
- Check PORT is not hardcoded (Railway sets it dynamically)
- Verify HOST is `0.0.0.0` in config
- Check Railway logs for startup errors

### Issue: Database Connection Fails

**Verify Supabase credentials:**
```bash
# Test connection
curl "https://YOUR_SUPABASE_URL/rest/v1/" \
  -H "apikey: YOUR_SUPABASE_KEY"
```

**Expected:** 200 response with API info

**Common issues:**
- Wrong SUPABASE_URL (should include https://)
- Swapped SUPABASE_KEY and SUPABASE_SERVICE_KEY
- RLS policies blocking service role

### Issue: Redis Connection Fails

**Verify Redis addon is running:**
```bash
railway status
```

Should show Redis service active.

**Check REDIS_URL format:**
- Should be: `redis://default:password@host:6379`
- Railway sets this automatically

**Solution:**
1. Remove and re-add Redis: `railway add`
2. Redeploy: `railway up`

### Issue: Rate Limiting Not Working

**Check Redis connection:**
- Review logs for "rate_limit_error"
- Verify REDIS_URL is set

**Rate limiter fails open:**
- If Redis is down, requests still work
- But no rate limiting is enforced

### Issue: API Keys Invalid

**Test each API key:**

**Anthropic:**
```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 10,
    "messages": [{"role": "user", "content": "Hi"}]
  }'
```

**Google Gemini:**
```bash
curl "https://generativelanguage.googleapis.com/v1/models?key=$GOOGLE_GEMINI_API_KEY"
```

**OpenAI:**
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

If any fail, regenerate keys from provider dashboards.

---

## 🔄 Updating Your Deployment

### Deploy New Version

**Commit changes:**
```bash
git add .
git commit -m "feat: add new feature"
```

**Deploy to Railway:**
```bash
railway up
```

Railway automatically redeploys on push.

### Rollback Deployment

**Via Railway Dashboard:**
1. Go to Deployments tab
2. Find previous successful deployment
3. Click "Redeploy"

**Via CLI:**
```bash
railway status
# Note deployment ID of working version

railway redeploy <deployment-id>
```

---

## 📝 Post-Deployment Checklist

- [ ] Health check returns 200
- [ ] API docs are accessible
- [ ] Authentication works
- [ ] All endpoints tested
- [ ] Monitoring configured
- [ ] Custom domain set up (optional)
- [ ] Frontend updated with API URL
- [ ] Team notified of deployment
- [ ] Documentation updated
- [ ] Backup credentials stored

---

## 🎉 Success!

Your Persimmon RAG API is now live on Railway! 🚀

**Your API URL:** `https://your-app.railway.app`

**Next Steps:**
1. Share API URL with your team
2. Update frontend with `NEXT_PUBLIC_API_URL`
3. Test end-to-end RAG workflow
4. Monitor logs for first 24 hours
5. Set up budget alerts

**Support:**
- Railway Discord: https://discord.gg/railway
- Railway Docs: https://docs.railway.app
- API Docs: https://your-app.railway.app/docs

**Remember:** You can always check logs with `railway logs` and redeploy with `railway up`.

Happy deploying! 🚂✨
