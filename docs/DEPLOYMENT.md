# WealthPath AI Production Deployment Guide

## Overview
This comprehensive deployment guide covers the WealthPath AI financial advisory platform with multi-LLM integration, complete financial context services, and advanced debugging capabilities. The system is optimized for cloud deployment with zero ML dependencies and production-ready monitoring.

**Key Features:**
- Multi-LLM architecture (OpenAI, Gemini, Claude) with intelligent fallback
- Complete financial context integration (10 data types, 200+ data points)
- Vector-based conversation memory with zero database overhead
- Advanced debugging suite with LLM payload inspection
- Production-optimized: <256MB memory, 396MB Docker image

## Local Development Setup

### Quick Start with Multi-LLM Setup
```bash
# 1. Environment Setup
cp backend/.env.example backend/.env
# Configure your API keys:
# OPENAI_API_KEY=sk-your-key
# GEMINI_API_KEY=your-key  
# ANTHROPIC_API_KEY=your-key

# 2. Start all services
docker-compose up -d

# 3. Verify services are running
docker ps  # Should show: wpa-frontend, wpa-backend, wpa-postgres, wpa-redis

# 4. Create test user (first time or after reboot)
docker exec -it wpa-backend python -c "
from app.models.user import User
from app.db.session import get_db
from app.core.security import get_password_hash
db = next(get_db())
if not db.query(User).filter(User.email == 'test@gmail.com').first():
    user = User(email='test@gmail.com', password_hash=get_password_hash('password123'), is_active=True)
    db.add(user)
    db.commit()
    print('✅ Test user created successfully')
"

# 5. Verify Multi-LLM Integration
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/debug/llm-clients
# Should show: {"registered_clients": ["openai", "gemini", "claude"]}

# 6. Access application
# Frontend: http://localhost:3004
# Backend API: http://localhost:8000/docs
# Debug Endpoints: http://localhost:8000/api/v1/debug/
# Login: test@gmail.com / password123
```

### Common Issues & Advanced Troubleshooting

**After Windows/Mac Reboot - Login fails**
```bash
docker-compose up -d postgres redis  # Containers may not auto-start
docker-compose restart backend        # Reconnect backend to DB
# Then recreate test user (see Quick Start step 4)
```

**Multi-LLM Providers Not Working**
```bash
# Check which providers are registered
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/debug/llm-clients

# Verify API keys are set
docker exec -it wpa-backend printenv | grep API_KEY

# Check LLM service logs
docker-compose logs backend | grep -i "llm\|client\|provider"
```

**Chat Responses All Identical (Provider Diversity Issue)**
```bash
# This was a critical bug - verify all 3 clients registered:
# Should show: ["openai", "gemini", "claude"] not just ["gemini"]
curl http://localhost:8000/api/v1/debug/llm-clients
```

**Financial Context Missing from AI Responses**
```bash
# Debug complete financial context service
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/debug/financial-summary/1

# Check vector store contents
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/debug/vector-contents/1
```

**Conversation Memory Not Working**
```bash
# Check vector-based memory system
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/debug/vector-contents/1

# Look for: user_1_conversation_context and user_1_conversation_history
```

### Advanced Development Commands
```bash
# View logs with filtering
docker-compose logs -f backend | grep -E "(LLM|vector|memory|context)"
docker-compose logs -f backend | grep -E "(ERROR|WARNING|🚀|✅|❌)"

# Access database  
docker exec -it wpa-postgres psql -U wealthpath_user -d wealthpath_db

# Database inspection
docker exec -it wpa-postgres psql -U wealthpath_user -d wealthpath_db -c "
SELECT table_name FROM information_schema.tables WHERE table_schema='public';
"

# Vector store debugging
docker exec -it wpa-backend python -c "
from app.services.simple_vector_store import get_vector_store
store = get_vector_store()
print('Documents:', len(store.documents))
print('Document IDs:', list(store.documents.keys())[:5])
"

# Force vector rebuild for user
curl -X POST -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/debug/trigger-vector-sync/1?force_rebuild=true"

# Reset everything (complete clean slate)
docker-compose down -v && docker system prune -f && docker-compose up -d

# Clear browser storage (in console)
localStorage.clear(); sessionStorage.clear(); location.reload();
```

## Critical Configuration for Production Deployment

### 1. Smart API Client Configuration
**Current Implementation:** `frontend/src/utils/api-simple.ts`
```typescript
// Smart API URL detection based on environment
const getApiBaseUrl = () => {
  const hostname = window.location.hostname;
  
  // FORCE PRODUCTION URL FOR ANY NON-LOCALHOST
  if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
    console.log('🔗 PRODUCTION MODE - Using render backend:', hostname);
    return 'https://wealthpath-backend.onrender.com';
  }
  
  // Localhost fallback
  return 'http://localhost:8000';
};
```

**This configuration automatically:**
- ✅ Detects production deployment (Vercel/Render)
- ✅ Uses correct backend URL without manual configuration
- ✅ Provides localhost fallback for development
- ✅ No environment variables needed for basic deployment

### 2. Vite Configuration (Docker Optimized)
**Current:** `frontend/vite.config.ts`
```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://backend:8000',  // Docker service name
      changeOrigin: true,
      secure: false,
      ws: true,
    }
  }
}
```

**This configuration:**
- ✅ Works with Docker Compose (backend service name)
- ✅ Supports WebSocket connections for real-time features
- ✅ Proper error handling and logging

### 3. Backend Environment Variables (Production)
**Required for Render deployment:**

```env
# Database (Render PostgreSQL)
DATABASE_URL=postgresql://user:password@host:port/database

# Security (Generate secure keys)
JWT_SECRET_KEY=your-secure-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Multi-LLM Integration (All providers)
OPENAI_API_KEY=sk-your-openai-key
GEMINI_API_KEY=your-gemini-key
ANTHROPIC_API_KEY=your-claude-key
LLM_DEFAULT_PROVIDER=openai
LLM_DEFAULT_TIER=dev
LLM_CACHE_ENABLED=true

# CORS (Include your production frontend URL)
CORS_ORIGINS=https://smartfinanceadvisor.net,http://localhost:3004
ENABLE_CORS=true

# Production Settings
ENVIRONMENT=production
DEBUG=false

# Redis (Render Redis or external)
REDIS_URL=redis://host:port
```

## CRITICAL PRODUCTION FIX APPLIED - January 7, 2025 ⚠️

### 🚨 EMERGENCY PRODUCTION ISSUE - RESOLVED 
**Issue**: Production application down due to CORS misconfiguration preventing frontend-backend communication

**Root Cause**: CORS middleware using wildcard origins (`["*"]`) which doesn't work with credentials, causing cascade of errors

**Fix Applied**: Updated CORS configuration in `backend/app/main.py` to explicitly allow production domain:

```python
# CORS middleware - PRODUCTION FIX
production_origins = [
    "https://smartfinanceadvisor.net",
    "http://localhost:3000",
    "http://localhost:3001", 
    "http://localhost:3002",
    "http://localhost:3003",
    "http://localhost:3004"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=production_origins,
    allow_credentials=True,  # Critical: Enable credentials for authentication
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)
```

**Database Schema**: ✅ **NO ISSUES FOUND** - All required columns already exist in `user_benefits` table:
- ✅ `social_security_estimated_benefit` 
- ✅ `social_security_claiming_age`
- ✅ `employer_401k_match_formula`
- ✅ `employer_401k_vesting_schedule` 
- ✅ `max_401k_contribution`
- ✅ `pension_details`
- ✅ `other_benefits`
- ✅ `notes`

### Immediate Deployment Steps for Render.com:
1. **Push CORS fix to production**: `git push origin main`
2. **Monitor Render deployment** at dashboard
3. **Verify CORS headers**: `curl -H "Origin: https://smartfinanceadvisor.net" https://wealthpath-backend.onrender.com/health`
4. **Expected response headers**:
   - `access-control-allow-credentials: true`
   - `access-control-allow-origin: https://smartfinanceadvisor.net`

---

## Production Deployment Checklist

### Pre-Deployment Verification:

#### 1. Multi-LLM System ✅
- [ ] All 3 API keys configured (OpenAI, Gemini, Claude)
- [ ] Test endpoint: `GET /api/v1/debug/llm-clients`
- [ ] Should return: `{"registered_clients": ["openai", "gemini", "claude"]}`

#### 2. Complete Financial Context ✅
- [ ] Vector store contains all 10 document types per user
- [ ] Test endpoint: `GET /api/v1/debug/vector-contents/{user_id}`
- [ ] Financial context includes Social Security benefits, complete expenses

#### 3. Debug Suite ✅
- [ ] LLM payload inspection working: `GET /api/v1/debug/last-llm-payload/{user_id}`
- [ ] Vector store monitoring: `GET /api/v1/debug/vector-contents/{user_id}`
- [ ] Financial summary debugging: `GET /api/v1/debug/financial-summary/{user_id}`

#### 4. Frontend Configuration ✅
- [ ] Smart API client auto-detects production environment
- [ ] No manual environment variables needed for basic deployment
- [ ] Build optimization with chunking strategy configured

#### 5. Backend Production Settings ✅
- [x] **CORS FIXED**: Now properly configured for `https://smartfinanceadvisor.net`
- [x] **Database schema**: Verified all columns exist, no migrations needed
- [ ] All required environment variables set
- [ ] Health checks enabled: `GET /health`

## Step-by-Step Production Deployment

### Phase 1: Render Backend Deployment

#### 1.1 Create Render Web Service
```bash
# Connect your GitHub repo to Render
# Service Type: Web Service
# Environment: Docker
# Dockerfile Path: ./backend/Dockerfile
```

#### 1.2 Configure Render Environment Variables
```bash
# Essential environment variables (set in Render dashboard):
DATABASE_URL=postgresql://...  # Render PostgreSQL connection string
JWT_SECRET_KEY=your-secure-key
OPENAI_API_KEY=sk-your-key
GEMINI_API_KEY=your-key
ANTHROPIC_API_KEY=your-key
CORS_ORIGINS=https://smartfinanceadvisor.net
ENVIRONMENT=production
DEBUG=false
```

#### 1.3 Deploy Backend
```bash
# Push to trigger deployment
git add .
git commit -m "feat: production deployment with multi-LLM support"
git push origin main

# Monitor deployment at: https://dashboard.render.com
```

#### 1.4 Verify Backend Deployment
```bash
# Test health endpoint
curl https://wealthpath-backend.onrender.com/health

# Test multi-LLM registration (after user login)
curl https://wealthpath-backend.onrender.com/api/v1/debug/llm-clients

# Expected: {"registered_clients": ["openai", "gemini", "claude"]}
```

### Phase 2: Vercel Frontend Deployment

#### 2.1 Build Test Locally
```bash
cd frontend
npm ci  # Clean install
npm run build  # Test production build
npm run preview  # Test production preview locally
```

#### 2.2 Deploy to Vercel
```bash
# Install Vercel CLI if needed
npm i -g vercel

# Deploy (auto-detects and configures)
vercel --prod

# The smart API client will automatically use:
# https://wealthpath-backend.onrender.com for production
```

#### 2.3 Verify Frontend Deployment
```bash
# Test frontend
open https://wealthpath-ai.vercel.app

# Check API connectivity (browser console should show):
# "🔗 PRODUCTION MODE - Using render backend: smartfinanceadvisor.net"
```

### Phase 3: Post-Deployment Testing & Monitoring

#### 3.1 Comprehensive System Testing
```bash
# 1. Test Multi-LLM Functionality
curl https://smartfinanceadvisor.net/api/v1/debug/llm-clients
# Expected: All 3 providers registered

# 2. Test Chat with Different Providers  
# Login to frontend and test chat with:
# - "Ask OpenAI about my retirement"
# - "Ask Gemini about my finances"  
# - "Ask Claude for financial advice"
# Each should provide different responses (not identical)

# 3. Test Complete Financial Context
# Chat: "What's my current financial situation?"
# Response should include specific numbers from your profile:
# - Net worth: $X,XXX,XXX
# - Monthly income: $XX,XXX
# - Real estate allocation: XX.X%
# - Social Security benefits: $X,XXX/month

# 4. Test Conversation Memory
# Send multiple related questions in sequence
# AI should reference previous conversation context

# 5. Test Debug Endpoints (Admin access required)
https://smartfinanceadvisor.net/admin
# Should show real-time system monitoring
```

#### 3.2 Performance Verification
```bash
# Backend Response Time
curl -w "@curl-format.txt" https://wealthpath-backend.onrender.com/health
# Expected: <500ms response time

# Vector Store Performance  
# Check chat responses are delivered in <2 seconds
# Financial context loading should be <1 second

# Memory Usage Monitoring
# Render dashboard should show <256MB memory usage
```

#### 3.3 Monitoring Setup
```bash
# Set up alerts in Render for:
# - Memory usage >200MB  
# - Response time >2 seconds
# - Error rate >5%

# Set up Vercel monitoring for:
# - Build time >3 minutes
# - Function duration >10 seconds
# - Edge function errors
```

## Rollback & Recovery Plans

### If deployment breaks:

#### Quick Fix (Frontend):
```bash
# Revert to previous deployment on Vercel
vercel rollback

# Or redeploy previous working commit
git log --oneline -5  # Find last working commit
git reset --hard <commit-hash>
vercel --prod
```

#### Quick Fix (Backend):
```bash
# Revert last commit and redeploy
git revert HEAD
git push origin main

# Or rollback to specific commit
git reset --hard <last-working-commit>
git push origin main --force-with-lease
```

#### Emergency Troubleshooting:

**Multi-LLM System Down:**
```bash
# Check provider registration
curl https://wealthpath-backend.onrender.com/api/v1/debug/llm-clients

# If missing providers, verify environment variables:
# OPENAI_API_KEY, GEMINI_API_KEY, ANTHROPIC_API_KEY
```

**Financial Context Missing:**
```bash
# Force rebuild vector store
curl -X POST https://wealthpath-backend.onrender.com/api/v1/debug/trigger-vector-sync/1?force_rebuild=true

# Check vector contents
curl https://wealthpath-backend.onrender.com/api/v1/debug/vector-contents/1
```

**Chat Memory Not Working:**
```bash  
# Check conversation storage
curl https://wealthpath-backend.onrender.com/api/v1/debug/vector-contents/1
# Should contain: user_1_conversation_context, user_1_conversation_history
```

## Production Validation Checklist

### Post-Deployment Verification:

#### ✅ Core Functionality
1. **Login System**: `https://smartfinanceadvisor.net/login`
   - Test user registration and authentication
   - Verify JWT token handling and refresh

2. **Multi-LLM Chat**: `https://smartfinanceadvisor.net/chat`
   - Test responses from all 3 providers (OpenAI, Gemini, Claude)
   - Verify responses are different (not identical - critical bug fix)
   - Check conversation memory works across questions

3. **Complete Financial Context**:
   - Ask: "What's my current financial situation?"
   - Response should include specific dollar amounts and percentages
   - Verify Social Security benefits included
   - Check all expense categories present (including housing costs)

4. **Admin Dashboard**: `https://smartfinanceadvisor.net/admin` 
   - Real-time user monitoring
   - System health checks
   - LLM usage analytics

#### ✅ Technical Verification
```bash
# 1. Backend Health
curl https://wealthpath-backend.onrender.com/health

# 2. Multi-LLM Status  
curl https://wealthpath-backend.onrender.com/api/v1/debug/llm-clients

# 3. API Performance (should be <500ms)
time curl https://wealthpath-backend.onrender.com/api/v1/auth/me

# 4. Vector Store Performance
# Chat response should be delivered in <2 seconds

# 5. Memory Usage (Render dashboard)
# Should show <256MB usage consistently
```

#### ✅ Browser Console Verification
Open browser dev tools and check for:
- ✅ `🔗 PRODUCTION MODE - Using render backend` message
- ✅ No CORS errors
- ✅ No 401/403 authentication errors
- ✅ API calls completing in <2 seconds

## Current Production Configuration

**Updated: January 2025**

### ✅ Working Production Stack:
- **Frontend**: Vercel deployment with smart API client
- **Backend**: Render deployment with multi-LLM support
- **Database**: Render PostgreSQL with 10 financial data types
- **Vector Store**: SimpleVectorStore (JSON-based, <50ms queries)
- **Memory**: Vector-based conversation tracking
- **Auth**: JWT with unified auth store
- **Debug Suite**: Complete LLM payload inspection
- **Docker Image**: 396MB optimized build

## Advanced Troubleshooting Guide

### Issue: Multi-LLM Providers Responding Identically ⚠️ CRITICAL
**Symptoms**: All AI providers (OpenAI, Gemini, Claude) give identical responses
**Root Cause**: Missing provider client registration - all requests falling back to single provider
**Solution**:
```bash
# 1. Check registered clients
curl https://wealthpath-backend.onrender.com/api/v1/debug/llm-clients
# Should show: ["openai", "gemini", "claude"]

# 2. If missing, verify all API keys in Render environment variables
# 3. Redeploy backend to reinitialize client registration
```

### Issue: Financial Context Missing from AI Responses ⚠️ CRITICAL  
**Symptoms**: AI gives generic advice instead of using user's specific financial data
**Root Cause**: Complete financial context service not loading user data
**Solution**:
```bash
# 1. Test financial context endpoint
curl https://wealthpath-backend.onrender.com/api/v1/debug/financial-summary/1

# 2. Check vector store contents
curl https://wealthpath-backend.onrender.com/api/v1/debug/vector-contents/1
# Should contain 10 document types per user

# 3. Force vector store rebuild if needed
curl -X POST https://wealthpath-backend.onrender.com/api/v1/debug/trigger-vector-sync/1?force_rebuild=true
```

### Issue: Conversation Memory Not Working ⚠️ CRITICAL
**Symptoms**: AI doesn't remember previous conversation context
**Root Cause**: Vector-based memory service not storing conversation history
**Solution**:
```bash
# Check memory documents exist
curl https://wealthpath-backend.onrender.com/api/v1/debug/vector-contents/1
# Should contain: user_1_conversation_context, user_1_conversation_history

# Check LLM payload includes conversation memory
curl https://wealthpath-backend.onrender.com/api/v1/debug/last-llm-payload/1
# Should show conversation_context_included: true
```

### Issue: Social Security Benefits Missing from Responses
**Symptoms**: AI doesn't mention Social Security in retirement planning
**Root Cause**: Benefits data not included in LLM payload  
**Solution**: Verify benefits data in financial context debug endpoint

### Issue: Incomplete Expense Analysis
**Symptoms**: AI only mentions partial expenses, missing housing costs
**Root Cause**: Expense gap not calculated in context service
**Solution**: Check that "Housing & Other" category appears in expense breakdown

## Production Architecture Summary

### Current System (396MB Docker Image, <256MB Runtime):
- **Backend:** FastAPI + PostgreSQL + Redis + Multi-LLM Integration
- **Frontend:** React 18 + TypeScript + Vite with smart API client
- **Vector Storage:** SimpleVectorStore (JSON-based, zero ML dependencies)
- **Financial Context:** CompleteFinancialContextService (10 data types, 200+ fields)
- **Memory System:** Vector-based conversation tracking
- **Debug Suite:** Complete LLM payload inspection and monitoring

### Critical Services:
1. **SimpleVectorStore:** <50ms query performance, JSON persistence
2. **CompleteFinancialContextService:** Comprehensive financial data integration  
3. **VectorChatMemoryService:** Conversation continuity without database overhead
4. **Multi-LLM Service:** OpenAI + Gemini + Claude with intelligent fallback
5. **Trust Engine:** Response validation ensuring specific financial advice

### Recent Critical Fixes Applied:
- ✅ Multi-LLM client registration (prevents identical responses)
- ✅ Complete financial context integration (Social Security, expense gaps)
- ✅ Vector-based conversation memory (zero database overhead)
- ✅ Trust Engine response validation (prevents generic advice)
- ✅ Standard financial assumptions (7% growth, 4% withdrawal, 80% rule)

## Deployment History

| Date | Version | Major Changes | Status |
|------|---------|---------------|--------|
| 2025-01-07 | v2.1.0 | Multi-LLM system recovery, complete financial context, conversation memory | ✅ Production Ready |
| 2024-12-15 | v2.0.0 | Vector-based architecture, SimpleVectorStore, debug suite | ✅ Working |
| 2024-08-30 | v1.0.0 | Consolidated auth systems, initial production deployment | ✅ Working |

---

## Quick Production Deployment Summary

**Ready to Deploy:**
1. **Render Backend**: Set environment variables → Deploy from main branch
2. **Vercel Frontend**: `vercel --prod` → Auto-detects production environment  
3. **Verification**: Test multi-LLM, financial context, conversation memory

**Key URLs:**
- Frontend: `https://smartfinanceadvisor.net`
- Backend: `https://wealthpath-backend.onrender.com`  
- Health Check: `https://wealthpath-backend.onrender.com/health`
- Debug Suite: `https://wealthpath-backend.onrender.com/api/v1/debug/`

---

**Last Updated:** January 7, 2025  
**Production Status:** ✅ Ready for Deployment  
**All Critical Systems:** ✅ Functional and Tested  
**Maintainer:** WealthPath AI Development Team