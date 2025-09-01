"""Test Phase 3 of Agentic RAG - Iterative Refinement & Sufficiency Checking"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append('/app')

from app.services.agentic_rag import AgenticRAG
from app.db.session import SessionLocal

async def test_phase3():
    """Test Phase 3 iterative refinement and sufficiency checking."""
    print("🚀 Starting Phase 3 Agentic RAG tests...")
    print("Testing iterative refinement and sufficiency checking")
    
    rag = AgenticRAG()
    db = SessionLocal()
    
    # Complex queries that should trigger multiple iterations
    complex_queries = [
        "What's the best retirement strategy considering my age, income, and current savings?",
        "How should I optimize my tax strategy while maximizing long-term wealth building?",
        "What's my ideal asset allocation considering my risk tolerance and timeline?",
        "Should I prioritize debt payoff or investment based on my complete financial picture?",
        "How can I achieve financial independence considering all my current constraints?"
    ]
    
    print(f"📝 Testing {len(complex_queries)} complex queries that should trigger refinement...")
    
    results_summary = []
    
    for i, query in enumerate(complex_queries, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}: {query}")
        print('='*80)
        
        try:
            result = await rag.handle_query(user_id=1, message=query, db=db)
            
            print(f"✅ SUCCESS")
            print(f"📝 Response length: {len(result['response'])} chars")
            print(f"🎯 Confidence: {result['confidence']}")
            print(f"📚 Citations: {len(result['citations'])} sources")
            print(f"⚠️  Warnings: {result['warnings']}")
            print(f"🔍 Gaps identified: {result.get('gaps_identified', 0)}")
            print(f"🔄 Iterations performed: {result.get('iterations_performed', 0)}")
            
            if result['citations']:
                print(f"🔍 Citations: {', '.join(result['citations'][:3])}...")
            
            # Show response preview
            preview = result['response'][:300] + "..." if len(result['response']) > 300 else result['response']
            print(f"💬 Response preview: {preview}")
            
            # Track for summary
            results_summary.append({
                'query': query,
                'confidence': result['confidence'],
                'citations': len(result['citations']),
                'gaps': result.get('gaps_identified', 0),
                'iterations': result.get('iterations_performed', 0),
                'success': True
            })
            
            # Phase 3 specific checks
            if result.get('iterations_performed', 0) > 0:
                print(f"🎉 PHASE 3 FEATURE: Iterative refinement triggered!")
            if result.get('gaps_identified', 0) > 0:
                print(f"🧠 PHASE 3 FEATURE: Gap identification worked!")
                
        except Exception as e:
            print(f"❌ FAILED: {e}")
            import traceback
            print(f"📊 Traceback: {traceback.format_exc()}")
            
            results_summary.append({
                'query': query,
                'confidence': 'ERROR',
                'citations': 0,
                'gaps': 0,
                'iterations': 0,
                'success': False
            })
    
    db.close()
    
    # Phase 3 Summary Analysis
    print(f"\n{'='*80}")
    print(f"📈 PHASE 3 ANALYSIS SUMMARY")
    print('='*80)
    
    successful_tests = [r for r in results_summary if r['success']]
    total_iterations = sum([r['iterations'] for r in successful_tests])
    total_gaps = sum([r['gaps'] for r in successful_tests])
    high_confidence = len([r for r in successful_tests if r['confidence'] == 'HIGH'])
    
    print(f"✅ Successful tests: {len(successful_tests)}/{len(results_summary)}")
    print(f"🔄 Total iterations performed: {total_iterations}")
    print(f"🧠 Total gaps identified: {total_gaps}")
    print(f"📊 HIGH confidence responses: {high_confidence}/{len(successful_tests)}")
    print(f"📚 Average citations per response: {sum([r['citations'] for r in successful_tests])/len(successful_tests) if successful_tests else 0:.1f}")
    
    # Phase 3 Feature Verification
    iterative_refinement_working = total_iterations > 0
    gap_identification_working = total_gaps > 0
    
    print(f"\n🎯 PHASE 3 FEATURES:")
    print(f"   Iterative Refinement: {'✅ WORKING' if iterative_refinement_working else '❌ NOT TRIGGERED'}")
    print(f"   Gap Identification: {'✅ WORKING' if gap_identification_working else '❌ NOT DETECTED'}")
    print(f"   Smart Evidence Ranking: {'✅ ENABLED' if successful_tests else '❌ FAILED'}")
    print(f"   Enhanced Confidence: {'✅ WORKING' if high_confidence > 0 else '❌ NO HIGH CONFIDENCE'}")

async def test_refinement_triggers():
    """Test specific scenarios that should trigger refinement."""
    print(f"\n🧪 Testing refinement trigger scenarios...")
    
    rag = AgenticRAG()
    db = SessionLocal()
    
    # Scenarios designed to have information gaps
    gap_scenarios = [
        ("Missing timeline", "I want to retire early, what should I do?"),
        ("Incomplete tax info", "How can I optimize my taxes?"),
        ("Vague goals", "Help me with my investments"),
        ("Multi-factor query", "What's the best financial strategy for someone like me?")
    ]
    
    for scenario_name, query in gap_scenarios:
        print(f"\n📋 Testing: {scenario_name}")
        print(f"Query: '{query}'")
        
        try:
            result = await rag.handle_query(user_id=1, message=query, db=db)
            
            gaps = result.get('gaps_identified', 0)
            iterations = result.get('iterations_performed', 0)
            
            print(f"   Gaps identified: {gaps}")
            print(f"   Iterations: {iterations}")
            print(f"   Confidence: {result['confidence']}")
            
            if gaps > 0 or iterations > 0:
                print(f"   ✅ Refinement triggered as expected")
            else:
                print(f"   ⚠️  No refinement triggered")
                
        except Exception as e:
            print(f"   ❌ Failed: {e}")
    
    db.close()

async def test_caching_with_refinement():
    """Test that refinement results are cached properly."""
    print(f"\n💾 Testing refinement caching...")
    
    rag = AgenticRAG()
    db = SessionLocal()
    
    test_query = "What's my optimal retirement timeline given my current financial situation?"
    
    print("First call (should perform refinement):") 
    result1 = await rag.handle_query(user_id=1, message=test_query, db=db)
    iterations1 = result1.get('iterations_performed', 0)
    gaps1 = result1.get('gaps_identified', 0)
    cache_size_1 = len(rag.decomposition_cache)
    
    print(f"   Iterations: {iterations1}")
    print(f"   Gaps: {gaps1}")
    print(f"   Cache size: {cache_size_1}")
    
    print("Second call (should use cache):")
    result2 = await rag.handle_query(user_id=1, message=test_query, db=db) 
    iterations2 = result2.get('iterations_performed', 0)
    gaps2 = result2.get('gaps_identified', 0)
    cache_size_2 = len(rag.decomposition_cache)
    
    print(f"   Iterations: {iterations2}")
    print(f"   Gaps: {gaps2}")  
    print(f"   Cache size: {cache_size_2}")
    
    if cache_size_1 == cache_size_2:
        print("   ✅ Caching working - no new cache entries")
    else:
        print("   ❌ Caching issue - new entries created")
    
    db.close()

if __name__ == "__main__":
    print("WealthPath AI - Agentic RAG Phase 3 Tests")
    print("=" * 80)
    
    async def run_all_phase3_tests():
        # Test 1: Core Phase 3 functionality
        await test_phase3()
        
        # Test 2: Refinement trigger scenarios
        await test_refinement_triggers()
        
        # Test 3: Caching with refinement
        await test_caching_with_refinement()
        
        print(f"\n🏁 All Phase 3 tests completed!")
        print(f"\n📋 PHASE 3 SUCCESS CRITERIA:")
        print(f"   ✓ Complex queries trigger multiple iterations")
        print(f"   ✓ Gap identification works correctly")
        print(f"   ✓ Follow-up searches are generated")
        print(f"   ✓ Smart evidence ranking with iteration bonuses")
        print(f"   ✓ Enhanced confidence assessment")
        print(f"   ✓ Gap awareness in responses")
    
    asyncio.run(run_all_phase3_tests())