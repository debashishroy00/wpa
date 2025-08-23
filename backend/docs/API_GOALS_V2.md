# Goals V2 API Documentation

## Overview

The Goals V2 API provides comprehensive financial goal management with versioned goal tracking, audit trails, and conflict analysis. This is a major enhancement over the original goal system, providing enterprise-grade features for WealthPath AI.

## Authentication

All endpoints require authentication via Bearer token:
```
Authorization: Bearer <access_token>
```

## Base URL

All endpoints are prefixed with `/api/v1`

---

## Goals Management

### Create Goal
Creates a new financial goal with validation and audit trail.

**POST** `/goals`

**Request Body:**
```json
{
  "category": "retirement",
  "name": "Retirement Fund",
  "description": "Long-term retirement savings",
  "target_amount": 1000000.00,
  "target_date": "2055-12-31",
  "priority": 1,
  "params": {
    "retirement_age": 65,
    "annual_spending": 50000,
    "current_age": 30
  }
}
```

**Response:** `201 Created`
```json
{
  "goal_id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": 1,
  "category": "retirement",
  "name": "Retirement Fund",
  "description": "Long-term retirement savings",
  "target_amount": 1000000.00,
  "target_date": "2055-12-31",
  "priority": 1,
  "status": "active",
  "params": {...},
  "progress_percentage": 0.00,
  "current_amount": 0.00,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Get Goals
Retrieves user's goals with optional filtering.

**GET** `/goals?status=active&category=retirement&limit=10&offset=0`

**Query Parameters:**
- `status` (optional): Filter by status (active, achieved, cancelled, paused)
- `category` (optional): Filter by category
- `limit` (optional): Number of results (1-100, default 50)
- `offset` (optional): Pagination offset (default 0)

**Response:** `200 OK`
```json
[
  {
    "goal_id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Retirement Fund",
    "category": "retirement",
    "target_amount": 1000000.00,
    "progress_percentage": 15.50,
    "current_amount": 155000.00,
    "status": "active",
    "priority": 1,
    "target_date": "2055-12-31",
    "days_until_target": 11323
  }
]
```

### Get Goal Details
Retrieves detailed information for a specific goal.

**GET** `/goals/{goal_id}`

**Response:** `200 OK`
```json
{
  "goal_id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": 1,
  "category": "retirement",
  "name": "Retirement Fund",
  "description": "Long-term retirement savings",
  "target_amount": 1000000.00,
  "target_date": "2055-12-31",
  "priority": 1,
  "status": "active",
  "params": {
    "retirement_age": 65,
    "annual_spending": 50000,
    "current_age": 30
  },
  "progress_percentage": 15.50,
  "current_amount": 155000.00,
  "days_until_target": 11323,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Update Goal
Updates an existing goal with audit trail.

**PUT** `/goals/{goal_id}`

**Request Body:**
```json
{
  "name": "Updated Retirement Fund",
  "target_amount": 1200000.00,
  "change_reason": "Increased target due to inflation"
}
```

**Response:** `200 OK` (Updated goal object)

### Delete Goal
Soft-deletes a goal (sets status to cancelled).

**DELETE** `/goals/{goal_id}`

**Response:** `200 OK`
```json
{
  "message": "Goal deleted successfully"
}
```

---

## Progress Tracking

### Record Progress
Records progress towards a goal.

**POST** `/goals/{goal_id}/progress`

**Request Body:**
```json
{
  "current_amount": 50000.00,
  "notes": "Monthly contribution"
}
```

**Response:** `201 Created`
```json
{
  "progress_id": "123e4567-e89b-12d3-a456-426614174001",
  "goal_id": "123e4567-e89b-12d3-a456-426614174000",
  "current_amount": 50000.00,
  "percentage_complete": 5.00,
  "notes": "Monthly contribution",
  "source": "manual",
  "recorded_at": "2024-01-01T00:00:00Z"
}
```

### Get Progress History
Retrieves progress history for a goal.

**GET** `/goals/{goal_id}/progress?limit=10`

**Response:** `200 OK`
```json
[
  {
    "progress_id": "123e4567-e89b-12d3-a456-426614174001",
    "current_amount": 50000.00,
    "percentage_complete": 5.00,
    "notes": "Monthly contribution",
    "source": "manual",
    "recorded_at": "2024-01-01T00:00:00Z"
  }
]
```

---

## Analysis & Reporting

### Goals Summary
Provides an overview of all user goals.

**GET** `/goals/summary`

**Response:** `200 OK`
```json
{
  "active_goals": 3,
  "achieved_goals": 1,
  "total_target": 1500000.00,
  "nearest_deadline": "2030-12-31",
  "average_progress": 22.5
}
```

### Goal Conflicts Analysis
Analyzes potential conflicts between goals.

**GET** `/goals/analysis/conflicts`

**Response:** `200 OK`
```json
[
  {
    "goal1_id": "123e4567-e89b-12d3-a456-426614174000",
    "goal1_name": "Retirement Fund",
    "goal2_id": "123e4567-e89b-12d3-a456-426614174001",
    "goal2_name": "College Fund",
    "conflict_type": "timeline_overlap",
    "severity": "medium"
  }
]
```

### Goal History
Retrieves complete audit history for a goal.

**GET** `/goals/{goal_id}/history`

**Response:** `200 OK`
```json
[
  {
    "history_id": "123e4567-e89b-12d3-a456-426614174002",
    "goal_id": "123e4567-e89b-12d3-a456-426614174000",
    "changed_by": "user@example.com",
    "change_reason": "Updated target amount",
    "old_values": {"target_amount": 1000000.00},
    "new_values": {"target_amount": 1200000.00},
    "changed_at": "2024-01-01T00:00:00Z"
  }
]
```

---

## Batch Operations

### Batch Update Goals
Updates multiple goals at once.

**PUT** `/goals/batch`

**Request Body:**
```json
{
  "goal_ids": [
    "123e4567-e89b-12d3-a456-426614174000",
    "123e4567-e89b-12d3-a456-426614174001"
  ],
  "updates": {
    "priority": 2,
    "status": "paused"
  },
  "batch_reason": "Temporary pause due to market conditions"
}
```

**Response:** `200 OK` (Array of updated goal objects)

---

## User Preferences

### Get Preferences
Retrieves user's goal preferences.

**GET** `/preferences`

**Response:** `200 OK`
```json
{
  "preference_id": "123e4567-e89b-12d3-a456-426614174003",
  "user_id": 1,
  "risk_tolerance": "moderate",
  "investment_experience": "intermediate",
  "time_horizon": "long_term",
  "liquidity_needs": "low",
  "goal_prioritization": "balanced",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Update Preferences
Updates user's goal preferences.

**PUT** `/preferences`

**Request Body:**
```json
{
  "risk_tolerance": "aggressive",
  "investment_experience": "advanced",
  "time_horizon": "long_term",
  "liquidity_needs": "medium"
}
```

**Response:** `200 OK` (Updated preferences object)

---

## Reference Data

### Goal Categories
Retrieves available goal categories with descriptions.

**GET** `/categories`

**Response:** `200 OK`
```json
{
  "retirement": {
    "name": "Retirement",
    "description": "Long-term retirement savings and planning",
    "required_params": ["retirement_age", "annual_spending", "current_age"],
    "typical_timeline": "20-40 years"
  },
  "education": {
    "name": "Education",
    "description": "College, graduate school, or professional education",
    "required_params": ["degree_type", "institution_type", "start_year"],
    "typical_timeline": "1-10 years"
  }
}
```

### Goal Templates
Retrieves pre-configured goal templates.

**GET** `/templates`

**Response:** `200 OK`
```json
[
  {
    "name": "Retirement at 65",
    "category": "retirement",
    "description": "Standard retirement goal for age 65",
    "template_params": {
      "retirement_age": 65,
      "annual_spending": 50000,
      "inflation_rate": 0.03
    }
  }
]
```

---

## Error Handling

### Error Response Format
```json
{
  "detail": "Error message",
  "type": "validation_error",
  "errors": [
    {
      "loc": ["body", "target_amount"],
      "msg": "Target amount must be positive",
      "type": "value_error"
    }
  ]
}
```

### HTTP Status Codes
- `200 OK`: Success
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation errors
- `500 Internal Server Error`: Server error

---

## Goal Categories

### Retirement
**Required Parameters:**
- `retirement_age`: Target retirement age
- `annual_spending`: Expected annual spending in retirement
- `current_age`: Current age of the user

### Education
**Required Parameters:**
- `degree_type`: Type of degree (undergraduate, graduate, professional)
- `institution_type`: Type of institution (public, private)
- `start_year`: Expected start year

### Real Estate
**Required Parameters:**
- `property_type`: Type of property (primary_residence, investment, vacation)
- `down_payment_percentage`: Down payment percentage

### Emergency Fund
**Required Parameters:**
- `months_of_expenses`: Number of months of expenses to save

### Business
**Required Parameters:**
- `business_type`: Type of business venture

### Travel
**Required Parameters:**
- `destination`: Travel destination
- `duration`: Trip duration

### Debt Payoff
**Required Parameters:**
- `debt_type`: Type of debt (credit_card, student_loan, mortgage)
- `current_balance`: Current outstanding balance

### Major Purchase
**Required Parameters:**
- `item_type`: Type of item being purchased

---

## Database Schema

The Goals V2 system uses the following key tables:

- **goals**: Primary goal information with JSONB parameters
- **goals_history**: Complete audit trail of all changes
- **goal_progress**: Progress tracking over time
- **goal_relationships**: Dependencies between goals
- **user_preferences**: User-specific goal preferences

All tables include automatic audit triggers and UUID primary keys for enhanced security and tracking.