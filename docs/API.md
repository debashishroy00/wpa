# WealthPath AI - API Documentation

## Overview

WealthPath AI provides a comprehensive RESTful API for intelligent financial planning and advisory services. The API is built with FastAPI and includes automatic interactive documentation at `/docs` (Swagger UI) and `/redoc` (ReDoc).

**Base URL**: `http://localhost:8000` (development) or your production domain

**API Version**: v1 (all endpoints prefixed with `/api/v1`)

**Authentication**: JWT Bearer tokens required for most endpoints (see Authentication section)

## Table of Contents

1. [Authentication & User Management](#authentication--user-management)
2. [Financial Management](#financial-management)
3. [AI Advisory & Chat](#ai-advisory--chat)
4. [Goals & Planning](#goals--planning)
5. [User Profile & Benefits](#user-profile--benefits)
6. [Tax Planning](#tax-planning)
7. [Estate Planning](#estate-planning)
8. [Admin Dashboard](#admin-dashboard)
9. [Debug & Monitoring](#debug--monitoring)
10. [Health Checks](#health-checks)

---

## Authentication & User Management

### Register New User
```http
POST /api/v1/auth/register
```
**Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "full_name": "John Doe"
}
```
**Response**: `201 Created` - Returns user details

### Login
```http
POST /api/v1/auth/login
```
**Body**:
```json
{
  "username": "user@example.com",
  "password": "SecurePassword123!"
}
```
**Response**: `200 OK` - Returns access and refresh tokens
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Refresh Token
```http
POST /api/v1/auth/refresh
```
**Headers**: `Authorization: Bearer {refresh_token}`
**Response**: `200 OK` - Returns new access and refresh tokens

### Get Current User
```http
GET /api/v1/auth/me
```
**Headers**: `Authorization: Bearer {access_token}`
**Response**: `200 OK` - Returns current user details

### Logout
```http
POST /api/v1/auth/logout
```
**Headers**: `Authorization: Bearer {access_token}`
**Response**: `200 OK` - Invalidates tokens

### Change Password
```http
POST /api/v1/auth/change-password
```
**Headers**: `Authorization: Bearer {access_token}`
**Body**:
```json
{
  "current_password": "OldPassword123!",
  "new_password": "NewPassword456!"
}
```

### Password Reset Request
```http
POST /api/v1/auth/password-reset-request
```
**Body**:
```json
{
  "email": "user@example.com"
}
```

### Password Reset
```http
POST /api/v1/auth/password-reset
```
**Body**:
```json
{
  "token": "reset-token-from-email",
  "new_password": "NewPassword789!"
}
```

---

## Financial Management

### Get Financial Summary
```http
GET /api/v1/financial/summary
```
**Headers**: `Authorization: Bearer {access_token}`
**Response**: Complete financial overview including:
- Net worth
- Monthly cash flow
- Asset allocation
- Debt-to-income ratio
- Emergency fund coverage
- Savings rate

### Get All Financial Entries
```http
GET /api/v1/financial/entries
```
**Headers**: `Authorization: Bearer {access_token}`
**Query Parameters**:
- `category`: Filter by category (optional)
- `skip`: Pagination offset (default: 0)
- `limit`: Pagination limit (default: 100)

### Create Financial Entry
```http
POST /api/v1/financial/entries
```
**Headers**: `Authorization: Bearer {access_token}`
**Body**:
```json
{
  "category": "INCOME",
  "subcategory": "salary",
  "entry_type": "income",
  "amount": 5000.00,
  "frequency": "monthly",
  "description": "Monthly salary",
  "date": "2024-01-01"
}
```

### Update Financial Entry
```http
PUT /api/v1/financial/entries/{entry_id}
```
**Headers**: `Authorization: Bearer {access_token}`
**Body**: Same as create entry

### Delete Financial Entry
```http
DELETE /api/v1/financial/entries/{entry_id}
```
**Headers**: `Authorization: Bearer {access_token}`

### Get Categorized Financial Data
```http
GET /api/v1/financial/entries/categorized
```
**Headers**: `Authorization: Bearer {access_token}`
**Response**: Financial data organized by categories

### Get Financial Accounts
```http
GET /api/v1/financial/accounts
```
**Headers**: `Authorization: Bearer {access_token}`
**Response**: List of all financial accounts

### Get Portfolio Allocation
```http
GET /api/v1/financial/portfolio-allocation
```
**Headers**: `Authorization: Bearer {access_token}`
**Response**: Asset allocation breakdown

### Get Net Worth History
```http
GET /api/v1/financial/net-worth/history
```
**Headers**: `Authorization: Bearer {access_token}`
**Response**: Historical net worth snapshots

### Create Net Worth Snapshot
```http
POST /api/v1/financial/net-worth/snapshot
```
**Headers**: `Authorization: Bearer {access_token}`

### Get Cash Flow Analysis
```http
GET /api/v1/financial/cash-flow/{user_id}
```
**Headers**: `Authorization: Bearer {access_token}`
**Note**: Admin only or own user_id

### Financial Calculators

#### Debt Payoff Calculator
```http
POST /api/v1/financial/calculator/payoff
```

#### Compare Debt Strategies
```http
POST /api/v1/financial/calculator/compare-strategies
```

#### Debt Avalanche Calculator
```http
POST /api/v1/financial/calculator/debt-avalanche
```

#### Mortgage vs Investment Calculator
```http
POST /api/v1/financial/calculator/mortgage-vs-invest
```

#### Emergency Fund Calculator
```http
POST /api/v1/financial/calculator/emergency-fund
```

#### Retirement Projection
```http
POST /api/v1/financial/calculator/retirement-projection
```

### Sync Operations

#### Sync to Vector Database
```http
POST /api/v1/financial/sync/vector-db
```
**Headers**: `Authorization: Bearer {access_token}`

#### Complete Sync
```http
POST /api/v1/financial/sync/complete
```
**Headers**: `Authorization: Bearer {access_token}`

#### Get Sync Status
```http
GET /api/v1/financial/sync/status
```
**Headers**: `Authorization: Bearer {access_token}`

---

## AI Advisory & Chat

### Send Chat Message (with Memory)
```http
POST /api/v1/chat/message
```
**Headers**: `Authorization: Bearer {access_token}`
**Body**:
```json
{
  "message": "What's my current financial situation?",
  "session_id": "optional-session-id",
  "context": {
    "include_financial_data": true,
    "include_goals": true
  }
}
```
**Response**: AI-generated response with financial context

### Intelligent Chat (Enhanced)
```http
POST /api/v1/chat/intelligent
```
**Headers**: `Authorization: Bearer {access_token}`
**Body**:
```json
{
  "message": "Help me plan for retirement",
  "insight_level": "comprehensive",
  "include_projections": true
}
```

### Get Chat Sessions
```http
GET /api/v1/chat/sessions/{user_id}
```
**Headers**: `Authorization: Bearer {access_token}`

### Get Session Messages
```http
GET /api/v1/chat/session/{session_id}/messages
```
**Headers**: `Authorization: Bearer {access_token}`

### Create New Chat Session
```http
POST /api/v1/chat/sessions/new
```
**Headers**: `Authorization: Bearer {access_token}`
**Body**:
```json
{
  "name": "Retirement Planning Discussion"
}
```

### Delete Chat Session
```http
DELETE /api/v1/chat/sessions/{session_id}
```
**Headers**: `Authorization: Bearer {access_token}`

### Generate Advisory Report
```http
POST /api/v1/advisory/generate
```
**Headers**: `Authorization: Bearer {access_token}`
**Body**:
```json
{
  "topic": "retirement_planning",
  "include_scenarios": true,
  "time_horizon": "30_years"
}
```

### Compare Financial Scenarios
```http
POST /api/v1/advisory/compare-scenarios
```
**Headers**: `Authorization: Bearer {access_token}`
**Body**:
```json
{
  "scenarios": [
    {
      "name": "Conservative",
      "parameters": {...}
    },
    {
      "name": "Aggressive",
      "parameters": {...}
    }
  ]
}
```

### Search Knowledge Base
```http
GET /api/v1/advisory/knowledge-base/search
```
**Query Parameters**:
- `query`: Search query
- `limit`: Number of results (default: 5)

### Get Advisory Templates
```http
GET /api/v1/advisory/templates
```
**Response**: List of available advisory templates

---

## Goals & Planning

### Get All Goals
```http
GET /api/v1/goals
```
**Headers**: `Authorization: Bearer {access_token}`

### Create Goal
```http
POST /api/v1/goals
```
**Headers**: `Authorization: Bearer {access_token}`
**Body**:
```json
{
  "name": "Buy a House",
  "description": "Save for down payment",
  "goal_type": "savings",
  "target_amount": 100000,
  "target_date": "2026-01-01",
  "priority": "high",
  "monthly_contribution": 2000
}
```

### Get Goal Details
```http
GET /api/v1/goals/{goal_id}
```
**Headers**: `Authorization: Bearer {access_token}`

### Update Goal
```http
PUT /api/v1/goals/{goal_id}
```
**Headers**: `Authorization: Bearer {access_token}`
**Body**: Same as create goal

### Delete Goal
```http
DELETE /api/v1/goals/{goal_id}
```
**Headers**: `Authorization: Bearer {access_token}`

### Get Goal Progress
```http
GET /api/v1/goals/{goal_id}/progress
```
**Headers**: `Authorization: Bearer {access_token}`
**Response**: Progress metrics and projections

### Get Goal Analytics
```http
GET /api/v1/goals/analytics/summary
```
**Headers**: `Authorization: Bearer {access_token}`
**Response**: Overall goals performance metrics

### Analyze Goal Scenarios
```http
GET /api/v1/goals/{goal_id}/scenarios
```
**Headers**: `Authorization: Bearer {access_token}`
**Response**: What-if scenarios for goal achievement

### Analyze Goal Feasibility
```http
POST /api/v1/goals/{goal_id}/analyze
```
**Headers**: `Authorization: Bearer {access_token}`

---

## User Profile & Benefits

### Get User Profile
```http
GET /api/v1/profile/profile
```
**Headers**: `Authorization: Bearer {access_token}`

### Create/Update Profile
```http
POST /api/v1/profile/profile
```
**Headers**: `Authorization: Bearer {access_token}`
**Body**:
```json
{
  "date_of_birth": "1985-01-01",
  "occupation": "Software Engineer",
  "annual_income": 150000,
  "filing_status": "married_filing_jointly",
  "state": "CA",
  "dependents": 2
}
```

### Partial Update Profile
```http
PATCH /api/v1/profile/profile
```
**Headers**: `Authorization: Bearer {access_token}`
**Body**: Partial profile fields

### Get Complete Profile
```http
GET /api/v1/profile/complete-profile
```
**Headers**: `Authorization: Bearer {access_token}`
**Response**: All profile data including family, benefits, tax info

### Family Members

#### Get Family Members
```http
GET /api/v1/profile/family
```

#### Add Family Member
```http
POST /api/v1/profile/family
```
**Body**:
```json
{
  "name": "Jane Doe",
  "relationship": "spouse",
  "date_of_birth": "1987-03-15"
}
```

#### Update Family Member
```http
PATCH /api/v1/profile/family/{member_id}
```

#### Delete Family Member
```http
DELETE /api/v1/profile/family/{member_id}
```

### Benefits Management

#### Get Benefits
```http
GET /api/v1/profile/benefits
```

#### Add Benefit
```http
POST /api/v1/profile/benefits
```
**Body**:
```json
{
  "benefit_type": "401k",
  "employer_name": "Tech Corp",
  "value": 150000,
  "employer_match_percentage": 6,
  "vesting_schedule": "3_year_cliff"
}
```

#### Update Benefit
```http
PATCH /api/v1/profile/benefits/{benefit_id}
```

#### Delete Benefit
```http
DELETE /api/v1/profile/benefits/{benefit_id}
```

### Social Security Analysis
```http
POST /api/v1/profile/social-security
```
**Headers**: `Authorization: Bearer {access_token}`
**Body**:
```json
{
  "estimated_benefit_at_fra": 3000,
  "claiming_age": 67,
  "include_spouse": true
}
```

### 401k Optimization
```http
POST /api/v1/profile/401k
```
**Headers**: `Authorization: Bearer {access_token}`
**Body**:
```json
{
  "current_balance": 250000,
  "annual_contribution": 22500,
  "employer_match": 6,
  "expected_return": 7
}
```

---

## Tax Planning

### Tax Health Check
```http
GET /api/v1/tax/health
```
**Headers**: `Authorization: Bearer {access_token}`

### Analyze Tax Situation
```http
POST /api/v1/tax/analyze
```
**Headers**: `Authorization: Bearer {access_token}`
**Body**:
```json
{
  "year": 2024,
  "include_projections": true
}
```

### Tax Strategy Recommendations
```http
POST /api/v1/tax/strategy/{strategy_type}
```
**Headers**: `Authorization: Bearer {access_token}`
**Strategy Types**:
- `backdoor_roth`
- `mega_backdoor_roth`
- `tax_loss_harvesting`
- `bunching`
- `retirement_optimization`

### Calculate Marginal Tax Rate
```http
POST /api/v1/tax/calculate/marginal-rate
```

### Calculate Itemization Benefits
```http
POST /api/v1/tax/calculate/itemization
```

### Calculate Bunching Strategy
```http
POST /api/v1/tax/calculate/bunching
```

### Calculate Retirement Tax Optimization
```http
POST /api/v1/tax/calculate/retirement-optimization
```

### Calculate Tax Loss Harvesting
```http
POST /api/v1/tax/calculate/tax-loss-harvesting
```

### Calculate Quarterly Payments
```http
POST /api/v1/tax/calculate/quarterly-payments
```

### Get Tax Opportunities
```http
GET /api/v1/tax/opportunities
```
**Headers**: `Authorization: Bearer {access_token}`

### Get Tax Insights
```http
GET /api/v1/tax/insights
```
**Headers**: `Authorization: Bearer {access_token}`

### Get/Update Tax Information
```http
GET /api/v1/profile/tax-info
POST /api/v1/profile/tax-info
PATCH /api/v1/profile/tax-info/{tax_id}
DELETE /api/v1/profile/tax-info/{tax_id}
```

---

## Estate Planning

### Get Estate Documents
```http
GET /api/v1/estate/documents
```
**Headers**: `Authorization: Bearer {access_token}`

### Get Estate Planning Summary
```http
GET /api/v1/estate/summary
```
**Headers**: `Authorization: Bearer {access_token}`
**Response**: Overview of estate planning status

### Get Document Details
```http
GET /api/v1/estate/documents/{document_id}
```

### Create Estate Document
```http
POST /api/v1/estate/documents
```
**Body**:
```json
{
  "document_type": "will",
  "name": "Last Will and Testament",
  "status": "completed",
  "last_updated": "2024-01-01",
  "location": "Safe deposit box",
  "notes": "Updated after second child"
}
```

### Update Estate Document
```http
PUT /api/v1/estate/documents/{document_id}
```

### Delete Estate Document
```http
DELETE /api/v1/estate/documents/{document_id}
```

### Get Document Types
```http
GET /api/v1/estate/document-types
```
**Response**: List of available document types

### Estate Planning Gap Analysis
```http
GET /api/v1/estate/gap-analysis
```
**Headers**: `Authorization: Bearer {access_token}`
**Response**: Missing documents and recommendations

---

## Admin Dashboard
**Note**: All admin endpoints require authentication as `debashishroy@gmail.com`

### Get All Users
```http
GET /api/v1/admin/users
```
**Query Parameters**:
- `skip`: Pagination offset
- `limit`: Pagination limit

### Get User Details
```http
GET /api/v1/admin/users/{user_id}
```

### Get Active Sessions
```http
GET /api/v1/admin/sessions
```

### System Health Check
```http
GET /api/v1/admin/health
```
**Response**: Comprehensive system health status

### Force User Logout
```http
POST /api/v1/admin/force-logout/{user_id}
```

### Clear User Cache
```http
DELETE /api/v1/admin/user-cache/{user_id}
```

### Revoke User Tokens
```http
DELETE /api/v1/admin/user-tokens/{user_id}
```

### Clear All Cache
```http
POST /api/v1/admin/clear-cache
```

### Get System Logs
```http
GET /api/v1/admin/logs
```
**Query Parameters**:
- `level`: Log level filter (debug, info, warning, error)
- `limit`: Number of log entries

### Get Debug Logs
```http
GET /api/v1/admin/debug/logs
```

### Get Performance Metrics
```http
GET /api/v1/admin/debug/performance
```

### Data Integrity Check
```http
GET /api/v1/admin/data-integrity
```

---

## Debug & Monitoring

### Get Vector Store Contents
```http
GET /api/v1/debug/vector-contents/{user_id}
```
**Headers**: `Authorization: Bearer {access_token}`
**Response**: User's vector store documents and embeddings

### Get Last LLM Payload
```http
GET /api/v1/debug/last-llm-payload/{user_id}
```
**Headers**: `Authorization: Bearer {access_token}`
**Response**: Last LLM request/response for debugging

### Clear LLM Payloads
```http
POST /api/v1/debug/clear-payloads
```
**Headers**: `Authorization: Bearer {access_token}`

### Trigger Vector Store Sync
```http
POST /api/v1/debug/trigger-vector-sync/{user_id}
```
**Headers**: `Authorization: Bearer {access_token}`

### Check LLM Clients Status
```http
GET /api/v1/debug/llm-clients
```
**Response**: Status of all configured LLM providers

### Get Financial Summary Debug
```http
GET /api/v1/debug/financial-summary/{user_id}
```
**Headers**: `Authorization: Bearer {access_token}`

### Chat Memory Status
```http
GET /api/v1/debug/memory-status/{user_id}
```

### Data Pipeline Debug
```http
GET /api/v1/debug/data-pipeline/{user_id}
```

---

## Health Checks

### Basic Health Check
```http
GET /api/v1/health
```
**Response**: `200 OK` - Service is running

### Live Health Check
```http
GET /api/v1/health/live
```
**Response**: Basic liveness check

### Readiness Check
```http
GET /api/v1/health/ready
```
**Response**: Checks if service is ready to handle requests
- Database connectivity
- Redis connectivity
- LLM provider status

### Deep Health Check
```http
GET /api/v1/health/deep
```
**Response**: Comprehensive health check including:
- Database status and metrics
- Redis status
- LLM providers status
- Memory usage
- Disk usage
- Service dependencies

### Startup Check
```http
GET /api/v1/health/startup
```
**Response**: Startup status and configuration

### Metrics Endpoint
```http
GET /api/v1/health/metrics
```
**Response**: Prometheus-compatible metrics

---

## Error Responses

All endpoints follow a consistent error response format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

## Rate Limiting

The API implements rate limiting to prevent abuse:
- **Default**: 100 requests per minute per user
- **Chat endpoints**: 20 requests per minute per user
- **Admin endpoints**: No rate limiting

## Authentication Flow

1. **Register** or **Login** to receive access and refresh tokens
2. Include access token in `Authorization: Bearer {token}` header
3. Access token expires in 15 minutes (configurable)
4. Use refresh token to get new access token
5. Refresh token expires in 7 days (configurable)

## WebSocket Support

Real-time features are available via WebSocket connections:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/{user_id}');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Handle real-time updates
};
```

## SDK Examples

### Python
```python
import requests

# Login
response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    data={"username": "user@example.com", "password": "password"}
)
tokens = response.json()

# Make authenticated request
headers = {"Authorization": f"Bearer {tokens['access_token']}"}
financial_summary = requests.get(
    "http://localhost:8000/api/v1/financial/summary",
    headers=headers
)
```

### JavaScript/TypeScript
```typescript
// Using axios
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
});

// Login
const { data: tokens } = await api.post('/auth/login', {
  username: 'user@example.com',
  password: 'password'
});

// Set auth header
api.defaults.headers.common['Authorization'] = `Bearer ${tokens.access_token}`;

// Get financial summary
const { data: summary } = await api.get('/financial/summary');
```

## Testing the API

### Using curl
```bash
# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@gmail.com&password=password123"

# Get financial summary (replace TOKEN with actual token)
curl -X GET "http://localhost:8000/api/v1/financial/summary" \
  -H "Authorization: Bearer TOKEN"
```

### Using Postman
1. Import the OpenAPI spec from `http://localhost:8000/openapi.json`
2. Set up environment variables for base URL and tokens
3. Use the pre-built collection to test all endpoints

## API Versioning

The API uses URL versioning. Current version: `v1`

Future versions will be available at `/api/v2/`, `/api/v3/`, etc.

## Support

For API issues or questions:
- Check the interactive docs at `/docs`
- Review error messages for debugging hints
- Check health endpoints for system status
- Contact admin for access issues

---

**Last Updated**: January 2025
**API Version**: 1.0.0
**Documentation Version**: 1.0.0