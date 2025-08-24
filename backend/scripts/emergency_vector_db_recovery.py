#!/usr/bin/env python3
"""
🚑 EMERGENCY VECTOR DATABASE RECOVERY SCRIPT
Restores missing documents after destructive API call caused data loss (48→7 documents)

USAGE:
    python3 scripts/emergency_vector_db_recovery.py --user-id 1 --restore
    python3 scripts/emergency_vector_db_recovery.py --user-id 1 --check-only
    
SAFETY:
    - Never deletes existing data
    - Only adds missing documents
    - Creates backup before any changes
    - Verifies recovery completion
"""

import sys
import os
import asyncio
import argparse
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Now we can import our services
from app.services.vector_db_service import get_vector_db
from app.services.financial_summary_service import FinancialSummaryService
from app.db.session import SessionLocal
from app.models.user import User
import structlog

logger = structlog.get_logger(__name__)

class VectorDBRecoveryService:
    """Emergency recovery service for vector database data loss"""
    
    def __init__(self):
        self.vector_db = get_vector_db()
        self.financial_service = FinancialSummaryService()
    
    async def check_user_documents(self, user_id: int) -> dict:
        """Check current document status for user"""
        try:
            # Get current documents
            current_docs = self.vector_db.collection.get(where={"user_id": user_id})
            current_count = len(current_docs.get('ids', []))
            
            # Get categories
            categories = {}
            for metadata in current_docs.get('metadatas', []):
                category = metadata.get('category', 'unknown')
                categories[category] = categories.get(category, 0) + 1
            
            return {
                "user_id": user_id,
                "current_document_count": current_count,
                "categories": categories,
                "documents": current_docs,
                "status": "healthy" if current_count >= 40 else "data_loss_detected" if current_count < 20 else "warning"
            }
        except Exception as e:
            logger.error(f"Failed to check user documents: {e}")
            return {"user_id": user_id, "error": str(e), "status": "error"}
    
    async def generate_comprehensive_documents(self, user_id: int, db_session) -> list:
        """Generate all expected documents for user from source data"""
        try:
            # Get comprehensive financial data
            summary = await self.financial_service.get_user_financial_summary(user_id, db_session)
            
            documents = []
            
            # Generate all document types that should exist
            documents.extend(self._generate_profile_documents(user_id, summary))
            documents.extend(self._generate_financial_documents(user_id, summary))
            documents.extend(self._generate_goal_documents(user_id, summary))
            documents.extend(self._generate_calculation_documents(user_id, summary))
            
            logger.info(f"Generated {len(documents)} documents for recovery")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to generate documents: {e}")
            return []
    
    def _generate_profile_documents(self, user_id: int, summary: dict) -> list:
        """Generate profile-related documents"""
        documents = []
        
        if 'personal_info' in summary:
            personal = summary['personal_info']
            documents.append({
                'id': f"profile_personal_{user_id}",
                'content': f"User Profile: {personal.get('name', 'Unknown')} (Age: {personal.get('age', 'N/A')})",
                'metadata': {
                    'user_id': user_id,
                    'category': 'profile',
                    'subcategory': 'personal',
                    'type': 'personal_info'
                }
            })
        
        if 'employment' in summary:
            employment = summary['employment']
            documents.append({
                'id': f"profile_employment_{user_id}",
                'content': f"Employment: {employment.get('occupation', 'N/A')} - Annual Income: ${employment.get('annual_income', 0):,}",
                'metadata': {
                    'user_id': user_id,
                    'category': 'profile', 
                    'subcategory': 'employment',
                    'type': 'employment_info'
                }
            })
        
        return documents
    
    def _generate_financial_documents(self, user_id: int, summary: dict) -> list:
        """Generate financial data documents"""
        documents = []
        
        # Net worth summary
        if 'net_worth' in summary:
            documents.append({
                'id': f"financial_net_worth_{user_id}",
                'content': f"Net Worth: ${summary['net_worth']:,} (Assets: ${summary.get('total_assets', 0):,}, Liabilities: ${summary.get('total_liabilities', 0):,})",
                'metadata': {
                    'user_id': user_id,
                    'category': 'financial',
                    'subcategory': 'net_worth',
                    'type': 'summary'
                }
            })
        
        # Cash flow
        if 'monthly_surplus' in summary:
            documents.append({
                'id': f"financial_cash_flow_{user_id}",
                'content': f"Monthly Cash Flow: ${summary['monthly_surplus']:,} surplus (Income: ${summary.get('monthly_income', 0):,}, Expenses: ${summary.get('monthly_expenses', 0):,})",
                'metadata': {
                    'user_id': user_id,
                    'category': 'financial',
                    'subcategory': 'cash_flow', 
                    'type': 'monthly_summary'
                }
            })
        
        # Asset categories
        for asset_type in ['checking', 'savings', 'investments', 'retirement', 'real_estate']:
            if asset_type in summary and summary[asset_type] > 0:
                documents.append({
                    'id': f"asset_{asset_type}_{user_id}",
                    'content': f"{asset_type.title().replace('_', ' ')}: ${summary[asset_type]:,}",
                    'metadata': {
                        'user_id': user_id,
                        'category': 'assets',
                        'subcategory': asset_type,
                        'type': 'asset_balance'
                    }
                })
        
        return documents
    
    def _generate_goal_documents(self, user_id: int, summary: dict) -> list:
        """Generate goal-related documents"""
        documents = []
        
        # Retirement goals
        if 'retirement' in summary:
            retirement = summary['retirement']
            documents.append({
                'id': f"goal_retirement_{user_id}",
                'content': f"Retirement Goal: Target ${retirement.get('target_amount', 0):,} by age {retirement.get('target_age', 65)} - Currently {retirement.get('completion_percentage', 0):.1f}% funded",
                'metadata': {
                    'user_id': user_id,
                    'category': 'goals',
                    'subcategory': 'retirement',
                    'type': 'retirement_planning'
                }
            })
        
        return documents
    
    def _generate_calculation_documents(self, user_id: int, summary: dict) -> list:
        """Generate calculation and ratio documents"""
        documents = []
        
        # Financial ratios
        if 'debt_to_income_ratio' in summary:
            documents.append({
                'id': f"ratio_dti_{user_id}",
                'content': f"Debt-to-Income Ratio: {summary['debt_to_income_ratio']:.1f}% ({'Excellent' if summary['debt_to_income_ratio'] < 20 else 'Good' if summary['debt_to_income_ratio'] < 36 else 'Needs Improvement'})",
                'metadata': {
                    'user_id': user_id,
                    'category': 'ratios',
                    'subcategory': 'debt_analysis',
                    'type': 'financial_ratio'
                }
            })
        
        # Savings rate
        if 'savings_rate' in summary:
            documents.append({
                'id': f"ratio_savings_{user_id}",
                'content': f"Savings Rate: {summary['savings_rate']:.1f}% of income ({'Excellent' if summary['savings_rate'] > 20 else 'Good' if summary['savings_rate'] > 10 else 'Needs Improvement'})",
                'metadata': {
                    'user_id': user_id,
                    'category': 'ratios',
                    'subcategory': 'savings_analysis',
                    'type': 'financial_ratio'
                }
            })
        
        return documents
    
    async def restore_missing_documents(self, user_id: int, force: bool = False) -> dict:
        """Restore missing documents for user"""
        try:
            # Step 1: Check current status
            current_status = await self.check_user_documents(user_id)
            current_count = current_status['current_document_count']
            
            logger.info(f"Current document count for user {user_id}: {current_count}")
            
            # Step 2: Create backup of existing data
            backup = self.vector_db.backup_user_data(user_id)
            logger.info(f"Created backup of {backup['document_count']} existing documents")
            
            # Step 3: Generate fresh documents from source data
            with SessionLocal() as db:
                new_documents = await self.generate_comprehensive_documents(user_id, db)
            
            if not new_documents:
                return {"status": "error", "message": "Could not generate documents from source data"}
            
            # Step 4: Add new documents (without deleting existing ones)
            existing_ids = set(current_status['documents'].get('ids', []))
            documents_added = 0
            
            for doc in new_documents:
                if doc['id'] not in existing_ids:
                    try:
                        self.vector_db.collection.add(
                            ids=[doc['id']],
                            documents=[doc['content']],
                            metadatas=[doc['metadata']]
                        )
                        documents_added += 1
                    except Exception as e:
                        logger.warning(f"Failed to add document {doc['id']}: {e}")
            
            # Step 5: Verify recovery
            final_status = await self.check_user_documents(user_id)
            final_count = final_status['current_document_count']
            
            recovery_result = {
                "user_id": user_id,
                "recovery_timestamp": datetime.now().isoformat(),
                "before_count": current_count,
                "after_count": final_count,
                "documents_added": documents_added,
                "backup_created": backup['document_count'],
                "status": "success" if final_count > current_count else "partial",
                "categories_after": final_status['categories']
            }
            
            logger.info(f"Recovery complete: {recovery_result}")
            return recovery_result
            
        except Exception as e:
            logger.error(f"Recovery failed: {e}")
            return {"status": "error", "error": str(e)}

async def main():
    """Main recovery script"""
    parser = argparse.ArgumentParser(description='Emergency Vector DB Recovery')
    parser.add_argument('--user-id', type=int, required=True, help='User ID to recover')
    parser.add_argument('--restore', action='store_true', help='Actually restore documents')
    parser.add_argument('--check-only', action='store_true', help='Only check current status')
    parser.add_argument('--force', action='store_true', help='Force recovery even if docs exist')
    
    args = parser.parse_args()
    
    recovery_service = VectorDBRecoveryService()
    
    print(f"🚑 EMERGENCY VECTOR DB RECOVERY")
    print(f"User ID: {args.user_id}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 50)
    
    # Check current status
    print("📊 Checking current document status...")
    status = await recovery_service.check_user_documents(args.user_id)
    
    print(f"Current Documents: {status['current_document_count']}")
    print(f"Status: {status['status']}")
    print(f"Categories: {status.get('categories', {})}")
    
    if args.check_only:
        print("✅ Check complete - no changes made")
        return
    
    if args.restore:
        if status['current_document_count'] >= 40 and not args.force:
            print("⚠️  User already has sufficient documents (40+). Use --force to proceed anyway.")
            return
        
        print("🚑 Starting document recovery...")
        result = await recovery_service.restore_missing_documents(args.user_id, args.force)
        
        print("🎯 RECOVERY RESULTS:")
        print(f"Before: {result.get('before_count', 0)} documents")
        print(f"After: {result.get('after_count', 0)} documents")
        print(f"Added: {result.get('documents_added', 0)} documents")
        print(f"Status: {result.get('status', 'unknown')}")
        
        if result.get('status') == 'success':
            print("✅ Recovery completed successfully!")
        else:
            print("⚠️  Recovery completed with warnings")
    
    else:
        print("Use --restore to actually restore documents or --check-only to just check status")

if __name__ == "__main__":
    asyncio.run(main())