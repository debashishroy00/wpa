# WealthPath AI - Intelligent Financial Planning Platform 🚀

> **Multi-AI Financial Advisory • Complete Portfolio Management • Real-time Projections**

[![Production Ready](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)](https://github.com/debashishroy00/wpa)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.2.0-61dafb)](https://reactjs.org)
[![Docker](https://img.shields.io/badge/Docker-396MB-blue)](https://hub.docker.com)
[![Multi-LLM](https://img.shields.io/badge/AI-Multi--LLM%20Support-orange)](https://openai.com)
[![Deployment](https://img.shields.io/badge/Deploy-Render%20%7C%20Railway-purple)](https://render.com)

## 🌟 Why WealthPath AI?

**🤖 Intelligent Financial Advisory:**
- **Multi-AI Support**: OpenAI GPT-4, Google Gemini Pro, and Anthropic Claude with intelligent fallback
- **Smart Conversations**: Vector-based memory system with conversation continuity and context awareness
- **Complete Financial Context**: Every AI response uses your complete financial profile (10 data types)
- **Response Validation**: Trust Engine ensures specific, data-driven advice (not generic responses)
- **Real-time Calculations**: Standard financial assumptions built-in (7% growth, 4% withdrawal, 80% rule)

**💼 Comprehensive Financial Management:**
- **Complete Financial Profile**: 200+ data points across 10 financial categories (assets, liabilities, goals, taxes, benefits)
- **Advanced Analytics**: Real-time calculations for net worth, cash flow, savings rate, debt-to-income ratios
- **Social Security Optimization**: Claiming scenarios analysis with break-even calculations
- **Tax Strategy Planning**: Backdoor Roth, Mega Backdoor Roth, tax-loss harvesting, bracket optimization
- **401k & Benefits Optimization**: Employer match analysis, vesting strategies, contribution limits

**🚀 Enterprise-Ready Platform:**
- **Zero ML Dependencies**: SimpleVectorStore (JSON-based) for fast, reliable performance
- **Debug & Monitoring**: Complete LLM payload inspection, vector store debugging, multi-LLM health checks  
- **Production Optimized**: <256MB memory usage, 396MB Docker image, <50ms query response time
- **Cloud Native**: Deploy on Railway, Render, AWS, or any Docker platform with health checks

**⚡ Reliable & Accessible:**
- **Always Available**: Lightning-fast startup means no waiting for your financial data
- **Cost-Effective**: Runs on free cloud tiers, keeping your hosting costs minimal
- **Simple Setup**: One-click deployment with no complex ML infrastructure needed
- **Dependable**: Streamlined architecture means fewer things that can break or slow down

## 🏗️ Optimized Technology Stack

### **Backend** (396MB Docker Image)
- **Framework**: FastAPI 0.104.1 + Uvicorn/Gunicorn
- **Database**: PostgreSQL 14 with SQLAlchemy ORM + Alembic migrations
- **Cache**: Redis 7 for session management and LLM caching
- **Vector Store**: SimpleVectorStore (JSON-based, zero ML dependencies)
- **AI Integration**: Multi-LLM with intelligent fallback (OpenAI, Gemini, Claude)
- **Financial Context**: CompleteFinancialContextService with 10 synchronized data types
- **Auth**: JWT with refresh tokens, secure session handling
- **Debug Tools**: LLM payload inspection, vector store monitoring, multi-LLM health checks
- **API**: 25+ REST endpoints with comprehensive financial advisory capabilities

### **Frontend** (React 18 + TypeScript)
- **Framework**: React 18.2.0 with TypeScript 5.2
- **Build**: Vite 5.0 for fast development and optimized builds
- **Styling**: Tailwind CSS 3.3 with responsive dark theme
- **State Management**: Zustand + React Query for efficient state
- **UI Components**: Radix UI primitives + Lucide React icons
- **Charts**: Recharts for financial data visualization
- **Admin Dashboard**: Real-time monitoring with auto-refresh
- **Testing**: Jest + React Testing Library

### **Deployment Stack**
- **Container**: Multi-service Docker Compose setup
- **Backend Dependencies**: Clean requirements.txt (17 packages)
- **Frontend Dependencies**: Modern React ecosystem (40+ dev packages)
- **Hosting**: Render, Railway, or any Docker platform
- **Database**: PostgreSQL 14 (cloud-ready with health checks)
- **Cache**: Redis 7 (Alpine-based, minimal footprint)
- **Monitoring**: Optional Prometheus + Grafana stack
- **Memory**: <256MB per service (perfect for free tiers!)

## 🚀 Quick Deployment

### 1. **Docker (Production-Ready)**
```bash
git clone https://github.com/debashishroy00/wpa.git
cd wpa
docker-compose up -d

# Services will be available at:
# Frontend: http://localhost:3004
# Backend API: http://localhost:8000/docs
# Admin Dashboard: http://localhost:3004/admin
# Prometheus (optional): http://localhost:9090
# Grafana (optional): http://localhost:3001
```

### 2. **Cloud Deployment (Render/Railway)**
```bash
# Backend automatically deploys from Dockerfile
# Frontend deploys from frontend/ directory
# Total memory: <256MB (free tier compatible!)
```

## 🎯 Core Features

### **🔮 AI Financial Advisory Engine**
- **Multi-LLM Architecture**: OpenAI GPT-4 + Google Gemini Pro + Anthropic Claude with diversified fallback
- **Complete Financial Context**: Every response uses all 10 financial data types (assets, liabilities, goals, taxes, benefits)
- **Vector-Based Memory**: VectorChatMemoryService with conversation continuity and intent tracking
- **Response Validation**: Trust Engine scores responses to ensure specific financial data usage (not generic advice)
- **Standard Assumptions Built-In**: 7% investment growth, 4% withdrawal rate, 80% retirement expense rule
- **Debug Transparency**: Complete LLM payload inspection with context analysis and validation scoring

### **📊 Comprehensive Financial Management**
- **Complete Financial Profile**: 200+ data points across assets, liabilities, income, expenses, goals, taxes, benefits, estate, insurance
- **Real-Time Analytics**: Net worth tracking, cash flow analysis, savings rate, debt-to-income ratios, emergency fund coverage
- **Advanced Tax Optimization**: Backdoor Roth eligibility, Mega Backdoor Roth strategies, tax-loss harvesting, bracket optimization
- **Social Security Planning**: Claiming scenarios (early/FRA/delayed), break-even analysis, spouse benefit optimization
- **401k & Benefits Strategy**: Employer match analysis, vesting schedules, contribution limits, HSA planning
- **Estate & Insurance Tracking**: Document management, beneficiary designations, policy optimization
- **Goal Achievement**: SMART financial goals with progress visualization and timeline tracking

### **🛡️ Enterprise Admin Dashboard**
- **Real-time User Management**: Live PostgreSQL user data with detailed profiles
- **System Health Monitoring**: Service status, database connections, Redis cache
- **Authentication Monitor**: Active sessions, login analytics, security events
- **Advanced Debug Tools**: System logs, API performance, database queries
- **Data Integrity Validation**: Comprehensive database health checks
- **Shadow Mode**: Admin access without affecting user experience
- **LLM Usage Analytics**: AI provider usage and cost tracking

### **⚡ Advanced Performance Optimizations**
- **SimpleVectorStore**: JSON-based storage with <50ms query response time, zero ML dependencies
- **Real-Time Synchronization**: VectorSyncService automatically syncs PostgreSQL changes to vector store
- **Complete Context Loading**: CompleteFinancialContextService provides comprehensive financial data for every AI response
- **Multi-LLM Fallback**: Intelligent provider routing with diversified fallback (openai → claude → gemini)
- **Response Validation**: Trust Engine ensures AI responses contain specific financial data, not generic advice
- **Debug Monitoring**: LLM payload inspection, vector store health checks, multi-provider status monitoring
- **Memory Efficiency**: <256MB runtime per service, <10MB vector storage per user

## 🔐 Authentication

```bash
# Demo User Access
Email: test@gmail.com
Password: password123

# Admin access restricted to authorized personnel
```

## 📁 Advanced Project Structure

```
wpa/
├── backend/                    # 396MB Docker image
│   ├── app/
│   │   ├── api/v1/endpoints/  # 20+ API routes (auth, advisory, financial, admin)
│   │   ├── services/          # Business logic (LLM, vector store, calculations)
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── schemas/           # Pydantic data validation
│   │   └── core/              # Configuration, security, middleware
│   ├── alembic/               # Database migrations
│   ├── Dockerfile             # Multi-stage optimized build
│   └── requirements.txt       # 17 essential packages only
├── frontend/                  # React TypeScript with Vite
│   ├── src/
│   │   ├── components/        # React components (Chat, Dashboard, Admin)
│   │   ├── pages/             # Route components
│   │   ├── hooks/             # Custom React hooks
│   │   ├── stores/            # Zustand state management
│   │   └── services/          # API client services
│   ├── package.json           # 40+ dev packages, optimized build
│   └── vite.config.ts         # Vite configuration
├── docker-compose.yml         # Multi-service development
├── backend/docs/              # Technical documentation
│   ├── CHAT.md               # Chat service architecture and multi-LLM integration
│   ├── VECTOR.md             # Vector database implementation and recent fixes  
│   └── DATA.md               # Data model documentation and PostgreSQL mapping
├── CLAUDE.md                  # Development guidelines and project architecture
└── README.md                 # This comprehensive overview
```

## 🛠️ Development

### **Backend Development**
```bash
cd backend
# Setup virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies (17 packages only!)
pip install -r requirements.txt

# Database setup
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000
```

### **Frontend Development**
```bash
cd frontend
# Install dependencies
npm install

# Start development server
npm run dev

# Type checking
npm run type-check

# Build for production
npm run build
```

### **Docker Development (Recommended)**
```bash
# Start all services
docker-compose up

# With monitoring stack
docker-compose --profile monitoring up

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### **Testing & Validation**
```bash
# Backend tests
cd backend
pytest --cov=app

# Frontend build validation
cd frontend
npm run build
npm run type-check

# System integration tests
python test_complete_system.py
```

## 🌐 Comprehensive API Documentation

### **Authentication & Users**
```
POST /api/v1/auth/login          # User authentication
POST /api/v1/auth/register       # User registration  
POST /api/v1/auth/refresh        # Token refresh
GET  /api/v1/auth/me            # Current user profile
```

### **AI Advisory Engine**
```
POST /api/v1/chat/message               # Multi-LLM chat with complete financial context
GET  /api/v1/debug/last-llm-payload/{user_id}    # LLM payload inspection
GET  /api/v1/debug/vector-contents/{user_id}     # Vector store debugging
GET  /api/v1/debug/llm-clients          # Multi-LLM health check
POST /api/v1/debug/trigger-vector-sync/{user_id} # Force vector rebuild
```

### **Financial Management**
```
GET  /api/v1/profile/financial-summary  # Complete financial overview
POST /api/v1/profile/benefits          # 401k and benefits optimization  
POST /api/v1/profile/tax-info           # Tax planning and strategies
GET  /api/v1/goals                      # SMART financial goals tracking
POST /api/v1/goals                      # Create new goal with progress tracking
GET  /api/v1/debug/financial-summary/{user_id}  # Financial context debugging
```

### **Admin Dashboard (Restricted Access)**
```
GET /api/v1/admin/users           # Real-time user management
GET /api/v1/admin/health          # System health monitoring
GET /api/v1/admin/sessions        # Active session tracking
GET /api/v1/admin/debug/logs      # System diagnostics
GET /api/v1/admin/data-integrity  # Database validation
```

**📖 Interactive API Docs**: `http://localhost:8000/docs`
**🔧 ReDoc Documentation**: `http://localhost:8000/redoc`

## 🚀 Why WealthPath AI Works Better

### **Simplified Architecture = Better Experience**
- **Instant Access**: No waiting for heavy ML models to load - your financial advisor is ready immediately
- **Always Online**: Lightweight design runs reliably on any cloud platform without resource constraints
- **Cost Efficient**: Optimized to run on free hosting tiers, so you don't pay premium prices for basic financial planning
- **Quick Setup**: Deploy in minutes, not hours - get your financial planning platform running today

### **Smart Design Choices**
- **Complete Financial Context**: Every AI response uses comprehensive user data (10 financial categories, 200+ data points)
- **Zero ML Dependencies**: SimpleVectorStore delivers fast performance without complex ML infrastructure  
- **Multi-LLM Diversity**: Intelligent fallback ensures provider diversity (prevents identical responses)
- **Production Monitoring**: Complete debug suite with LLM payload inspection and vector store health checks
- **Response Quality**: Trust Engine validates AI responses contain specific financial data, not generic advice

## 📋 Production Excellence Checklist

✅ **Multi-LLM Architecture**: OpenAI GPT-4 + Gemini Pro + Claude with intelligent fallback and diversity assurance  
✅ **Complete Financial Context**: All 10 data types synchronized to vector store, comprehensive LLM context integration
✅ **Response Validation**: Trust Engine scoring system ensures specific financial advice, not generic responses
✅ **Vector-Based Memory**: Conversation continuity with VectorChatMemoryService, zero database overhead
✅ **Advanced Debug Suite**: LLM payload inspection, vector store monitoring, multi-LLM health checks  
✅ **Financial Optimization**: Social Security scenarios, tax strategies, 401k optimization, benefits analysis
✅ **Real-Time Analytics**: Net worth tracking, cash flow analysis, savings rate, debt-to-income ratios
✅ **Performance Optimized**: <256MB per service, <50ms query response, 396MB Docker image
✅ **Production Monitoring**: Health checks, structured logging, admin dashboard with real-time metrics
✅ **Enterprise Security**: JWT with refresh tokens, role-based access, secure data handling  

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

MIT License - see LICENSE file for details.

---

## 🏆 **WealthPath AI: Enterprise Success Story**

**From 14.6GB Monolith to 396MB Multi-Service Architecture!**

*Advanced AI Financial Planning • Multi-LLM Integration • Enterprise Admin • Production-Ready*

### **Key Achievements**
- ✨ **97% Size Reduction**: 14.6GB → 396MB optimized deployment with zero ML dependencies
- 🧠 **Multi-LLM Excellence**: OpenAI GPT-4 + Gemini Pro + Claude with intelligent fallback and response diversity
- 🎯 **Complete Financial Context**: Every AI response uses comprehensive user data (10 categories, 200+ data points)
- 🔍 **Response Validation**: Trust Engine ensures specific financial advice, not generic responses  
- 💡 **Advanced Financial Planning**: Social Security optimization, tax strategies, 401k analysis, benefits planning
- ⚡ **Production Performance**: <50ms query response, <256MB memory, vector-based conversation memory
- 🛠️ **Enterprise Debug Suite**: LLM payload inspection, vector store monitoring, multi-provider health checks

**🚀 Deploy anywhere. Scale effortlessly. Monitor comprehensively.**

---

*WealthPath AI demonstrates how intelligent architecture choices can deliver enterprise-grade financial advisory capabilities with multi-LLM intelligence, complete financial context integration, and production-ready monitoring—all in a lightweight, cost-effective package optimized for modern cloud deployments.*

---

## 📚 Complete Documentation Suite

- **[README.md](./README.md)**: Comprehensive system overview and deployment guide
- **[CLAUDE.md](./CLAUDE.md)**: Development guidelines and project architecture  
- **[backend/docs/CHAT.md](./backend/docs/CHAT.md)**: Chat service architecture and multi-LLM integration
- **[backend/docs/VECTOR.md](./backend/docs/VECTOR.md)**: Vector database implementation and recent fixes
- **[backend/docs/DATA.md](./backend/docs/DATA.md)**: Data model documentation and PostgreSQL mapping

This documentation provides complete guidance for developers working on any aspect of the WealthPath AI system.