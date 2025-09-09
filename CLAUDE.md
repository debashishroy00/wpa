# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

WealthPath AI is an optimized financial planning platform with a FastAPI backend and React frontend, designed for maximum efficiency:

- **Backend**: FastAPI + PostgreSQL + Redis (17 core packages only, 396MB Docker image)
- **Frontend**: React 18 + TypeScript + Vite with Tailwind CSS
- **Database**: PostgreSQL with Alembic migrations
- **Cache**: Redis for session management and caching
- **Vector Storage**: Simple JSON-based vector store (no ML dependencies)
- **LLM Integration**: Multi-provider support (OpenAI, Gemini, Anthropic)
- **Deployment**: Optimized for cloud platforms (Railway, Render, Vercel)

## Key Development Commands

### Backend Development
```bash
# Setup virtual environment
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Database migrations
alembic revision --autogenerate -m "Description"
alembic upgrade head

# Run backend (development)
uvicorn app.main:app --reload --port 8000

# Run backend (production)
gunicorn app.main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Run tests
pytest
pytest --cov=app  # With coverage
```

### Frontend Development
```bash
cd frontend

# Install dependencies
npm install

# Development server
npm run dev

# Type checking
npm run type-check

# Build for production
npm run build

# Linting
npm run lint

# Tests
npm test
npm run test:coverage
```

### Docker Development
```bash
# Start all services (recommended)
docker-compose up

# Start with monitoring (Prometheus/Grafana)
docker-compose --profile monitoring up

# Build without cache
docker-compose build --no-cache

# Stop services
docker-compose down

# Clean up (remove volumes)
docker-compose down -v

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

## Project Structure

### Backend (`/backend/`)
```
app/
├── api/v1/endpoints/     # API endpoints
│   ├── auth.py          # Authentication
│   ├── advisory.py      # LLM advisory engine
│   ├── financial.py     # Financial data
│   ├── admin.py         # Admin dashboard
│   └── health.py        # Health checks
├── core/                # Core configuration
│   ├── config.py        # Settings management
│   ├── security.py      # JWT authentication
│   └── cache.py         # Redis cache utilities
├── models/              # SQLAlchemy models
│   ├── user.py         # User models
│   ├── financial.py    # Financial data models
│   └── goal.py         # Goal tracking
├── schemas/             # Pydantic schemas
├── services/            # Business logic
│   ├── simple_vector_store.py      # JSON vector storage
│   ├── ml_fallbacks.py            # Pure Python ML replacements
│   ├── advisory_engine.py         # LLM advisory service
│   └── chat_memory_service.py     # Conversation memory
└── middleware/          # Custom middleware
```

### Frontend (`/frontend/`)
```
src/
├── components/          # React components
│   ├── Chat/           # Chat interface
│   ├── Dashboard/      # Main dashboard
│   ├── admin/          # Admin components
│   └── ui/             # Reusable UI components
├── pages/              # Page components
├── hooks/              # Custom React hooks
├── stores/             # Zustand state management
├── services/           # API clients
└── utils/              # Utility functions
```

## Critical Development Rules

### Never Break These
1. **No ML Dependencies**: Never add numpy, pandas, torch, chromadb, or any ML packages
2. **Use Simple Vector Store**: Always use `simple_vector_store.py` for vector operations
3. **Admin Authentication**: Admin endpoints must verify `debashishroy@gmail.com`
4. **Docker Size Limit**: Keep Docker image under 500MB (currently 396MB)
5. **Memory Limit**: Maintain <256MB runtime memory usage

### Authentication Patterns
```python
# Standard user authentication
@router.get("/endpoint")
async def endpoint(current_user: User = Depends(get_current_user)):
    pass

# Admin-only endpoint
@router.get("/admin/endpoint")
async def admin_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.email != "debashishroy@gmail.com":
        raise HTTPException(status_code=403, detail="Admin access required")
    # Admin logic here
```

### Vector Store Usage
```python
from app.services.simple_vector_store import simple_vector_store

# Add documents
simple_vector_store.add_document("doc_id", "content", {"metadata": "value"})

# Search documents  
results = simple_vector_store.search("query", limit=5)

# Get document
doc = simple_vector_store.get_document("doc_id")
```

## Database Patterns

### Alembic Migration Workflow
```bash
# Create new migration after model changes
alembic revision --autogenerate -m "Add new table"

# Review generated migration file in alembic/versions/
# Edit if necessary, then apply
alembic upgrade head

# Check current migration status
alembic current

# Rollback one migration
alembic downgrade -1
```

## API Endpoint Patterns

### Standard CRUD Operations
```python
@router.get("/items", response_model=List[ItemResponse])
async def get_items(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    items = db.query(Item).filter(Item.user_id == current_user.id).offset(skip).limit(limit).all()
    return items

@router.post("/items", response_model=ItemResponse)
async def create_item(
    item: ItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_item = Item(**item.dict(), user_id=current_user.id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
```

## Frontend Patterns

### Component Structure
```typescript
// Standard component with TypeScript
interface ComponentProps {
  data: DataType[];
  onUpdate: (id: string) => void;
}

export const Component: React.FC<ComponentProps> = ({ data, onUpdate }) => {
  const [loading, setLoading] = useState(false);
  
  // API calls with error handling
  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await api.getData();
      // Handle response
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gray-800 border border-gray-700 text-gray-100">
      {/* Component content */}
    </div>
  );
};
```

### State Management with Zustand
```typescript
interface StoreState {
  data: DataType[];
  loading: boolean;
  setData: (data: DataType[]) => void;
  setLoading: (loading: boolean) => void;
}

export const useStore = create<StoreState>((set) => ({
  data: [],
  loading: false,
  setData: (data) => set({ data }),
  setLoading: (loading) => set({ loading }),
}));
```

## Environment Configuration

### Backend Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/wealthpath_db

# Authentication
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15

# LLM Providers
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
ANTHROPIC_API_KEY=...
LLM_DEFAULT_PROVIDER=openai

# Redis
REDIS_URL=redis://localhost:6379

# Development
DEBUG=true
ENVIRONMENT=development
```

### Frontend Environment Variables
```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_ENVIRONMENT=development
```

## Testing Guidelines

### Backend Testing
```python
# Test file structure: test_*.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_endpoint():
    response = client.get("/api/v1/test")
    assert response.status_code == 200
    assert "expected_field" in response.json()
```

### Frontend Testing
```typescript
// Component testing with React Testing Library
import { render, screen, fireEvent } from '@testing-library/react';
import { Component } from './Component';

test('renders component correctly', () => {
  render(<Component />);
  expect(screen.getByText('Expected Text')).toBeInTheDocument();
});
```

## Performance Optimizations

### Backend Optimizations
- Use Redis caching for frequent database queries
- Implement pagination for large datasets
- Use database indexing for search queries
- Keep vector operations in JSON format (no ChromaDB)

### Frontend Optimizations
- Use React.memo for expensive components
- Implement virtual scrolling for large lists
- Lazy load heavy components
- Optimize bundle size with code splitting

## Deployment

### Docker Build Process
```bash
# Backend Dockerfile optimized for small size
# Currently builds to 396MB production image
docker build -t wpa-backend .

# Frontend optimized build
docker build -t wpa-frontend -f Dockerfile.optimized .
```

### Production Checklist
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Redis connection verified
- [ ] LLM API keys configured
- [ ] Docker image size under 500MB
- [ ] Memory usage under 256MB
- [ ] Health endpoints responding
- [ ] CORS configured for production domain

## Common Issues and Solutions

### Import Errors
- Ensure virtual environment is activated
- Check that all dependencies are in requirements.txt
- Verify Python interpreter selection in IDE

### Database Connection Issues
- Check DATABASE_URL format
- Ensure PostgreSQL service is running
- Verify user permissions and database exists

### Docker Issues
- Clear Docker cache: `docker system prune -a`
- Check port conflicts: `docker ps`
- Verify environment variables in docker-compose.yml

### Frontend Build Issues
- Clear node_modules: `rm -rf node_modules && npm install`
- Check TypeScript errors: `npm run type-check`
- Verify API base URL configuration

This codebase is optimized for production deployment with minimal resource usage while maintaining full functionality.