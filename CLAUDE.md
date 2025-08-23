# Claude Code Development Guide

## 🎯 Purpose
This file provides Claude Code with essential technical context for WealthPath AI development.

## 🏗️ System Architecture Quick Reference

### Core Stack
- **Backend**: FastAPI + PostgreSQL + Redis
- **Frontend**: React 18 + TypeScript + Vite  
- **Admin**: 5-section dashboard with real data integration
- **AI**: Multi-LLM (OpenAI/Gemini/Claude) with vector DB

### Key Directories
```
backend/app/api/v1/endpoints/    # API endpoints
backend/app/services/            # Business logic
frontend/src/components/         # React components
frontend/src/components/admin/   # Admin dashboard
```

## 🚨 Critical Development Rules

### NEVER Break These
1. **Admin Isolation**: Admin changes must not affect main app
2. **Authentication**: Always verify `debashishroy@gmail.com` for admin
3. **Real Data**: Replace mock data with actual database queries
4. **Error Handling**: Graceful fallbacks for all API failures

### Always Follow These Patterns
```python
# Admin endpoint pattern
@router.get("/admin/endpoint")
async def admin_function(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.email != "debashishroy@gmail.com":
        raise HTTPException(status_code=403, detail="Admin access required")
```

```typescript
// Frontend data fetching pattern
const [data, setData] = useState(null);
const [loading, setLoading] = useState(true);

useEffect(() => {
  fetchData();
  const interval = setInterval(fetchData, 30000); // Auto-refresh
  return () => clearInterval(interval);
}, []);
```

## 📊 Admin Dashboard Status

### Completed Sections (All with Real Data)
- ✅ **User Management** - Real user data from PostgreSQL
- ✅ **System Health** - Real service monitoring
- ✅ **Auth Monitor** - Real session tracking
- ✅ **Debug Tools** - Real system metrics
- ✅ **Data Integrity** - Real database validation

## 🔌 Key API Endpoints

### Admin APIs (All require admin auth)
```
GET /api/v1/admin/users         # User management
GET /api/v1/admin/health        # System health
GET /api/v1/admin/sessions      # Active sessions
GET /api/v1/admin/debug/logs    # System logs
GET /api/v1/admin/data-integrity # DB validation
```

### Main App APIs
```
POST /api/v1/advisory           # AI financial advice
GET /api/v1/financial/summary   # User financial data
POST /api/v1/auth/login         # User authentication
```

## 🎨 UI Styling Standards

### Dark Theme (Consistent across all admin)
```typescript
// Card styling
className="bg-gray-800 border border-gray-700 text-gray-100"

// Text styling  
className="text-white"           // Headers
className="text-gray-300"        // Labels  
className="text-gray-400"        // Descriptions

// Status colors (preserve these)
className="text-green-500"       // Healthy
className="text-red-500"         // Error
className="text-yellow-500"      // Warning
```

## 🧪 Testing Requirements

### Before Any Deployment
```bash
# Backend tests
cd backend && pytest --cov=app

# Frontend compilation
cd frontend && npm run build

# Admin functionality
python test_data_integrity_endpoint.py
```

## 📝 Recent Changes (CR #001-#006)
- All mock data replaced with real database queries
- Admin dashboard fully operational
- Dark theme consistency implemented
- Auto-refresh functionality added
- Error handling and fallbacks implemented

## 🎯 Current Development Focus
- System ready for production deployment
- Documentation updates and deployment preparation
- No new features - focus on stability and deployment readiness

---

*This file is specifically for Claude Code development context.*  
*For comprehensive documentation, see README.md*