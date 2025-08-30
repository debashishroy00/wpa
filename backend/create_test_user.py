#!/usr/bin/env python3
"""
Create test user with sample financial data
This will NOT affect debashishroy@gmail.com
"""
import sys
import os
sys.path.append('/mnt/c/projects/wpa/backend')

from datetime import datetime, timezone
from decimal import Decimal
from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.user import User
from app.models.financial import FinancialEntry, EntryCategory

def create_test_user_with_data():
    """Create debashishroy@gmail.com with sample financial data"""
    db = SessionLocal()
    
    try:
        print("🔍 Creating test user with sample financial data...")
        
        # Check if debashishroy user exists
        test_user = db.query(User).filter(User.email == "debashishroy@gmail.com").first()
        
        if not test_user:
            # Create test user
            test_user = User(
                email="debashishroy@gmail.com",
                first_name="Test",
                last_name="User",
                password_hash=get_password_hash("password123"),
                is_active=True
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            print(f"✅ Created test user: {test_user.email} (ID: {test_user.id})")
        else:
            print(f"✅ Test user exists: {test_user.email} (ID: {test_user.id})")
        
        # Check if user already has financial data
        existing_entries = db.query(FinancialEntry).filter(FinancialEntry.user_id == test_user.id).count()
        
        if existing_entries > 0:
            print(f"ℹ️  Test user already has {existing_entries} financial entries")
            return test_user
            
        print("💰 Adding sample financial data...")
        
        # Sample financial entries
        sample_entries = [
            # Assets
            {
                "entry_name": "Checking Account",
                "category": EntryCategory.CASH,
                "amount": Decimal("15000.00"),
                "is_asset": True,
                "description": "Primary checking account"
            },
            {
                "entry_name": "Savings Account", 
                "category": EntryCategory.CASH,
                "amount": Decimal("45000.00"),
                "is_asset": True,
                "description": "High yield savings"
            },
            {
                "entry_name": "401k Retirement",
                "category": EntryCategory.RETIREMENT,
                "amount": Decimal("125000.00"),
                "is_asset": True,
                "description": "Company 401k plan"
            },
            {
                "entry_name": "Stock Portfolio",
                "category": EntryCategory.INVESTMENT,
                "amount": Decimal("75000.00"),
                "is_asset": True,
                "description": "Individual stock holdings"
            },
            {
                "entry_name": "Primary Residence",
                "category": EntryCategory.REAL_ESTATE,
                "amount": Decimal("450000.00"),
                "is_asset": True,
                "description": "Home value"
            },
            
            # Liabilities
            {
                "entry_name": "Mortgage",
                "category": EntryCategory.DEBT,
                "amount": Decimal("285000.00"),
                "is_asset": False,
                "description": "Home mortgage remaining"
            },
            {
                "entry_name": "Car Loan",
                "category": EntryCategory.DEBT,
                "amount": Decimal("18500.00"),
                "is_asset": False,
                "description": "Auto loan balance"
            },
            {
                "entry_name": "Credit Card",
                "category": EntryCategory.DEBT,
                "amount": Decimal("3200.00"),
                "is_asset": False,
                "description": "Credit card debt"
            }
        ]
        
        # Add entries to database
        for entry_data in sample_entries:
            entry = FinancialEntry(
                user_id=test_user.id,
                entry_name=entry_data["entry_name"],
                category=entry_data["category"],
                amount=entry_data["amount"],
                is_asset=entry_data["is_asset"],
                description=entry_data["description"],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(entry)
        
        db.commit()
        
        # Calculate totals
        total_assets = sum(e["amount"] for e in sample_entries if e["is_asset"])
        total_liabilities = sum(e["amount"] for e in sample_entries if not e["is_asset"])
        net_worth = total_assets - total_liabilities
        
        print(f"✅ Added {len(sample_entries)} financial entries")
        print(f"📊 Sample Financial Summary:")
        print(f"   💰 Total Assets: ${total_assets:,.2f}")
        print(f"   💸 Total Liabilities: ${total_liabilities:,.2f}")
        print(f"   🎯 Net Worth: ${net_worth:,.2f}")
        print(f"\n🔐 Login credentials:")
        print(f"   📧 Email: test@gmail.com")
        print(f"   🔑 Password: password123")
        
        return test_user
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("WealthPath AI - Test User Creation")
    print("=" * 60)
    
    user = create_test_user_with_data()
    
    if user:
        print("\n✅ Test user setup complete!")
        print("You can now test the application with realistic financial data.")
        print("\nTo test:")
        print("1. Login with test@gmail.com / password123")
        print("2. Navigate to financial dashboard")
        print("3. Test projections and chat features")
    else:
        print("\n❌ Failed to create test user")
        
    print("\n" + "=" * 60)