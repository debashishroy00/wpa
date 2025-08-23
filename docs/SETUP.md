# WealthPath AI - Development Setup Guide (Windows)

## Prerequisites

- **Python 3.11+** - Download from [python.org](https://www.python.org/downloads/)
- **Node.js 18+** - Download from [nodejs.org](https://nodejs.org/)
- **Docker Desktop** - Download from [docker.com](https://www.docker.com/products/docker-desktop/)
- **Git** - Download from [git-scm.com](https://git-scm.com/)

## Quick Start

### 1. Open Project in Terminal
```cmd
# Navigate to project directory
cd C:\projects\wpa
```

### 2. Install Backend Dependencies (Python)
```cmd
# Navigate to backend folder
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Install Frontend Dependencies (Node.js)
```cmd
# Open new terminal window and navigate to frontend
cd C:\projects\wpa\frontend

# Install dependencies
npm install
```

### 4. Environment Setup
```cmd
# Copy environment file (in project root)
cd C:\projects\wpa
copy .env.development .env

# Start database services with Docker
docker-compose up -d postgres redis

# Or start all services
docker-compose up
```

### 5. Database Setup
```cmd
# In backend folder with activated virtual environment
cd C:\projects\wpa\backend
venv\Scripts\activate

# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Run migrations
alembic upgrade head
```

### 6. Start Development Servers

**Option A: Using Docker (Recommended)**
```cmd
cd C:\projects\wpa
docker-compose up
```

**Option B: Local Development**
```cmd
# Terminal 1 - Backend
cd C:\projects\wpa\backend
venv\Scripts\activate
uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend (new terminal)
cd C:\projects\wpa\frontend
npm run dev
```

### 5. Access Applications
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090

## Development Workflow

### VS Code Setup
1. Install Python and Node.js extensions
2. Select Python interpreter: `backend/venv/bin/python`
3. Install recommended extensions:
   - Python
   - Pylance
   - TypeScript and JavaScript Language Features
   - Tailwind CSS IntelliSense
   - Docker

### Resolving Import Errors (VS Code)
The import errors you're seeing are because VS Code can't find the packages. Fix by:

1. **Select correct Python interpreter**:
   - Press `Ctrl+Shift+P` 
   - Type "Python: Select Interpreter"
   - Choose `.\backend\venv\Scripts\python.exe`

2. **Ensure dependencies are installed**:
   ```cmd
   cd C:\projects\wpa\backend
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Restart VS Code** or reload window (`Ctrl+Shift+P` → "Developer: Reload Window")

### Running Tests
```cmd
# Backend tests
cd C:\projects\wpa\backend
venv\Scripts\activate
pytest

# Frontend tests
cd C:\projects\wpa\frontend
npm test

# Run with coverage
npm run test:coverage
```

## Troubleshooting

### Common Issues

**PowerShell Execution Policy Error**:
```powershell
# Run as Administrator and enable script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Port already in use**:
```cmd
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process by PID
taskkill /PID <PID_NUMBER> /F

# Or use different ports in docker-compose.yml
```

**Docker Desktop not running**:
```cmd
# Start Docker Desktop manually
# Or check if Docker is running
docker version
```

**Virtual environment activation issues**:
```cmd
# Make sure you're in the right directory
cd C:\projects\wpa\backend

# Try absolute path
C:\projects\wpa\backend\venv\Scripts\activate

# If still issues, recreate venv
rmdir venv /s
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**Database connection errors**:
```cmd
# Check if PostgreSQL is running
docker-compose ps

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

**Redis connection errors**:
```cmd
# Check Redis status
docker-compose exec redis redis-cli ping
# Should return PONG
```

**Path issues with long Windows paths**:
```cmd
# Enable long path support (Run as Administrator)
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

### Development Tips

1. **Hot Reloading**: Both backend (FastAPI) and frontend (Vite) support hot reloading
2. **Database Changes**: Use Alembic migrations for schema changes
3. **API Testing**: Use the interactive docs at http://localhost:8000/docs
4. **Debugging**: Enable debug logging in .env: `DEBUG=true`

### Next Steps

Once setup is complete, you can:

1. **Test Authentication**: Register a user via API docs
2. **Create Financial Entries**: Test manual data entry
3. **Set up Goals**: Create a sample retirement goal
4. **Verify Database**: Check PostgreSQL tables are created
5. **Monitor Performance**: View metrics in Grafana

## File Structure Overview

```
wpa/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Configuration & security  
│   │   ├── db/          # Database setup
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas
│   │   └── services/    # Business logic
│   ├── alembic/         # Database migrations
│   └── tests/           # Backend tests
├── frontend/            # React frontend
│   ├── src/
│   │   ├── components/  # UI components
│   │   ├── pages/       # Application pages
│   │   ├── hooks/       # Custom hooks
│   │   ├── stores/      # Zustand stores
│   │   └── utils/       # Utility functions
│   └── tests/           # Frontend tests
└── infrastructure/      # Docker & deployment
    ├── docker/          # Docker configurations
    └── monitoring/      # Monitoring setup
```

Ready to begin Phase 2 development! 🚀