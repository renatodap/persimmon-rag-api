# 🚀 Deployment Checklist - Persimmon RAG API

**Use this checklist to ensure a smooth deployment to Railway (or any platform).**

---

## ✅ Phase 1: Pre-Deployment Preparation

### 1.1 Code & Dependencies
- [ ] **Poetry configuration is valid**
  ```bash
  poetry check
  ```
- [ ] **All dependencies are installed**
  ```bash
  poetry install
  ```
- [ ] **Code passes linting**
  ```bash
  poetry run ruff check app tests
  poetry run black app tests --check
  ```
- [ ] **Type checking passes**
  ```bash
  poetry run mypy app
  ```

### 1.2 Tests & Quality
- [ ] **All tests pass**
  ```bash
  poetry run pytest
  ```
- [ ] **Test coverage is ≥80%**
  ```bash
  poetry run pytest --cov=app --cov-report=term-missing
  ```
- [ ] **No critical security issues**
  ```bash
  # Review code for hardcoded secrets, SQL injection, etc.
  ```

### 1.3 Environment Variables
- [ ] **Validate environment variables**
  ```bash
  poetry run python scripts/validate_env.py
  ```
- [ ] **All required variables are documented in .env.example**
- [ ] **Secrets are generated (JWT_SECRET, WEBHOOK_SECRET)**
  - Minimum 32 characters
  - Use strong random strings
  - **DO NOT use default values in production!**

### 1.4 Database Setup
- [ ] **Supabase project created**
  - Account: [supabase.com](https://supabase.com)
  - Project name: `persimmon-rag-api` or similar

- [ ] **pgvector extension enabled**
  ```sql
  -- In Supabase SQL Editor:
  CREATE EXTENSION IF NOT EXISTS vector;
  ```

- [ ] **Database schema created**
  ```bash
  # Run migration in Supabase SQL Editor:
  # Copy contents of migrations/000_initial_schema.sql
  ```

- [ ] **Verify tables exist**
  - sources
  - summaries
  - collections
  - collection_sources
  - tags
  - webhooks

- [ ] **Verify RLS policies are enabled**
  ```sql
  -- Check RLS status:
  SELECT tablename, rowsecurity
  FROM pg_tables
  WHERE schemaname = 'public'
  AND tablename IN ('sources', 'summaries', 'collections', 'tags', 'webhooks');
  ```

- [ ] **Test vector search function**
  ```sql
  -- Should not error:
  SELECT * FROM match_summaries(
    query_embedding := array_fill(0, ARRAY[768])::vector(768),
    match_threshold := 0.5,
    match_count := 5
  );
  ```

### 1.5 API Keys & Credentials
- [ ] **Supabase credentials ready**
  - `SUPABASE_URL` (from project settings)
  - `SUPABASE_KEY` (anon/public key)
  - `SUPABASE_SERVICE_KEY` (service_role key - keep secret!)

- [ ] **Anthropic API key obtained**
  - Sign up: [console.anthropic.com](https://console.anthropic.com)
  - Create API key
  - Format: `sk-ant-...`

- [ ] **Google Gemini API key obtained**
  - Sign up: [ai.google.dev](https://ai.google.dev)
  - Create API key
  - **FREE tier: 1500 requests/day**

- [ ] **OpenAI API key obtained**
  - Sign up: [platform.openai.com](https://platform.openai.com)
  - Create API key
  - Format: `sk-...`

### 1.6 Local Testing
- [ ] **Local server runs without errors**
  ```bash
  poetry run uvicorn app.main:app --reload
  ```

- [ ] **Health check returns 200**
  ```bash
  curl http://localhost:8000/health
  # Expected: {"status": "healthy", "environment": "development"}
  ```

- [ ] **API docs are accessible**
  - Swagger UI: http://localhost:8000/docs
  - ReDoc: http://localhost:8000/redoc

- [ ] **Test authentication flow**
  - Create test user in Supabase
  - Get JWT token
  - Test protected endpoints

- [ ] **Test core features**
  - Create a source
  - Generate summary
  - Create embedding
  - Search sources
  - Create collection

---

## 🚂 Phase 2: Railway Deployment

### 2.1 Railway Setup
- [ ] **Railway CLI installed**
  ```bash
  npm install -g @railway/cli
  # Verify:
  railway --version
  ```

- [ ] **Logged into Railway**
  ```bash
  railway login
  ```

- [ ] **Railway project initialized**
  ```bash
  railway init
  # Project name: persimmon-rag-api
  ```

### 2.2 Redis Setup
- [ ] **Redis addon added**
  ```bash
  railway add
  # Select: Redis
  ```

- [ ] **REDIS_URL is auto-configured**
  ```bash
  railway variables
  # Should show: REDIS_URL=redis://...
  ```

### 2.3 Environment Variables Configuration
- [ ] **All production variables set in Railway dashboard**
  ```
  ✓ SUPABASE_URL
  ✓ SUPABASE_KEY
  ✓ SUPABASE_SERVICE_KEY
  ✓ ANTHROPIC_API_KEY
  ✓ GOOGLE_GEMINI_API_KEY
  ✓ OPENAI_API_KEY
  ✓ JWT_SECRET (32+ chars, NOT default!)
  ✓ WEBHOOK_SECRET (32+ chars, NOT default!)
  ✓ ENVIRONMENT=production
  ✓ LOG_LEVEL=INFO
  ✓ ALLOWED_ORIGINS=https://your-frontend-domain.com
  ✓ REDIS_URL (auto-set by Railway)
  ```

- [ ] **Verify no variables contain default values**
  - JWT_SECRET ≠ "your_jwt_secret_key_minimum_32_characters"
  - WEBHOOK_SECRET ≠ "default-webhook-secret-change-in-production"

### 2.4 Deploy to Railway
- [ ] **Deploy the application**
  ```bash
  railway up
  ```

- [ ] **Deployment succeeds without errors**
  ```bash
  railway logs
  # Look for: "starting_application"
  ```

- [ ] **Get deployment URL**
  ```bash
  railway open
  # Note the URL: https://your-app.railway.app
  ```

---

## ✅ Phase 3: Post-Deployment Verification

### 3.1 Health Checks
- [ ] **Production health check returns 200**
  ```bash
  curl https://your-app.railway.app/health
  # Expected: {"status": "healthy", "environment": "production"}
  ```

- [ ] **API docs are accessible**
  - https://your-app.railway.app/docs
  - https://your-app.railway.app/redoc

### 3.2 Functionality Tests
- [ ] **Authentication works**
  - Get JWT token from Supabase
  - Test with Authorization header

- [ ] **Create source**
  ```bash
  curl -X POST https://your-app.railway.app/api/v1/sources \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"title": "Test", "content_type": "text", "original_content": "Test content", "summary_text": "Test summary", "key_actions": [], "key_topics": ["test"], "word_count": 2}'
  ```

- [ ] **Search works**
  ```bash
  curl -X POST https://your-app.railway.app/api/v1/search \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"query": "test", "mode": "hybrid", "limit": 5}'
  ```

- [ ] **Embeddings generation works**
  ```bash
  curl -X POST https://your-app.railway.app/api/v1/embeddings/generate \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"text": "test query", "type": "query"}'
  ```

- [ ] **Batch operations work**
  - Test batch embeddings (up to 100)
  - Test batch source creation (up to 50)

- [ ] **Webhooks work**
  - Register a webhook
  - Create a source
  - Verify webhook delivery

### 3.3 Performance & Monitoring
- [ ] **Response times are acceptable**
  - Non-AI endpoints: < 500ms
  - AI endpoints: < 5s (depending on provider)

- [ ] **Rate limiting works**
  - Test exceeding rate limits
  - Verify 429 responses

- [ ] **Error handling works**
  - Test invalid requests
  - Verify structured error responses
  - No internal errors leaked

- [ ] **Logs are structured and readable**
  ```bash
  railway logs
  # Should see JSON logs with context
  ```

### 3.4 Database Verification
- [ ] **RLS policies are enforced**
  - Users can only access their own data
  - Test with different user tokens

- [ ] **Vector search performs well**
  - Test semantic search
  - Check similarity scores
  - Verify relevance

- [ ] **Indexes are being used**
  ```sql
  -- In Supabase SQL Editor:
  EXPLAIN ANALYZE SELECT * FROM sources WHERE user_id = 'xxx';
  -- Should show index scan, not seq scan
  ```

---

## 🔒 Phase 4: Security & Compliance

### 4.1 Security Checks
- [ ] **JWT tokens are properly validated**
- [ ] **RLS policies prevent unauthorized access**
- [ ] **API keys are not exposed in logs**
- [ ] **CORS is properly configured**
  - Only allow trusted origins in production
  - No `*` wildcard in ALLOWED_ORIGINS

- [ ] **HTTPS is enforced**
  - Railway handles this automatically
  - Verify no HTTP endpoints

- [ ] **Rate limiting is active**
  - Prevents abuse
  - Per-user limits enforced

- [ ] **Input validation works**
  - Pydantic validates all inputs
  - SQL injection prevention

### 4.2 Secrets Management
- [ ] **No secrets in version control**
  ```bash
  git log --all -p | grep -i "api_key"
  # Should return nothing
  ```

- [ ] **Secrets are rotated periodically**
  - JWT_SECRET rotation plan
  - API keys rotation schedule

- [ ] **Backup credentials stored securely**
  - Use password manager
  - Document recovery process

---

## 📊 Phase 5: Monitoring & Maintenance

### 5.1 Monitoring Setup
- [ ] **Railway metrics are monitored**
  - CPU usage
  - Memory usage
  - Request count
  - Error rate

- [ ] **Uptime monitoring configured**
  - UptimeRobot or similar
  - Health check: /health
  - Alert on downtime

- [ ] **Error tracking configured (optional)**
  - Sentry DSN set
  - Error notifications enabled

### 5.2 Cost Monitoring
- [ ] **Railway costs are tracked**
  - Hobby plan: $5/month
  - Pro plan: Usage-based

- [ ] **AI API costs are monitored**
  - Gemini: FREE tier usage
  - OpenAI: Token usage
  - Claude: Summary generation costs

- [ ] **Budget alerts set**
  - Alert at 80% of budget
  - Alert at 100% of budget

### 5.3 Documentation
- [ ] **Deployment documented**
  - Railway URL recorded
  - Environment variables documented
  - Database credentials stored securely

- [ ] **Frontend configured**
  - If using notebook-recall frontend:
    - Update `NEXT_PUBLIC_API_URL`
    - Test end-to-end flow

- [ ] **Team access configured**
  - Railway project shared (if needed)
  - Supabase project access
  - API documentation shared

---

## 🎯 Phase 6: Final Verification

### 6.1 End-to-End Testing
- [ ] **Complete RAG workflow works**
  1. Create source with AI summary
  2. Generate embeddings
  3. Perform semantic search
  4. Use results in RAG context
  5. Test with actual AI agent

- [ ] **All features tested**
  - ✓ Sources CRUD
  - ✓ Collections
  - ✓ Search (semantic, keyword, hybrid)
  - ✓ Embeddings (single & batch)
  - ✓ Webhooks
  - ✓ Authentication
  - ✓ Rate limiting

### 6.2 Performance Baseline
- [ ] **Load testing performed**
  ```bash
  # Use tool like Apache Bench or k6
  ab -n 100 -c 10 https://your-app.railway.app/health
  ```

- [ ] **Performance metrics recorded**
  - Average response time
  - P95 response time
  - Throughput (requests/sec)

### 6.3 Rollback Plan
- [ ] **Rollback procedure documented**
  - Railway allows deployment rollback
  - Database backup procedure
  - Environment variables backup

- [ ] **Test rollback process**
  - Deploy new version
  - Rollback to previous
  - Verify functionality

---

## 🎉 Deployment Complete!

**Once all items are checked:**
- ✅ Application is production-ready
- ✅ All features are working
- ✅ Security is properly configured
- ✅ Monitoring is in place
- ✅ Team is notified

**Next Steps:**
1. Share API URL with frontend team
2. Update documentation with production URL
3. Monitor logs for first 24 hours
4. Gather user feedback
5. Plan for scaling if needed

---

## 📞 Support Resources

**Railway:**
- Dashboard: https://railway.app/dashboard
- Docs: https://docs.railway.app
- Discord: https://discord.gg/railway

**Supabase:**
- Dashboard: https://app.supabase.com
- Docs: https://supabase.com/docs
- Discord: https://discord.supabase.com

**API Documentation:**
- Swagger UI: https://your-app.railway.app/docs
- Agent Guide: docs/AGENT_API_GUIDE.md

---

**Remember:** A successful deployment is one you can sleep soundly after! 😴✨
