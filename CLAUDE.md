# Claude Code Development Guide

## 🎯 Purpose
This file provides Claude Code with essential technical context for WealthPath AI development - now optimized from 14.6GB to 396MB!

## 🏗️ Optimized System Architecture (396MB Docker Image!)

### Core Stack
- **Backend**: FastAPI + PostgreSQL + Redis (15 packages only)
- **Frontend**: React 18 + TypeScript + Vite  
- **Admin**: 5-section dashboard with real data integration
- **AI**: Multi-LLM (OpenAI/Gemini/Claude) with simple JSON vector store
- **Vector Storage**: Simple JSON store (pure Python, no ML dependencies)
- **Memory**: <256MB runtime (perfect for cloud free tiers)

### Key Directories
```
backend/app/api/v1/endpoints/    # API endpoints
backend/app/services/            # Business logic (optimized)
├── simple_vector_store.py       # JSON-based vector store
├── smart_context_selector.py    # Keyword-based context selection
└── ml_fallbacks.py              # Pure Python ML replacements
frontend/src/components/         # React components
frontend/src/components/admin/   # Admin dashboard
```

## 🚨 Critical Development Rules

### NEVER Break These
1. **Admin Isolation**: Admin changes must not affect main app
2. **Authentication**: Always verify `debashishroy@gmail.com` for admin
3. **Real Data**: Replace mock data with actual database queries
4. **Error Handling**: Graceful fallbacks for all API failures
5. **NO ML Dependencies**: Never add numpy, pandas, torch, chromadb, etc.
6. **Simple Vector Store**: Use JSON store, not ChromaDB

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

```python
# Vector store usage (NO ChromaDB!)
from app.services.simple_vector_store import simple_vector_store

# Add documents
simple_vector_store.add_document("doc_id", "content", {"metadata": "value"})

# Search documents  
results = simple_vector_store.search("query", limit=5)
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
- ✅ **Debug Tools** - Real system metrics (using simple vector store)
- ✅ **Data Integrity** - Real database validation

## 🔌 Key API Endpoints

### Admin APIs (All require admin auth)
```
GET /api/v1/admin/users         # User management
GET /api/v1/admin/health        # System health
GET /api/v1/admin/sessions      # Active sessions
GET /api/v1/admin/debug/logs    # System logs
GET /api/v1/admin/data-integrity # DB validation
GET /api/v1/admin/debug/vector-contents/{user_id} # Vector store debug
```

### Main App APIs
```
POST /api/v1/advisory           # AI financial advice
GET /api/v1/financial/summary   # User financial data
POST /api/v1/auth/login         # User authentication
POST /api/v1/sync-finances      # Financial data sync
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

# Docker build test (should be ~396MB)
docker build -t wpa-test .
```

## 🚀 Architecture Optimization Details

### **Before (14.6GB Monster)**
- Dependencies: 56+ packages (torch, numpy, pandas, chromadb)
- Docker Image: 14.6GB with CUDA/ML packages
- Memory: >2GB runtime usage
- Build Time: 10+ minutes
- Deployment: Impossible on free tiers

### **After (396MB Beast)**
- Dependencies: 15 essential packages only
- Docker Image: 396MB (97% reduction!)
- Memory: <256MB runtime usage  
- Build Time: ~30 seconds
- Deployment: Perfect for free tiers

### **Key Services (Optimized)**
1. **SimpleVectorStore**: JSON-based, no ChromaDB
2. **SmartContextSelector**: Keyword-based, prevents repetition
3. **MLFallbacks**: Pure Python, no numpy/pandas
4. **OpenAI Embeddings**: API-based, no local models

## 📝 Recent Changes (Massive Optimization)
- ✅ ChromaDB → Simple JSON Vector Store
- ✅ All ML dependencies removed (torch, numpy, pandas)
- ✅ Dead code cleanup (200KB+ files removed)
- ✅ Docker optimization (14.6GB → 396MB)
- ✅ File consolidation (6 Dockerfiles → 1, 6 requirements → 1)
- ✅ Admin dashboard fully operational with real data
- ✅ All functionality verified working

## 🎯 Current Development Focus
- ✅ **System ready for production deployment**
- ✅ **Documentation updated** 
- ✅ **Massive optimization completed**
- **No new features** - focus on deployment and stability
- **Maintain <256MB memory usage**

## ⚠️ Development Warnings

### NEVER Do These
- ❌ Add ML packages (numpy, pandas, torch, chromadb)
- ❌ Use ChromaDB collection methods
- ❌ Import sentence_transformers or similar
- ❌ Create multiple Dockerfiles/requirements files
- ❌ Break the 396MB Docker image size

### ALWAYS Do These  
- ✅ Use simple_vector_store for all vector operations
- ✅ Test Docker build size regularly
- ✅ Verify memory usage <256MB
- ✅ Use fallback implementations for math operations
- ✅ Keep admin auth restricted to debashishroy@gmail.com

---

*This file is specifically for Claude Code development context.*  
*System optimized from 14.6GB to 396MB - Production ready! 🚀*