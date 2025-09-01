"""Test Phase 3 Improvements - Debug Iterative Refinement"""

import asyncio
import sys
import os
import logging

# Add the backend directory to Python path
sys.path.append('/app')

from app.services.agentic_rag import AgenticRAG
from app.db.session import SessionLocal

# Set up logging to see debug output
logging.basicConfig(level=logging.INFO)

async def test_gap_triggering_queries():
    """Test specific queries that should trigger gap identification and iterations."""
    print("Testing gap-triggering queries with improved Phase 3...")
    print("=" * 70)
    
    rag = AgenticRAG()
    db = SessionLocal()
    
    # Queries specifically designed to trigger different gap types
    gap_test_queries = [
        {
            "query": "Calculate my exact RMD amount for next year, factoring in my IRA balance, 401k balance, age 72 rule changes, and how it affects my state tax liability in California",
            "expected_gaps": ["state_tax_rules", "contribution_limits", "retirement_timeline"],
            "description": "Complex RMD query requiring specific data"
        },
        {
            "query": "What's my optimal asset allocation considering my risk tolerance and retirement timeline?", 
            "expected_gaps": ["risk_assessment", "retirement_timeline"],
            "description": "Investment query missing key personal data"
        },
        {
            "query": "How much should I contribute to my 401k this year to minimize taxes?",
            "expected_gaps": ["contribution_limits", "state_tax_rules"],
            "description": "Tax optimization requiring current limits"
        },
        {
            "query": "Should I do a Roth conversion this year given my income and tax situation?",
            "expected_gaps": ["state_tax_rules", "retirement_timeline"],
            "description": "Complex tax strategy decision"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(gap_test_queries, 1):
        print(f"\nTEST {i}: {test_case['description']}")
        print(f"Query: '{test_case['query']}'")
        print(f"Expected gaps: {test_case['expected_gaps']}")
        print("-" * 70)
        
        try:
            result = await rag.handle_query(user_id=1, message=test_case["query"], db=db)
            
            # Extract Phase 3 metrics
            gaps_identified = result.get('gaps_identified', 0)
            iterations_performed = result.get('iterations_performed', 0) 
            confidence = result['confidence']
            citations = len(result['citations'])
            
            print(f"RESULTS:")
            print(f"  Gaps identified: {gaps_identified}")
            print(f"  Iterations performed: {iterations_performed}")
            print(f"  Confidence: {confidence}")
            print(f"  Citations: {citations}")
            print(f"  Warnings: {result['warnings']}")
            
            # Check if Phase 3 features activated
            iteration_triggered = iterations_performed > 0
            gap_detection_worked = gaps_identified > 0
            
            print(f"\nPHASE 3 ANALYSIS:")
            print(f"  Iterative refinement: {'TRIGGERED' if iteration_triggered else 'NOT TRIGGERED'}")
            print(f"  Gap identification: {'WORKING' if gap_detection_worked else 'NOT DETECTED'}")
            print(f"  Multiple citations: {'YES' if citations > 1 else 'NO'}")
            
            # Response preview
            preview = result['response'][:200] + "..." if len(result['response']) > 200 else result['response']
            print(f"  Response preview: {preview}")
            
            results.append({
                'test': i,
                'query': test_case['query'],
                'gaps_identified': gaps_identified,
                'iterations': iterations_performed,
                'confidence': confidence,
                'citations': citations,
                'iteration_triggered': iteration_triggered,
                'gap_detection': gap_detection_worked
            })
            
        except Exception as e:
            print(f"ERROR: {e}")
            results.append({
                'test': i,
                'query': test_case['query'],
                'error': str(e),
                'gaps_identified': 0,
                'iterations': 0,
                'confidence': 'ERROR',
                'citations': 0,
                'iteration_triggered': False,
                'gap_detection': False
            })
    
    db.close()
    
    # Overall analysis
    print(f"\n{'='*70}")
    print("PHASE 3 IMPROVEMENT ANALYSIS")
    print('='*70)
    
    successful_tests = [r for r in results if 'error' not in r]
    total_iterations = sum([r['iterations'] for r in successful_tests])
    total_gaps = sum([r['gaps_identified'] for r in successful_tests])
    iteration_triggers = sum([1 for r in successful_tests if r['iteration_triggered']])
    gap_detections = sum([1 for r in successful_tests if r['gap_detection']])
    
    print(f"Successful tests: {len(successful_tests)}/{len(results)}")
    print(f"Tests triggering iterations: {iteration_triggers}/{len(successful_tests)}")
    print(f"Tests detecting gaps: {gap_detections}/{len(successful_tests)}")
    print(f"Total iterations across all tests: {total_iterations}")
    print(f"Total gaps identified: {total_gaps}")
    print(f"Average iterations per test: {total_iterations/len(successful_tests) if successful_tests else 0:.1f}")
    
    # Success metrics for Phase 3
    iteration_success_rate = (iteration_triggers / len(successful_tests)) * 100 if successful_tests else 0
    gap_detection_rate = (gap_detections / len(successful_tests)) * 100 if successful_tests else 0
    
    print(f"\nPHASE 3 SUCCESS METRICS:")
    print(f"  Iteration trigger rate: {iteration_success_rate:.1f}% (target: >75%)")
    print(f"  Gap detection rate: {gap_detection_rate:.1f}% (target: >50%)")
    
    if iteration_success_rate >= 75:
        print("  ✅ Iterative refinement is working well!")
    elif iteration_success_rate >= 25:
        print("  ⚠️  Iterative refinement partially working, needs tuning")
    else:
        print("  ❌ Iterative refinement not triggering reliably")
    
    if gap_detection_rate >= 50:
        print("  ✅ Gap identification is working!")
    else:
        print("  ❌ Gap identification needs improvement")
    
    return results

async def test_vector_store_population():
    """Check if vector store has enough content to support iterative refinement."""
    print(f"\nTesting vector store population...")
    
    rag = AgenticRAG()
    
    # Test a few different search terms
    test_searches = [
        "retirement planning",
        "401k contribution limits", 
        "tax deductions",
        "investment allocation",
        "financial planning"
    ]
    
    for search_term in test_searches:
        try:
            results = await rag.vector_store.query(
                index="authority",
                query=search_term,
                filters={"limit": 5}
            )
            
            print(f"  '{search_term}': {len(results)} results")
            if results:
                sources = set(r.get('source', 'unknown') for r in results)
                print(f"    Sources: {list(sources)}")
            
        except Exception as e:
            print(f"  '{search_term}': ERROR - {e}")
    
    print("\nVector store analysis:")
    print("  - If most searches return 0-1 results: Vector store may be empty/minimal")
    print("  - If searches return 2-5 results: Should support basic iteration")
    print("  - If searches return diverse sources: Should support full Phase 3 features")

if __name__ == "__main__":
    print("WealthPath AI - Phase 3 Improvement Tests")
    print("=" * 70)
    
    async def run_improvement_tests():
        # Test 1: Vector store population
        await test_vector_store_population()
        
        # Test 2: Gap-triggering queries
        await test_gap_triggering_queries()
        
        print(f"\nImprovement tests completed!")
        print(f"\nNext steps based on results:")
        print(f"  - If iterations not triggering: Check sufficiency assessment logic")
        print(f"  - If no vector results: Need to populate knowledge base") 
        print(f"  - If gaps not detected: Verify gap detection rules")
        print(f"  - If LLM errors: Check API key configuration")
    
    asyncio.run(run_improvement_tests())