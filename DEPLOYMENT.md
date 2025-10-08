# Deployment Guide - Railway

Complete guide to deploying Recall Notebook backend to Railway.

## Prerequisites

1. Railway account (https://railway.app)
2. Railway CLI installed: `npm install -g @railway/cli`
3. All environment variables ready
4. Supabase project configured
5. Redis instance (Railway provides free Redis addon)

## Step-by-Step Deployment

### 1. Install Railway CLI

```bash
npm install -g @railway/cli
```

### 2. Login to Railway

```bash
railway login
```

### 3. Create New Railway Project

```bash
cd backend
railway init
```

Select "Create new project" and give it a name (e.g., "recall-notebook-backend").

### 4. Add Redis Addon

```bash
railway add
```

Select "Redis" from the list. Railway will automatically provision a Redis instance and set the `REDIS_URL` environment variable.

### 5. Set Environment Variables

In Railway dashboard or via CLI:

```bash
# Required environment variables
railway variables set SUPABASE_URL=your_supabase_url
railway variables set SUPABASE_KEY=your_supabase_anon_key
railway variables set SUPABASE_SERVICE_KEY=your_service_key
railway variables set ANTHROPIC_API_KEY=your_anthropic_key
railway variables set GOOGLE_GEMINI_API_KEY=your_gemini_key
railway variables set OPENAI_API_KEY=your_openai_key
railway variables set JWT_SECRET=your_jwt_secret_32chars_minimum
railway variables set ENVIRONMENT=production
railway variables set LOG_LEVEL=INFO
railway variables set ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
```

**Important**: Railway automatically sets `PORT` and `REDIS_URL`, so you don't need to set these manually.

### 6. Deploy to Railway

```bash
railway up
```

Railway will:
1. Detect Python project
2. Install dependencies from `pyproject.toml`
3. Build the application
4. Start the server using `Procfile`

### 7. Verify Deployment

Check the deployment logs:

```bash
railway logs
```

Visit your app:

```bash
railway open
```

Test the health endpoint:

```bash
curl https://your-app.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "environment": "production"
}
```

### 8. View API Documentation

Visit: `https://your-app.railway.app/docs`

This opens the interactive Swagger UI where you can test all endpoints.

## Update Frontend to Use Railway Backend

In your Next.js frontend `.env.local`:

```bash
NEXT_PUBLIC_API_URL=https://your-app.railway.app
```

Update API calls in frontend to use this URL instead of `/api`.

## Monitoring & Maintenance

### View Logs

```bash
railway logs
```

### Check Metrics

Visit Railway dashboard → Metrics to see:
- CPU usage
- Memory usage
- Request count
- Response times

### Update Environment Variables

```bash
railway variables set VARIABLE_NAME=new_value
```

### Redeploy

```bash
railway up
```

### Rollback

In Railway dashboard → Deployments → Select previous deployment → Redeploy

## Cost Optimization

### Railway Pricing
- **Hobby Plan**: $5/month
  - 512 MB RAM
  - 1 GB disk
  - Shared CPU
  - Perfect for development/testing

- **Pro Plan**: Usage-based
  - Auto-scaling
  - Better performance
  - Custom domains

### AI API Costs
- **Gemini Embeddings**: FREE (1500/day)
- **OpenAI Embeddings**: $0.02/1M tokens (fallback)
- **Claude Summaries**: $3-15/1M tokens
- **Target**: ~$0.50/user/month

Monitor costs:
- Check Railway metrics
- Review structured logs for AI API usage
- Set up budget alerts

## Troubleshooting

### Build Fails

Check logs for missing dependencies:
```bash
railway logs --build
```

### Runtime Errors

Check application logs:
```bash
railway logs --runtime
```

### Health Check Fails

Verify:
1. `/health` endpoint returns 200
2. PORT environment variable is used
3. Server binds to `0.0.0.0`

### Database Connection Issues

Verify:
1. Supabase URL and keys are correct
2. RLS policies allow service role access
3. pgvector extension is enabled

### Redis Connection Issues

Verify:
1. Redis addon is added to project
2. `REDIS_URL` environment variable is set
3. Check Redis logs in Railway dashboard

## Security Checklist

- [x] JWT_SECRET is at least 32 characters
- [x] All API keys are stored in Railway environment variables
- [x] CORS is configured with specific origins
- [x] Rate limiting is enabled
- [x] Supabase RLS policies are active
- [x] HTTPS is enforced (Railway does this automatically)

## Performance Optimization

### Enable Caching
- Use Redis for rate limiting
- Cache frequently accessed data
- Implement API response caching

### Database Optimization
- Add indexes on frequently queried columns
- Use pgvector HNSW index for embeddings
- Optimize query patterns

### AI API Optimization
- Use Gemini FREE tier for embeddings
- Batch embedding requests
- Implement request deduplication
- Cache AI responses when possible

## Next Steps

1. Set up custom domain (Railway dashboard → Domains)
2. Enable monitoring with Sentry
3. Set up CI/CD with GitHub Actions
4. Configure backup strategy for Supabase
5. Implement health check monitoring (e.g., UptimeRobot)

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Supabase Docs: https://supabase.com/docs
