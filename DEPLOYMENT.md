# WealthPath AI Deployment Guide

## Overview
This document outlines the configuration differences between local development and production deployment (Vercel/Render) to ensure smooth deployments without breaking either environment.

## Local Development Setup

### Quick Start
```bash
# 1. Start all services
docker-compose up -d

# 2. Verify services are running
docker ps  # Should show: wpa-frontend, wpa-backend, wpa-postgres-1, wpa-redis-1

# 3. Create test user (first time or after reboot)
docker exec -it wpa-backend python -c "
from app.models.user import User
from app.core.database import get_db
from app.core.security import get_password_hash
db = next(get_db())
if not db.query(User).filter(User.email == 'debashishroy@gmail.com').first():
    user = User(email='debashishroy@gmail.com', password_hash=get_password_hash('password123'), is_active=True)
    db.add(user)
    db.commit()
    print('User created')
"

# 4. Access application
# Frontend: http://localhost:3004
# Backend: http://localhost:8000/docs
# Login: debashishroy@gmail.com / password123
```

### Common Issues & Fixes

**After Windows/Mac Reboot - Login fails**
```bash
docker-compose up -d postgres redis  # Containers may not auto-start
docker-compose restart backend        # Reconnect backend to DB
# Then recreate test user (see Quick Start step 3)
```

**Containers show "unhealthy"**
```bash
docker-compose logs backend --tail 20  # Check errors
docker-compose restart                  # Often fixes it
```

**Port conflicts**
```bash
lsof -i :3004  # Check what's using the port
# Change port in docker-compose.yml if needed
```

### Development Commands
```bash
# View logs
docker-compose logs -f backend

# Access database
docker exec -it wpa-postgres-1 psql -U postgres -d wealthpath

# Reset everything
docker-compose down -v && docker-compose up -d

# Clear browser storage (in console)
localStorage.clear(); sessionStorage.clear();
```

## Critical Configuration Differences

### 1. Vite Proxy Configuration
**Local Development:** `frontend/vite.config.ts`
```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8000',  // Local backend
    changeOrigin: true,
  }
}
```

**Docker Development:**
```typescript
proxy: {
  '/api': {
    target: 'http://backend:8000',  // Docker service name
    changeOrigin: true,
  }
}
```

**Production (Vercel/Render):**
- No proxy needed - direct API calls to backend URL
- API calls use full URLs from environment variable

### 2. API Base URL Configuration

**Local:** `frontend/.env.local`
```env
VITE_API_BASE_URL=http://localhost:8000
```

**Production:** `frontend/.env.production`
```env
VITE_API_BASE_URL=https://wealthpath-backend.onrender.com
```

### 3. Chat Component URL
**File:** `frontend/src/components/Chat/FinancialAdvisorChat.tsx`

**Current Implementation (Dynamic):**
```typescript
const baseUrl = getApiBaseUrl();
const fullUrl = `${baseUrl}/api/v1/chat/message`;
```

## Pre-Deployment Checklist

### Before Deploying to Production:

#### 1. Environment Variables on Vercel:
- [ ] Set `VITE_API_BASE_URL=https://wealthpath-backend.onrender.com`
- [ ] Ensure all other required env vars are set

#### 2. Environment Variables on Render:
- [ ] `DATABASE_URL` (PostgreSQL connection string)
- [ ] `JWT_SECRET_KEY` (secure random string)
- [ ] `OPENAI_API_KEY` (or other LLM keys)
- [ ] `CORS_ORIGINS` includes `https://wealthpath-ai.vercel.app`

#### 3. Code Adjustments:
- [ ] DO NOT commit `.env.local` file
- [ ] Ensure `frontend/.env.production` exists with production URLs
- [ ] Verify CORS settings in backend allow Vercel domain
- [ ] Test build locally with `npm run build`

## Deployment Commands

### Deploy Frontend to Vercel:
```bash
cd frontend
npm run build  # Test build locally first
vercel --prod  # Deploy to production
```

### Deploy Backend to Render:
```bash
# Render auto-deploys from GitHub main branch
git add .
git commit -m "deploy: description of changes"
git push origin main
```

## Environment-Specific Build Script

Consider adding to `frontend/package.json`:
```json
{
  "scripts": {
    "dev": "vite",
    "dev:docker": "DOCKER_ENV=true vite",
    "build": "vite build",
    "build:production": "vite build --mode production",
    "preview": "vite preview"
  }
}
```

## Smart Configuration Approach

### Option 1: Environment-Aware Vite Config
Update `frontend/vite.config.ts`:
```typescript
export default defineConfig(({ mode }) => {
  const isProduction = mode === 'production';
  const isDocker = process.env.DOCKER_ENV === 'true';
  
  return {
    plugins: [react()],
    server: {
      port: 3000,
      proxy: !isProduction ? {
        '/api': {
          target: isDocker ? 'http://backend:8000' : 'http://localhost:8000',
          changeOrigin: true,
        }
      } : undefined
    }
  };
});
```

### Option 2: API Client Environment Detection
Update `frontend/src/utils/api-simple.ts`:
```typescript
const getBaseURL = () => {
  // Production: Use environment variable
  if (import.meta.env.PROD && import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  
  // Development: Use proxy (relative URLs)
  return '';
};
```

## Rollback Plan

### If deployment breaks:

#### Quick Fix (Frontend):
```bash
# Revert to previous deployment on Vercel
vercel rollback
```

#### Quick Fix (Backend):
```bash
# Revert last commit and force push
git revert HEAD
git push origin main --force
```

## Testing Deployment

### Local Testing of Production Build:
```bash
# Frontend
cd frontend
npm run build
npm run preview  # Serves production build locally on port 4173

# Backend
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Post-Deployment Verification:
1. ✅ Check login works: https://wealthpath-ai.vercel.app
2. ✅ Test chat functionality
3. ✅ Verify financial data loads
4. ✅ Check browser console for errors
5. ✅ Monitor Render logs for backend errors

## Current Working Configuration

As of August 30, 2024, the working configuration is:
- **Local:** Using localhost:8000 proxy
- **Production:** Using environment variable VITE_API_BASE_URL
- **Auth:** Single `unified-auth-store.ts`
- **API Client:** Single `api-simple.ts`
- **Docker Image:** 396MB optimized build

## Common Issues and Solutions

### Issue: Chat 401 errors in production
**Solution:** Ensure auth tokens are being sent with requests. Check that the unified auth store is properly initialized and tokens are in sessionStorage.

### Issue: CORS errors
**Solution:** Verify backend CORS settings include frontend domain. Check docker-compose.yml for CORS_ORIGINS environment variable.

### Issue: API calls failing locally
**Solution:** Check vite proxy configuration points to correct backend URL (localhost:8000 for local, backend:8000 for Docker).

### Issue: Login not working locally
**Solution:** See Local Development Setup - likely missing postgres container after reboot.

### Issue: Different auth systems conflicting
**Solution:** Ensure only `unified-auth-store.ts` is being used. Delete any references to `auth-store.ts` or `secure-auth-service.ts`.

## Architecture Notes

### Optimized System (396MB Docker Image):
- **Backend:** FastAPI + PostgreSQL + Redis (15 packages only)
- **Frontend:** React 18 + TypeScript + Vite
- **Vector Storage:** Simple JSON store (no ML dependencies)
- **Memory:** <256MB runtime usage

### Key Services:
1. **SimpleVectorStore:** JSON-based, no ChromaDB
2. **SmartContextSelector:** Keyword-based, prevents repetition
3. **MLFallbacks:** Pure Python, no numpy/pandas
4. **Unified Auth:** Session-based with tab isolation

## Deployment History

| Date | Version | Changes | Status |
|------|---------|---------|--------|
| 2024-08-30 | v1.0.0 | Consolidated auth systems, fixed local dev | ✅ Working |
| 2024-08-29 | v0.9.0 | Initial deployment with 3 auth systems | ⚠️ Had issues |

---

**Last Updated:** August 30, 2024  
**Configuration Verified Working:** Yes ✅  
**Maintainer:** WealthPath AI Team