#!/usr/bin/env python3
"""
🚑 COMPREHENSIVE VECTOR DATABASE RECOVERY
Indexes ALL financial data and goals into vector database
"""
print('🚑 COMPREHENSIVE DATA INDEXING...')
import sys
sys.path.append('/app')

try:
    from app.services.vector_db_service import get_vector_db
    from app.db.session import SessionLocal
    from app.services.user_service import UserService
    from app.models.financial import FinancialEntry
    from app.models.goal import FinancialGoal
    import hashlib
    from datetime import datetime
    
    print('✅ All modules imported')
    
    vector_db = get_vector_db()
    
    with SessionLocal() as db:
        user_service = UserService(db)
        user = user_service.get_user_by_id(1)
        
        if not user:
            print('❌ User not found')
            exit(1)
            
        print(f'👤 User: {user.email}')
        
        # Get ALL financial entries
        financial_entries = db.query(FinancialEntry).filter(
            FinancialEntry.user_id == 1,
            FinancialEntry.is_active == True
        ).all()
        
        print(f'💰 Found {len(financial_entries)} financial entries')
        
        # Get ALL goals
        goals = db.query(FinancialGoal).filter(
            FinancialGoal.user_id == 1,
            FinancialGoal.status == 'active'
        ).all()
        
        print(f'🎯 Found {len(goals)} goals')
        
        documents_to_add = []
        
        # Index each financial entry as a separate document
        for entry in financial_entries:
            doc_id = f'user_1_financial_{entry.id}'
            content = f'{entry.category}: {entry.subcategory} - {entry.description} Amount: ${entry.amount:,.2f}'
            
            documents_to_add.append({
                'id': doc_id,
                'content': content,
                'metadata': {
                    'user_id': 1,
                    'type': 'financial_entry',
                    'category': str(entry.category),
                    'subcategory': str(entry.subcategory),
                    'amount': float(entry.amount),
                    'timestamp': datetime.now().isoformat()
                }
            })
        
        # Index each goal as a separate document  
        for goal in goals:
            doc_id = f'user_1_goal_{goal.goal_id}'
            content = f'Goal: {goal.name} Target: ${goal.target_amount:,.2f} Category: {goal.category}'
            
            documents_to_add.append({
                'id': doc_id,
                'content': content,
                'metadata': {
                    'user_id': 1,
                    'type': 'goal',
                    'category': goal.category,
                    'target_amount': float(goal.target_amount),
                    'timestamp': datetime.now().isoformat()
                }
            })
        
        print(f'📋 Prepared {len(documents_to_add)} documents to index')
        
        # Add all documents to vector database
        added_count = 0
        for doc in documents_to_add:
            try:
                vector_db.collection.add(
                    ids=[doc['id']],
                    documents=[doc['content']],
                    metadatas=[doc['metadata']]
                )
                added_count += 1
            except Exception as e:
                print(f'❌ Error adding document {doc["id"]}: {e}')
        
        print(f'✅ Successfully added {added_count} documents')
        
        # Final count check
        final_docs = vector_db.collection.get(where={'user_id': 1})
        final_count = len(final_docs.get('ids', []))
        print(f'📊 FINAL TOTAL DOCUMENTS: {final_count}')
        
        if final_count >= 40:
            print('🎉 SUCCESS: Full recovery achieved!')
        else:
            print(f'⚠️  Still need more documents: {final_count}/48 target')
        
except Exception as e:
    print(f'❌ ERROR: {e}')
    import traceback
    traceback.print_exc()