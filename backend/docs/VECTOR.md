# WealthPath AI Vector Store Documentation

## Overview
The vector store contains 7 core documents providing structured financial data and conversation memory for intelligent retrieval and analysis. This clean, organized structure replaces the previous chaotic system that contained test data pollution and malformed documents.

## Document Structure

### 1. Financial Summary (user_1_financial_summary)
**Purpose**: High-level financial snapshot  
**Category**: `summary`  
**Content**:
- Net Worth: $2,565,545
- Monthly Income: $17,744
- Monthly Expenses: $7,481
- Monthly Surplus: $10,263
- Savings Rate: 57.8%
- Debt-to-Income: 13.9%
- Housing Cost Ratio: 20.7%

**Search Triggers**: "net worth", "financial summary", "overview", "snapshot"

### 2. Income Breakdown (user_1_income_breakdown)
**Purpose**: Categorized income sources  
**Category**: `income`  
**Content**:
- Manual Entry: $17,744
  - Salary: $12,000
  - 401K Contribution: $2,400
  - Company RSU: $2,500
  - Rental Income: $844
- Total Monthly Income: $17,744

**Search Triggers**: "income", "salary", "earnings", "revenue sources"

### 3. Expense Breakdown (user_1_expense_breakdown)
**Purpose**: Detailed expense categorization  
**Category**: `expenses`  
**Content**:
- Food: $1,400
  - Groceries: $600
  - Restaurants: $800
- Healthcare: $550
  - Doctors: $200
  - Gym: $350
- Utilities: $1,000
  - Water: $100
  - All utilities: $900
- Transportation: $500
- Housing: $2,881
  - Home Improvement: $200
  - Property Tax: $517
- Personal: $1,000
  - General Merchandise: $800
  - Entertainment: $200
- Total Monthly Expenses: $7,481

**Search Triggers**: "expenses", "spending", "costs", "budget", "categories"

### 4. Asset Allocation (user_1_asset_allocation)
**Purpose**: Portfolio composition and distribution  
**Category**: `assets`  
**Content**:
- Real Estate: 50.3% ($1,449,706)
- Investments: 25.7% ($741,000)
- Retirement: 10.8% ($310,216)
- Alternative: 4.5% ($130,000 Bitcoin)
- Cash: 3.6% ($104,557)
- Other: 5.0% ($144,348)
- Total Assets: $2,879,827

**Search Triggers**: "assets", "allocation", "portfolio", "investments", "diversification"

### 5. Financial Goals (user_1_financial_goals)
**Purpose**: Goal tracking and progress monitoring  
**Category**: `goals`  
**Content**:
- Retirement Goal: $3,500,000
  - Current Progress: 66.2% ($2,317,896)
  - Years to Goal: 10.3
  - Target Achievement Age: 64
- College Fund: $100,000
  - Current Progress: 90% ($90,000)
  - Years to Goal: 2
- Emergency Fund: $104,557
  - Target: 6 months expenses ($44,886)
  - Current Status: ✅ Adequate

**Search Triggers**: "goals", "retirement", "college", "targets", "progress"

### 6. Estate & Insurance (user_1_estate_insurance)
**Purpose**: Protection planning and estate documentation status  
**Category**: `estate_insurance`  
**Content**:
**Estate Planning**:
- Beneficiary Designation: Current
- Healthcare Directive: Current
- Will: Current
- Power of Attorney: Current

**Insurance Coverage**:
- Life Insurance: $1,000,000
  - Annual Premium: $1,400
- Home Insurance: $800,000
  - Annual Premium: $1,300

**Search Triggers**: "estate", "insurance", "will", "beneficiary", "coverage"

## Technical Implementation

### Storage Details
- **Storage Path**: `/tmp/vector_store.json`
- **Format**: JSON with embedded metadata
- **Search Method**: Cosine similarity + keyword matching
- **Update Frequency**: Real-time with database changes

### Document Metadata
Each document includes:
```json
{
  "category": "summary|income|expenses|assets|goals|estate_insurance",
  "user_id": 1,
  "last_updated": "ISO timestamp"
}
```

### Search Performance
- **Query Response Time**: <100ms
- **Relevance Scoring**: Hybrid (semantic + keyword)
- **Result Ranking**: Score-based with category preference

## Usage Examples

### Chat Integration
The vector store integrates with the CompleteFinancialContextService to provide:

```python
# Example: Expense categorization query
query = "What are my monthly expenses by category?"
results = vector_store.search(query, user_id=1)
# Returns: user_1_expense_breakdown with detailed categorization

# Example: Financial overview query  
query = "Show me my financial summary"
results = vector_store.search(query, user_id=1)
# Returns: user_1_financial_summary with key metrics
```

### Query Optimization
- **Specific queries**: Return single most relevant document
- **General queries**: Return multiple documents ranked by relevance
- **Category filtering**: Use metadata for precise targeting

## Data Quality Standards

### Content Requirements
- ✅ No test data or placeholder content
- ✅ Complete financial information (no truncation)
- ✅ Consistent formatting and structure
- ✅ Real-time accuracy with database

### Maintenance Schedule
- **Daily**: Automated content updates from database
- **Weekly**: Document structure validation
- **Monthly**: Performance optimization and cleanup

## Troubleshooting

### Common Issues
1. **Empty Results**: Check document indexing and search terms
2. **Outdated Data**: Verify database sync processes
3. **Relevance Issues**: Review search algorithms and metadata

### Monitoring
- Document count: Should always be 6 core documents
- Content validation: Regular checks for data integrity
- Search performance: Query response time monitoring

## Integration Points

### Connected Services
- **CompleteFinancialContextService**: Real-time data sync
- **Chat Endpoints**: Query processing and response generation
- **Financial Summary Service**: Source data provider
- **Vector Sync Service**: Automated updates

This structured approach ensures consistent, accurate financial data retrieval for enhanced user experience and intelligent advisory capabilities.