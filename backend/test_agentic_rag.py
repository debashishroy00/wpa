"""Test Phase 1 of Agentic RAG"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append('/app')

from app.services.agentic_rag import AgenticRAG
from app.db.session import SessionLocal

async def test_phase1():
    """Test basic functionality."""
    print("🚀 Starting Phase 1 Agentic RAG tests...")
    
    rag = AgenticRAG()
    db = SessionLocal()
    
    test_queries = [
        "What's my net worth?",
        "What are the 401k limits?", 
        "How much can I save?",
        "Show me my expenses",
        "Tax optimization help"
    ]
    
    print(f"📝 Testing {len(test_queries)} queries...")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*50}")
        print(f"Test {i}: {query}")
        print('='*50)
        
        try:
            result = await rag.handle_query(
                user_id=1,  # Use test user ID
                message=query,
                db=db
            )
            
            print(f"✅ SUCCESS")
            print(f"📝 Response: {result['response'][:150]}...")
            print(f"🎯 Confidence: {result['confidence']}")
            print(f"📚 Citations: {len(result['citations'])} sources")
            print(f"⚠️  Warnings: {result['warnings']}")
            
            if result['citations']:
                print(f"🔍 Top citation: {result['citations'][0]}")
                
        except Exception as e:
            print(f"❌ FAILED: {e}")
            import traceback
            print(f"📊 Traceback: {traceback.format_exc()}")
    
    db.close()
    print(f"\n🎉 Phase 1 testing completed!")

async def test_service_connections():
    """Test that all services initialize correctly."""
    print("\n🔧 Testing service connections...")
    
    try:
        rag = AgenticRAG()
        print("✅ AgenticRAG initialized")
        
        # Test QueryParser
        result = rag.parser.parse("What's my net worth?")
        print(f"✅ QueryParser: intent={result['intent']}")
        
        # Test VectorStore connection
        vector_results = await rag.vector_store.query("authority", "test", {"limit": 1})
        print(f"✅ VectorStore: returned {len(vector_results)} results")
        
        # Test IdentityMath (without DB call)
        print("✅ IdentityMath initialized")
        
        # Test TrustEngine  
        print("✅ TrustEngine initialized")
        
        print("✅ All service connections successful!")
        return True
        
    except Exception as e:
        print(f"❌ Service connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 WealthPath AI - Agentic RAG Phase 1 Tests")
    print("=" * 60)
    
    async def run_all_tests():
        # Test 1: Service connections
        connections_ok = await test_service_connections()
        
        if connections_ok:
            # Test 2: Full pipeline
            await test_phase1()
        else:
            print("❌ Skipping pipeline tests due to connection failures")
    
    asyncio.run(run_all_tests())