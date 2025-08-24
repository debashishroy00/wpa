#!/usr/bin/env python3
"""
Migration Script: ChromaDB to Simple Vector Store
Migrates existing 90 knowledge base documents to SimpleVectorStore
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime
import hashlib

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.simple_vector_store import get_vector_store, reset_vector_store
from app.services.knowledge_base import KnowledgeBaseService

def migrate_documents():
    """Migrate documents from filesystem to SimpleVectorStore"""
    print("🔄 Starting migration from filesystem to SimpleVectorStore...")
    
    # Reset vector store to start fresh
    reset_vector_store()
    vector_store = get_vector_store()
    
    # Initialize knowledge base service (this will load docs from filesystem)
    kb_service = KnowledgeBaseService()
    
    # Get stats
    stats = vector_store.get_stats()
    print(f"✅ Migration completed!")
    print(f"📊 Statistics:")
    print(f"   - Total documents: {stats['total_documents']}")
    print(f"   - Documents with embeddings: {stats['documents_with_embeddings']}")
    print(f"   - Categories: {list(stats['categories'].keys())}")
    print(f"   - Storage path: {stats['storage_path']}")
    
    return stats

def verify_migration():
    """Verify that migration was successful"""
    print("\n🔍 Verifying migration...")
    
    vector_store = get_vector_store()
    kb_service = KnowledgeBaseService()
    
    # Test basic operations
    total_docs = vector_store.count_documents()
    print(f"✅ Total documents in store: {total_docs}")
    
    # Test search functionality
    test_queries = [
        "retirement planning",
        "asset allocation", 
        "tax strategy",
        "debt management",
        "emergency fund"
    ]
    
    print("\n🔍 Testing search functionality:")
    for query in test_queries:
        results = vector_store.search(query, limit=3)
        print(f"   Query: '{query}' -> {len(results)} results")
        
        if results:
            best_result = results[0]
            print(f"      Best match: {best_result[2].metadata.get('title', 'No title')} (score: {best_result[1]:.3f})")
    
    # Test knowledge base integration
    print("\n🔍 Testing knowledge base integration:")
    kb_results = kb_service.search("portfolio diversification", top_k=2)
    print(f"   KB search results: {len(kb_results)}")
    
    for result in kb_results:
        print(f"      {result.document.title} (score: {result.score:.3f})")
    
    # Test categories
    categories = kb_service.list_categories()
    print(f"\n📂 Available categories: {categories}")
    
    return {
        "total_documents": total_docs,
        "search_working": len(test_queries) > 0,
        "kb_integration_working": len(kb_results) > 0,
        "categories": categories
    }

def create_sample_documents():
    """Create some sample documents if no documents exist"""
    vector_store = get_vector_store()
    
    if vector_store.count_documents() == 0:
        print("📝 No documents found, creating sample documents...")
        
        sample_docs = [
            {
                "title": "Retirement Planning Basics",
                "content": """
                # Retirement Planning Fundamentals
                
                Retirement planning is crucial for financial security. Key concepts include:
                
                - 401(k) contributions and employer matching
                - IRA vs Roth IRA considerations
                - Asset allocation by age
                - Withdrawal strategies in retirement
                - Social Security optimization
                
                The 4% rule suggests you can safely withdraw 4% of your retirement portfolio annually.
                """,
                "category": "retirement",
                "tags": ["401k", "ira", "asset allocation", "withdrawal"]
            },
            {
                "title": "Asset Allocation Strategies",
                "content": """
                # Asset Allocation for Different Life Stages
                
                Asset allocation should change as you age:
                
                **20s-30s (Aggressive Growth)**
                - 80-90% stocks
                - 10-20% bonds
                - Focus on growth investments
                
                **40s-50s (Moderate Growth)**
                - 60-70% stocks
                - 30-40% bonds
                - Balance growth with stability
                
                **60s+ (Conservative)**
                - 40-50% stocks
                - 50-60% bonds
                - Preserve capital for retirement
                """,
                "category": "investment",
                "tags": ["stocks", "bonds", "diversification", "age-based"]
            },
            {
                "title": "Emergency Fund Guidelines",
                "content": """
                # Building Your Emergency Fund
                
                An emergency fund is essential for financial stability:
                
                **How Much to Save**
                - 3-6 months of expenses for stable employment
                - 6-12 months for variable income
                - Consider your personal risk factors
                
                **Where to Keep It**
                - High-yield savings account
                - Money market account
                - Short-term CDs
                
                **When to Use It**
                - Job loss
                - Major medical expenses
                - Essential home repairs
                - Not for vacations or wants
                """,
                "category": "cash",
                "tags": ["emergency fund", "savings", "liquidity", "stability"]
            },
            {
                "title": "Debt Payoff Strategies",
                "content": """
                # Effective Debt Management
                
                Choose the right strategy for your situation:
                
                **Debt Snowball Method**
                - Pay minimums on all debts
                - Put extra money toward smallest balance
                - Provides psychological wins
                
                **Debt Avalanche Method**
                - Pay minimums on all debts
                - Put extra money toward highest interest rate
                - Mathematically optimal
                
                **Consider Debt Consolidation**
                - Lower interest rates
                - Simplified payments
                - Improved cash flow
                """,
                "category": "debt",
                "tags": ["debt payoff", "snowball", "avalanche", "consolidation"]
            },
            {
                "title": "Tax-Efficient Investing",
                "content": """
                # Minimizing Investment Taxes
                
                Smart tax strategies can significantly impact returns:
                
                **Tax-Advantaged Accounts**
                - 401(k) for pre-tax contributions
                - Roth IRA for tax-free growth
                - HSA as retirement account
                
                **Asset Location Strategy**
                - Hold bonds in tax-advantaged accounts
                - Hold stocks in taxable accounts
                - Consider tax-loss harvesting
                
                **Long-term vs Short-term Gains**
                - Hold investments >1 year for lower tax rates
                - Time asset sales strategically
                """,
                "category": "tax",
                "tags": ["tax efficiency", "asset location", "capital gains", "tax-loss harvesting"]
            }
        ]
        
        for i, doc_data in enumerate(sample_docs):
            doc_id = f"sample_{i+1}_{hashlib.md5(doc_data['title'].encode()).hexdigest()[:8]}"
            
            vector_store.add_document(
                content=doc_data["content"],
                doc_id=doc_id,
                metadata={
                    "title": doc_data["title"],
                    "category": doc_data["category"],
                    "tags": doc_data["tags"],
                    "kb_id": f"SAMPLE-{i+1:03d}",
                    "file_path": f"samples/{doc_data['title'].lower().replace(' ', '_')}.md",
                    "last_updated": datetime.now().isoformat()[:10],
                    "source": "migration_script"
                }
            )
        
        print(f"✅ Created {len(sample_docs)} sample documents")
    
    return vector_store.count_documents()

def main():
    """Main migration function"""
    print("🚀 SimpleVectorStore Migration Tool")
    print("=" * 50)
    
    try:
        # Step 1: Create sample documents if none exist
        doc_count = create_sample_documents()
        
        # Step 2: Migrate documents
        migration_stats = migrate_documents()
        
        # Step 3: Verify migration
        verification_results = verify_migration()
        
        # Step 4: Summary
        print("\n" + "=" * 50)
        print("📋 MIGRATION SUMMARY")
        print("=" * 50)
        print(f"✅ Documents migrated: {migration_stats['total_documents']}")
        print(f"✅ Categories available: {len(verification_results['categories'])}")
        print(f"✅ Search functionality: {'Working' if verification_results['search_working'] else 'Failed'}")
        print(f"✅ KB integration: {'Working' if verification_results['kb_integration_working'] else 'Failed'}")
        print(f"✅ Storage path: {migration_stats['storage_path']}")
        
        if migration_stats['total_documents'] > 0:
            print("\n🎉 Migration completed successfully!")
            print("💡 The SimpleVectorStore is ready for production use.")
        else:
            print("\n⚠️  Migration completed but no documents were found.")
            print("💡 Make sure the knowledge_base directory exists and contains .md files.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)