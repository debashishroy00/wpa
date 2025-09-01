"""Test vector store matching with actual stored documents"""

import asyncio
import sys
sys.path.append('/app')

from app.services.simple_vector_store import SimpleVectorStore

async def test_vector_store_matching():
    """Test searches that should match the stored documents"""
    print("Testing Vector Store Matching")
    print("=" * 50)
    
    store = SimpleVectorStore()
    
    # Check what's in the store
    print(f"Documents in store: {len(store.documents)}")
    if store.documents:
        print("Document IDs:")
        for doc_id, doc in store.documents.items():
            print(f"  {doc_id}: {doc.content[:100]}...")
    
    print(f"\nTesting searches that should match stored content:")
    
    # Test searches based on the document content we saw
    test_searches = [
        "net worth",
        "financial summary", 
        "income",
        "expenses",
        "assets",
        "retirement",
        "goals",
        "monthly",
        "asset allocation",
        "estate planning",
        # Financial terms that should match user data
        "financial snapshot",
        "income sources", 
        "expense categories",
        "real estate",
        "beneficiary"
    ]
    
    for search_term in test_searches:
        results = store.search(search_term, limit=3)
        print(f"\n'{search_term}': {len(results)} results")
        
        for doc_id, score, doc in results:
            print(f"  {doc_id} (score: {score:.2f}): {doc.content[:80]}...")
    
    # Test the complex queries from Phase 3 tests
    print(f"\n" + "="*50)
    print("Testing Phase 3 complex queries:")
    
    complex_queries = [
        "retirement strategy age income savings",  # Simplified version
        "tax strategy wealth building",           # Simplified version
        "asset allocation risk tolerance",        # Simplified version  
        "debt payoff investment financial",       # Simplified version
    ]
    
    for query in complex_queries:
        results = store.search(query, limit=5)
        print(f"\n'{query}': {len(results)} results")
        
        if results:
            unique_sources = len(set(r[0] for r in results))
            print(f"  Unique sources: {unique_sources}")
            for doc_id, score, doc in results:
                print(f"    {doc_id} (score: {score:.2f})")

if __name__ == "__main__":
    asyncio.run(test_vector_store_matching())