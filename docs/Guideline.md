 WealthPath AI Development Best Practices Guide
For Claude Code and Future Development Assistants
CRITICAL: Understand the Existing Architecture First

1. CORE ARCHITECTURAL PATTERNS
LLM Service Pattern
python# ✅ CORRECT - Use global instance
from app.services.llm_service import llm_service

# ❌ WRONG - Never create new instances
llm = LLMService()  # This breaks everything
Service Initialization Pattern
python# ✅ CORRECT - Services use dependency injection
class MyService:
    def __init__(self, db: Session):
        self.db = db
        # Use existing services, don't create new ones

# ❌ WRONG - Creating service chains
class MyService:
    def __init__(self):
        self.llm = LLMService()  # Creates isolated instance
        self.db = SessionLocal()  # Bypasses connection pool
Database Pattern
python# ✅ CORRECT - Use passed session
def my_function(db: Session):
    result = db.query(Model).filter(...)

# ❌ WRONG - Creating new sessions
def my_function():
    db = SessionLocal()  # Breaks transaction management

2. BEFORE CREATING NEW FEATURES
Step 1: Audit Existing Code
bash# Check if similar functionality exists
find backend -name "*.py" | xargs grep -l "keyword"

# Understand service dependencies
grep -r "from app.services" backend/app

# Check existing patterns
grep -r "llm_service\|LLMService" backend/app
Step 2: Follow Existing Patterns

If chat uses call_llm_with_memory(), use it
If services use global instances, use them
If there's a pattern for X, follow it

Step 3: Test Integration Points
python# Before building features, test the integration
# Can you call the existing service?
# Does the pattern work in isolation?
# Are there dependency issues?

3. ANTI-PATTERNS TO AVOID
❌ Creating Silos
python# WRONG - Isolated implementation
class MyFeatureService:
    def __init__(self):
        self.own_llm = LLMService()
        self.own_db = create_engine()
        self.own_cache = {}
❌ Hardcoding to "Fix" Issues
python# WRONG - Hardcoding when integration fails
if integration_failed:
    return "$15,000"  # Never do this
❌ Duplicate Implementations
python# WRONG - Creating parallel systems
# If TaxCalculations exists, don't create TaxOptimizer
# If financial_summary_service exists, don't create finance_service

4. INTEGRATION CHECKLIST
Before adding any feature:

 Does similar functionality exist?
 What pattern do existing features use?
 How does the chat endpoint work?
 How is LLM service accessed?
 Are there global services to use?
 What's the database session pattern?
 Are there existing models/schemas?


5. WHEN THINGS BREAK
Don't Band-Aid - Fix Properly
python# ❌ WRONG - Quick patch
try:
    result = broken_service()
except:
    return hardcoded_value

# ✅ CORRECT - Fix the root cause
# Understand why it's broken
# Fix the integration properly
# Test the fix thoroughly
Audit Before Fixing

What's the intended flow?
Where does it actually break?
Is it following existing patterns?
Are dependencies correct?


6. SPECIFIC WEALTHPATH AI RULES
Global Services (Never Recreate)

llm_service - Global LLM instance
vector_store - Global vector store
Database sessions - Always passed, never created

Established Patterns

Chat endpoints: Use chat_with_memory.py patterns
Financial data: Use financial_summary_service
Context building: Use complete_financial_context_service
Calculations: Consolidate in service classes

Architecture Principles

Single Source of Truth - One service per domain
Dependency Injection - Pass dependencies, don't create
Global Instances - Use existing, don't instantiate
Pattern Consistency - Follow established patterns


7. TESTING REQUIREMENTS
Before Declaring "Complete"
python# Test 1: Standalone functionality
assert service.calculate() == expected

# Test 2: Integration with existing system
assert chat_endpoint_with_feature() works

# Test 3: No hardcoded values
assert no_static_values_in_response()

# Test 4: Uses existing patterns
assert uses_global_llm_service()

8. RED FLAGS TO AVOID

🚩 Creating new LLM/DB instances
🚩 Hardcoding values "temporarily"
🚩 Duplicate services for same domain
🚩 Ignoring existing patterns
🚩 Not testing integration points
🚩 Band-aid fixes over root causes


THE GOLDEN RULE
Understand and follow existing patterns before creating new ones.
WealthPath AI has established patterns for a reason. Creating isolated implementations leads to integration failures, maintenance nightmares, and the hardcoding disasters we've seen.
When in doubt:

Audit what exists
Follow the pattern
Test integration
Fix properly, not quickly

This guide ensures consistent, maintainable development that integrates seamlessly with WealthPath AI's architecture.