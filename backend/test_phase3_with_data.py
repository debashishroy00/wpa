"""Test Phase 3 with properly populated vector store based on VECTOR.md"""

import asyncio
import sys
import json
from unittest.mock import MagicMock

sys.path.append('/app')

from app.services.agentic_rag import AgenticRAG
from app.services.simple_vector_store import SimpleVectorStore

def populate_test_vector_store():
    """Populate vector store with the 7 documents described in VECTOR.md"""
    store = SimpleVectorStore()
    
    # Document 1: Financial Summary
    store.add_document(
        doc_id="user_1_financial_summary",
        content="""FINANCIAL SNAPSHOT: Net Worth: $2,565,545 Monthly Income: $17,744 Monthly Expenses: $7,481 Monthly Surplus: $10,263 Savings Rate: 57.8% Debt-to-Income: 13.9% Housing Cost Ratio: 20.7%""",
        metadata={"category": "summary", "user_id": 1}
    )
    
    # Document 2: Income Breakdown
    store.add_document(
        doc_id="user_1_income_breakdown", 
        content="""INCOME SOURCES (Monthly): - manual entry: $17,744 - Salary: $12,000 - 401K Contribution: $2,400 - Company RSU: $2,500 - Rental Income: $844 - Total Monthly Income: $17,744""",
        metadata={"category": "income", "user_id": 1}
    )
    
    # Document 3: Expense Breakdown
    store.add_document(
        doc_id="user_1_expense_breakdown",
        content="""EXPENSE CATEGORIES (Monthly): - food: $1,400 • Groceries: $600 • Restaurants: $800 - healthcare: $550 • Doctors: $200 • Gym: $350 - utilities: $1,000 • Water: $100 • All utilities: $900 - transportation: $500 - housing: $2,881 • Home Improvement: $200 • Property Tax: $517 - personal: $1,000 • General Merchandise: $800 • Entertainment: $200 - Total Monthly Expenses: $7,481""",
        metadata={"category": "expenses", "user_id": 1}
    )
    
    # Document 4: Asset Allocation
    store.add_document(
        doc_id="user_1_asset_allocation",
        content="""ASSET ALLOCATION: - Real Estate: 50.3% ($1,449,706) - Investments: 25.7% ($741,000) - Retirement: 10.8% ($310,216) - Alternative: 4.5% ($130,000 Bitcoin) - Cash: 3.6% ($104,557) - Other: 5.0% ($144,348) - Total Assets: $2,879,827""",
        metadata={"category": "assets", "user_id": 1}
    )
    
    # Document 5: Financial Goals
    store.add_document(
        doc_id="user_1_financial_goals",
        content="""FINANCIAL GOALS: - Retirement Goal: $3,500,000 • Current Progress: 66.2% ($2,317,896) • Years to Goal: 10.3 • Target Achievement Age: 64 - College Fund: $100,000 • Current Progress: 90% ($90,000) • Years to Goal: 2 - Emergency Fund: $104,557 • Target: 6 months expenses ($44,886) • Current Status: Adequate""",
        metadata={"category": "goals", "user_id": 1}
    )
    
    # Document 6: Estate & Insurance
    store.add_document(
        doc_id="user_1_estate_insurance",
        content="""ESTATE PLANNING: - Beneficiary_Designation: current - Healthcare_Directive: current - Will: current - Power_of_Attorney: current INSURANCE COVERAGE: - Life_Insurance: $1,000,000 • Annual Premium: $1,400 - Home_Insurance: $800,000 • Annual Premium: $1,300""",
        metadata={"category": "estate_insurance", "user_id": 1}
    )
    
    # Document 7: Chat Intelligence & Memory  
    store.add_document(
        doc_id="user_1_chat_intelligence",
        content="""CHAT INTELLIGENCE & MEMORY:

SESSION SUMMARY: Recent conversation count and total exchanges

CONVERSATION CONTEXT:
- Recent Intent: Current user focus (retirement, budgeting, etc.)
- Active Topics: Key discussion areas
- Decision Patterns: User decision-making style
- Engagement Level: Conversation depth indicator

FINANCIAL FOCUS AREAS:
- Primary Interests: Most discussed topics
- Key Decisions: Recorded financial choices  
- Action Items: Pending tasks from conversations
- Conversation Continuity: Relationship establishment level

CONTEXT FOR AI ADVISOR:
- User communication preferences
- Financial sophistication level
- Response patterns and preferences""",
        metadata={"category": "chat_memory", "user_id": 1}
    )
    
    print(f"Populated vector store with {store.count_documents()} documents")
    return store

class MockLLMService:
    """Mock LLM service that returns sensible responses"""
    def __init__(self):
        self.clients = {"mock": True}
    
    async def generate(self, request):
        if "assessment engine" in request.system_prompt.lower():
            # Be more strict to trigger iterations  
            if "net worth" in request.user_prompt.lower() and "retirement" in request.user_prompt.lower():
                return MagicMock(content=json.dumps({
                    "sufficient": False,
                    "confidence": 0.3,
                    "gaps": [
                        {"gap_type": "retirement_timeline", "description": "Need specific retirement age and timeline analysis"},
                        {"gap_type": "tax_implications", "description": "Missing tax strategy for retirement planning"}
                    ],
                    "reasoning": "Complex retirement strategy requires comprehensive analysis across multiple dimensions"
                }))
            else:
                return MagicMock(content=json.dumps({
                    "sufficient": True,
                    "confidence": 0.8,
                    "gaps": [],
                    "reasoning": "Sufficient information available"
                }))
        
        elif "query planner" in request.system_prompt.lower():
            return MagicMock(content=json.dumps([
                {"step": 1, "question": "What is current financial position?", "search_query": "net worth financial summary", "index": "authority"},
                {"step": 2, "question": "What are retirement goals?", "search_query": "retirement goals timeline", "index": "authority"}
            ]))
        
        elif "search query generator" in request.system_prompt.lower():
            return MagicMock(content=json.dumps([
                {"query": "retirement timeline age 64 strategy", "gap_type": "retirement_timeline", "for_gap": "retirement timing"},
                {"query": "tax planning retirement distribution", "gap_type": "tax_implications", "for_gap": "tax strategy"}
            ]))
        
        else:
            return MagicMock(content="Based on your comprehensive financial profile with net worth of $2.57M and strong savings rate of 57.8%, here's your optimal retirement strategy. You're on track to reach your $3.5M retirement goal by age 64, with 66.2% progress already achieved. [This response demonstrates Phase 3 successfully used multiple iterations and data sources]")

async def test_phase3_with_real_data():
    """Test Phase 3 with properly populated vector store"""
    print("Phase 3 Test with Real Data from VECTOR.md")
    print("=" * 50)
    
    # Populate vector store
    vector_store = populate_test_vector_store()
    
    # Set up RAG with populated vector store
    rag = AgenticRAG()
    rag.vector_store.store = vector_store
    
    # Mock LLM service
    import app.services.agentic_rag as agentic_rag_module
    agentic_rag_module.llm_service = MockLLMService()
    
    # Mock IdentityMath
    rag.identity_math.compute_claims = lambda user_id, db: {
        'net_worth': 2565545,
        'monthly_surplus': 10263,
        'savings_rate': 57.8,
        '_context': {'age': 54, 'state': 'unknown'}
    }
    
    # Test queries that should find documents and potentially trigger iterations
    test_queries = [
        {
            "query": "What's my net worth and retirement strategy?",
            "should_match": ["user_1_financial_summary", "user_1_financial_goals"],
            "description": "Should trigger retirement timeline gap"
        },
        {
            "query": "Show me my monthly expenses and income breakdown", 
            "should_match": ["user_1_income_breakdown", "user_1_expense_breakdown"],
            "description": "Should find expense/income docs"
        },
        {
            "query": "What's my asset allocation and investment portfolio?",
            "should_match": ["user_1_asset_allocation"],
            "description": "Should find asset allocation doc"
        }
    ]
    
    results = []
    
    for test_case in test_queries:
        print(f"\nTEST: {test_case['description']}")
        print(f"Query: '{test_case['query']}'")
        print(f"Expected matches: {test_case['should_match']}")
        print("-" * 50)
        
        # Mock database
        mock_db = MagicMock()
        
        try:
            result = await rag.handle_query(user_id=1, message=test_case["query"], db=mock_db)
            
            print("RESULTS:")
            print(f"  Response length: {len(result['response'])} chars")
            print(f"  Confidence: {result['confidence']}")
            print(f"  Citations: {len(result['citations'])}")
            print(f"  Gaps identified: {result.get('gaps_identified', 0)}")
            print(f"  Iterations: {result.get('iterations_performed', 0)}")
            
            if result['citations']:
                print(f"  Citation sources:")
                for citation in result['citations']:
                    doc_id = citation.split('#')[0]
                    print(f"    - {doc_id}")
            
            # Check if expected documents were found
            found_docs = [c.split('#')[0] for c in result['citations']]
            expected_found = any(expected in found_docs for expected in test_case['should_match'])
            
            print(f"  Expected docs found: {'YES' if expected_found else 'NO'}")
            print(f"  Phase 3 triggered: {'YES' if result.get('iterations_performed', 0) > 0 else 'NO'}")
            
            # Show response preview
            preview = result['response'][:150] + "..." if len(result['response']) > 150 else result['response']
            print(f"  Response preview: {preview}")
            
            results.append({
                'query': test_case['query'],
                'citations': len(result['citations']),
                'iterations': result.get('iterations_performed', 0),
                'gaps': result.get('gaps_identified', 0),
                'confidence': result['confidence'],
                'expected_found': expected_found
            })
            
        except Exception as e:
            print(f"ERROR: {e}")
            results.append({
                'query': test_case['query'],
                'error': str(e),
                'citations': 0,
                'iterations': 0,
                'gaps': 0,
                'confidence': 'ERROR',
                'expected_found': False
            })
    
    # Summary analysis
    print(f"\n" + "="*50)
    print("PHASE 3 WITH REAL DATA ANALYSIS")
    print("="*50)
    
    successful_tests = [r for r in results if 'error' not in r]
    total_citations = sum(r['citations'] for r in successful_tests)
    total_iterations = sum(r['iterations'] for r in successful_tests)
    total_gaps = sum(r['gaps'] for r in successful_tests)
    docs_found = sum(1 for r in successful_tests if r['expected_found'])
    
    print(f"Successful tests: {len(successful_tests)}/{len(results)}")
    print(f"Total citations generated: {total_citations}")
    print(f"Total iterations triggered: {total_iterations}")
    print(f"Total gaps identified: {total_gaps}")
    print(f"Expected documents found: {docs_found}/{len(successful_tests)}")
    print(f"Average citations per query: {total_citations/len(successful_tests) if successful_tests else 0:.1f}")
    
    print(f"\nPHASE 3 SUCCESS METRICS:")
    citation_success = total_citations > len(successful_tests)  # More than 1 citation per query
    iteration_success = total_iterations > 0  # At least some iterations triggered
    document_matching = docs_found >= len(successful_tests) * 0.5  # 50%+ found expected docs
    
    print(f"  Rich citations (>1 per query): {'PASS' if citation_success else 'FAIL'}")
    print(f"  Iterative refinement: {'PASS' if iteration_success else 'FAIL'}")  
    print(f"  Document matching: {'PASS' if document_matching else 'FAIL'}")
    
    if citation_success and document_matching:
        print(f"\n SUCCESS: Vector store integration working!")
        print(f"   Phase 3 can now access real financial data")
        if iteration_success:
            print(f"   Phase 3 iterative refinement also triggered!")
    
    return results

if __name__ == "__main__":
    asyncio.run(test_phase3_with_real_data())