# WealthPath AI Vector Store Documentation

## Overview
The WealthPath AI system uses a lightweight JSON-based vector store (SimpleVectorStore) to provide intelligent financial data retrieval and context generation. This optimized architecture delivers fast queries without ML dependencies, supporting multi-LLM advisory services with comprehensive financial context.

**Key Features:**
- Zero ML dependencies (no ChromaDB, no embedding models)
- Real-time PostgreSQL synchronization
- Multi-user document isolation
- Fast semantic + keyword search
- Complete financial context for LLM advisory
- Debug endpoints for payload inspection

## Document Structure

The vector store maintains synchronized documents across **10 financial data types**, automatically synced from PostgreSQL:

### 1. Financial Summary (user_{id}_financial_summary)
**Purpose**: Comprehensive financial snapshot for LLM context  
**Category**: `summary`  
**Source**: `financial_summary_service.py`  
**Content**:
- Net Worth and asset distribution
- Monthly cash flow (income vs expenses)  
- Key financial ratios (savings rate, DTI)
- Retirement progress and timeline
- Emergency fund status
- **Recent Fix**: Now includes Social Security benefits in LLM payload

**Search Triggers**: "net worth", "financial summary", "overview", "snapshot", "cash flow"

### 2. Income Sources (user_{id}_income_breakdown)
**Purpose**: Detailed income categorization  
**Category**: `income`  
**Source**: `UserIncome` model  
**Content**:
- Primary income (salary, business, rental)
- Investment income and RSU vesting
- 401k contributions and employer matching
- Benefits and bonuses
- **Recent Fix**: 401k contribution limits now properly persisted

**Search Triggers**: "income", "salary", "earnings", "revenue", "401k", "rsu"

### 3. Expense Analysis (user_{id}_expense_breakdown)  
**Purpose**: Complete expense categorization with gap analysis  
**Category**: `expenses`  
**Source**: `UserExpense` model + calculated gaps  
**Content**:
- Itemized expenses by category (food, healthcare, utilities, etc.)
- Housing costs (mortgage, property tax, maintenance)
- **Recent Fix**: Added "Housing & Other" category to capture $3,881 expense gap
- Total monthly expenses: $7,481 (now complete in LLM payload)

**Search Triggers**: "expenses", "spending", "costs", "budget", "housing", "monthly expenses"

### 4. Asset Portfolio (user_{id}_assets)
**Purpose**: Investment and asset allocation analysis  
**Category**: `assets`  
**Source**: `UserAsset` model  
**Content**:
- Real Estate holdings and valuations
- Investment accounts (brokerage, retirement)
- Alternative investments (crypto, commodities)
- Cash and liquid assets
- Asset allocation percentages and diversification metrics

**Search Triggers**: "assets", "allocation", "portfolio", "investments", "diversification", "real estate"

### 5. Liability Management (user_{id}_liabilities)  
**Purpose**: Debt and liability tracking  
**Category**: `liabilities`  
**Source**: `UserLiability` model  
**Content**:
- Mortgage details (balance, rate, term)
- Credit card debt and utilization
- Student loans and auto loans
- Other debts and payment schedules
- Debt-to-income ratios and payoff strategies

**Search Triggers**: "debt", "liabilities", "mortgage", "loans", "payments", "credit cards"

### 6. Financial Goals (user_{id}_goals)
**Purpose**: Goal tracking and achievement planning  
**Category**: `goals`  
**Source**: `UserGoal` model  
**Content**:
- Retirement planning (target amount, timeline, progress)
- Short-term goals (emergency fund, vacation, major purchases)
- Education funding goals
- **Recent Fix**: Added standard planning assumptions (7% growth, 4% withdrawal, 80% rule)

**Search Triggers**: "goals", "retirement", "planning", "targets", "savings objectives"

### 7. Tax Information (user_{id}_tax_info)
**Purpose**: Tax planning and optimization data  
**Category**: `tax`  
**Source**: `UserTaxInfo` model  
**Content**:
- Filing status and tax year information
- Income sources and deductions
- Tax-advantaged account contributions
- **Recent Fix**: Save functionality now working properly

**Search Triggers**: "taxes", "deductions", "filing", "tax planning", "optimization"

### 8. Benefits & Insurance (user_{id}_benefits)
**Purpose**: Employee benefits and insurance coverage  
**Category**: `benefits`  
**Source**: `UserBenefit` + `UserInsurance` models  
**Content**:
- 401k matching and vesting schedules
- Health insurance and FSA contributions
- Life and disability insurance coverage
- Social Security benefit estimates
- **Recent Fix**: Max 401k contribution field now properly saved

**Search Triggers**: "benefits", "insurance", "401k", "health", "social security", "coverage"

### 9. Estate Planning (user_{id}_estate)
**Purpose**: Estate planning and document tracking  
**Category**: `estate`  
**Source**: `UserEstate` model  
**Content**:
- Will and trust documentation status
- Beneficiary designations across accounts
- Power of attorney arrangements
- Healthcare directives and end-of-life planning

**Search Triggers**: "estate", "will", "trust", "beneficiary", "power of attorney", "planning"

### 10. Chat Memory (user_{id}_chat_memory)
**Purpose**: Conversation context and user preferences  
**Category**: `chat_memory`  
**Source**: `chat_memory_service.py`  
**Content**:
- Recent conversation topics and context
- User communication preferences and patterns
- Financial sophistication level indicators
- Decision-making patterns and advisory preferences

**Search Triggers**: "conversation", "chat history", "memory", "context", "preferences"

## Technical Implementation

### SimpleVectorStore Architecture
```python
# Core Implementation: app/services/simple_vector_store.py
class SimpleVectorStore:
    storage_path: str = "/tmp/vector_store.json"
    documents: Dict[str, VectorDocument] = {}
    
    def search(self, query: str, user_id: int, limit: int = 5) -> List[VectorDocument]
    def add_document(self, doc_id: str, content: str, metadata: Dict) -> bool
    def update_document(self, doc_id: str, content: str, metadata: Dict) -> bool
```

### Storage Details
- **Storage Path**: `/tmp/vector_store.json` (in-memory + JSON persistence)
- **Format**: Structured JSON with document content and metadata
- **Search Method**: Hybrid scoring (keyword matching + content relevance)
- **Update Frequency**: Real-time via VectorSyncService
- **Memory Footprint**: <10MB for typical user datasets
- **Performance**: <50ms query response time

### Document Metadata Schema
```json
{
  "doc_id": "user_{user_id}_{document_type}",
  "content": "Full financial data content...",
  "metadata": {
    "user_id": 123,
    "document_type": "financial_summary|income|expenses|assets|liabilities|goals|tax|benefits|estate|chat_memory", 
    "category": "financial_data|chat_memory",
    "last_updated": "2025-01-07T10:30:00Z",
    "source_table": "PostgreSQL table name",
    "content_hash": "SHA256 for change detection"
  }
}
```

### Vector Sync Service
```python
# Automated synchronization: app/services/vector_sync_service.py
class VectorSyncService:
    def sync_user_data(user_id: int, db: Session) -> Dict
    def sync_all_users(db: Session) -> Dict
    def _clear_user_vector_data(user_id: int) -> bool
```

**Sync Process:**
1. Query all 10 financial data types from PostgreSQL
2. Generate structured content for each document type
3. Calculate content hash to detect changes
4. Update/insert documents in vector store
5. Persist to JSON file for durability

## Usage Examples

### LLM Advisory Integration
The vector store powers the CompleteFinancialContextService for multi-LLM advisory responses:

```python
# Complete financial context generation
from app.services.complete_financial_context_service import complete_financial_context_service

context = complete_financial_context_service.get_complete_context(
    user_id=123,
    query="Should I increase my 401k contribution?",
    insight_level="focused"
)

# Result: Comprehensive prompt with:
# - MANDATORY DATA: Net worth, cash flow, goals, benefits
# - FOCUSED DATA: 401k details, tax implications, retirement timeline  
# - STANDARD ASSUMPTIONS: 7% growth, 4% withdrawal, 80% rule
# - COMPLETE EXPENSE BREAKDOWN: Including housing gap analysis
```

### Multi-LLM Context Distribution
**Recent Fix**: All three LLM providers now receive identical, complete context:

```python
# LLM service routes to OpenAI, Gemini, or Claude with same payload:
llm_payload = {
    "system_prompt": "You are WealthPath AI, a certified financial advisor...",
    "user_message": "Complete context including all 10 financial data types...",
    "provider": "openai|gemini|claude",  # Properly registered clients
    "context_used": "Full financial profile with recent fixes"
}
```

### Debug and Monitoring
```python
# Debug endpoints for payload inspection:
GET /api/v1/debug/vector-contents/{user_id}   # All vector documents  
GET /api/v1/debug/last-llm-payload/{user_id}  # Complete LLM payload
POST /api/v1/debug/trigger-vector-sync/{user_id}  # Force rebuild

# Vector store health check:
GET /api/v1/debug/llm-clients  # Verify all providers registered
```

## Data Quality & Recent Fixes

### Critical Bug Fixes (Recent)
- ✅ **401k Contribution Persistence**: Added missing `max_401k_contribution` column to SQLAlchemy model
- ✅ **Tax Form Save Functionality**: Implemented complete save handler with API integration
- ✅ **Social Security in LLM Payload**: Added benefits data to mandatory context section
- ✅ **Complete Expense Breakdown**: Fixed $3,881 housing expense gap in LLM context
- ✅ **Multi-LLM System**: Fixed Claude client registration, all providers now working
- ✅ **Standard Financial Assumptions**: Added 7% growth, 4% withdrawal, 80% rule to prevent AI calculation avoidance

### Content Requirements
- ✅ Zero ML dependencies (pure Python + JSON)
- ✅ Complete financial information (10 document types)
- ✅ Real-time PostgreSQL synchronization
- ✅ User data isolation and security
- ✅ Gap analysis for missing data (e.g., expense categorization)

### Performance Metrics
- **Vector Store Size**: <10MB per user
- **Query Response Time**: <50ms average
- **Memory Usage**: <256MB total system
- **Docker Image**: 396MB (optimized)
- **Database Sync**: Real-time with change detection

## Troubleshooting & Debug Tools

### Debug Endpoints (Production Ready)
```bash
# Check vector store contents
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/debug/vector-contents/1

# Inspect LLM payload
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/debug/last-llm-payload/1

# Verify LLM client registration  
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/debug/llm-clients

# Force vector rebuild
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/debug/trigger-vector-sync/1?force_rebuild=true
```

### Common Issues & Solutions
1. **LLM Identical Responses**: Check client registration in `/debug/llm-clients`
2. **Missing Financial Data**: Use `/debug/vector-contents/{user_id}` to verify sync
3. **Expense Gap**: Verify "Housing & Other" category in breakdown
4. **401k Not Saving**: Check SQLAlchemy model has `max_401k_contribution` column
5. **Empty LLM Context**: Trigger vector sync with `force_rebuild=true`

### Monitoring Checklist
- ✅ Document count: 10 per user (all financial data types)
- ✅ LLM clients: 3 registered (OpenAI, Gemini, Claude)
- ✅ Context completeness: All mandatory data sections present
- ✅ Search performance: <50ms response time
- ✅ Memory usage: <256MB system total

## Integration Architecture

### Service Dependencies
```
CompleteFinancialContextService
├── SimpleVectorStore (document retrieval)
├── FinancialSummaryService (PostgreSQL sync)
├── VectorSyncService (real-time updates)
└── LLMService (multi-provider routing)
    ├── OpenAIClient
    ├── GeminiClient  
    └── ClaudeClient (fixed registration)
```

### Data Flow
```
PostgreSQL → VectorSyncService → SimpleVectorStore → CompleteFinancialContextService → LLMService → Multi-LLM Response
```

This architecture delivers fast, accurate, and comprehensive financial advisory responses while maintaining zero ML dependencies and optimal resource usage.