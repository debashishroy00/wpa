"""Test Phase 2 of Agentic RAG - Query Decomposition & Smart Planning"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append('/app')

from app.services.agentic_rag import AgenticRAG
from app.db.session import SessionLocal

async def test_phase2():
    """Test Phase 2 query decomposition."""
    print("🚀 Starting Phase 2 Agentic RAG tests...")
    print("Testing query decomposition and smart planning")
    
    rag = AgenticRAG()
    db = SessionLocal()
    
    complex_queries = [
        "How much should I contribute to my 401k given my income?",
        "What are the tax implications if I retire early?", 
        "Should I pay off debt or invest more?",
        "What's my optimal asset allocation at my age?",
        "How can I minimize taxes while maximizing retirement savings?"
    ]
    
    print(f"📝 Testing {len(complex_queries)} complex queries...")
    
    for i, query in enumerate(complex_queries, 1):
        print(f"\n{'='*70}")
        print(f"Test {i}: {query}")
        print('='*70)
        
        try:
            result = await rag.handle_query(user_id=1, message=query, db=db)
            
            print(f"✅ SUCCESS")
            print(f"📝 Response length: {len(result['response'])} chars")
            print(f"🎯 Confidence: {result['confidence']}")
            print(f"📚 Citations: {len(result['citations'])} sources")
            print(f"⚠️  Warnings: {result['warnings']}")
            
            if result['citations']:
                print(f"🔍 Citations: {', '.join(result['citations'][:3])}")
            
            # Show response preview
            preview = result['response'][:300] + "..." if len(result['response']) > 300 else result['response']
            print(f"💬 Response preview: {preview}")
            
            # Check if decomposition worked (Phase 2 specific)
            if hasattr(rag, 'decomposition_cache'):
                print(f"🧠 Plans cached: {len(rag.decomposition_cache)}")
                
        except Exception as e:
            print(f"❌ FAILED: {e}")
            import traceback
            print(f"📊 Traceback: {traceback.format_exc()}")
    
    db.close()
    print(f"\n🎉 Phase 2 testing completed!")
    
    # Summary
    print(f"\n📈 PHASE 2 ANALYSIS:")
    print(f"   Cache entries: {len(rag.decomposition_cache)}")
    print(f"   Max steps configured: {rag.max_steps}")
    print(f"   Max chunks configured: {rag.max_chunks}")

async def test_decomposition_caching():
    """Test that query decomposition caching works."""
    print("\n🧪 Testing decomposition caching...")
    
    rag = AgenticRAG() 
    db = SessionLocal()
    
    test_query = "Should I pay off my mortgage early?"
    
    # First call - should create cache entry
    print("First call (should cache):")
    result1 = await rag.handle_query(user_id=1, message=test_query, db=db)
    cache_size_1 = len(rag.decomposition_cache)
    print(f"Cache size after first call: {cache_size_1}")
    
    # Second call - should use cache
    print("Second call (should use cache):")
    result2 = await rag.handle_query(user_id=1, message=test_query, db=db)
    cache_size_2 = len(rag.decomposition_cache)
    print(f"Cache size after second call: {cache_size_2}")
    
    # Verify caching worked
    if cache_size_1 == cache_size_2:
        print("✅ Caching working - no new entries created")
    else:
        print("❌ Caching issue - new entry created")
    
    db.close()

async def test_fallback_planning():
    """Test fallback when LLM decomposition fails."""
    print("\n🛡️ Testing fallback planning...")
    
    rag = AgenticRAG()
    db = SessionLocal()
    
    # This should trigger fallback since it might not parse as JSON
    test_query = "Complex financial scenario with multiple variables"
    
    try:
        result = await rag.handle_query(user_id=1, message=test_query, db=db)
        print(f"✅ Fallback handling successful")
        print(f"   Response length: {len(result['response'])}")
        print(f"   Confidence: {result['confidence']}")
    except Exception as e:
        print(f"❌ Fallback failed: {e}")
    
    db.close()

if __name__ == "__main__":
    print("🧪 WealthPath AI - Agentic RAG Phase 2 Tests")
    print("=" * 80)
    
    async def run_all_phase2_tests():
        # Test 1: Complex query decomposition
        await test_phase2()
        
        # Test 2: Caching functionality  
        await test_decomposition_caching()
        
        # Test 3: Fallback handling
        await test_fallback_planning()
        
        print("\n🏁 All Phase 2 tests completed!")
    
    asyncio.run(run_all_phase2_tests())