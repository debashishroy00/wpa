"""Fix data integrity constraints

Revision ID: fix_data_integrity_001
Revises: 
Create Date: 2025-01-08 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fix_data_integrity_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add database-level constraints to prevent data integrity issues
    This prevents duplicate accounts and ensures data quality
    """
    
    # 1. Clean up existing duplicate active accounts first
    print("Cleaning up existing duplicate accounts...")
    
    # Deactivate older duplicate entries, keeping the most recent one
    op.execute("""
        WITH duplicates AS (
            SELECT 
                id,
                ROW_NUMBER() OVER (
                    PARTITION BY user_id, category, LOWER(TRIM(description)) 
                    ORDER BY created_at DESC
                ) as rn
            FROM financial_entries 
            WHERE category = 'assets' 
                AND is_active = true
        )
        UPDATE financial_entries 
        SET is_active = false,
            updated_at = NOW()
        WHERE id IN (
            SELECT id FROM duplicates WHERE rn > 1
        );
    """)
    
    # 2. Add unique constraint to prevent duplicate active accounts
    print("Adding unique constraint for active accounts...")
    
    # Create a partial unique index that only applies to active records
    op.execute("""
        CREATE UNIQUE INDEX CONCURRENTLY idx_unique_active_accounts 
        ON financial_entries (user_id, category, LOWER(TRIM(description))) 
        WHERE is_active = true AND category = 'assets';
    """)
    
    # 3. Add check constraints for data quality
    print("Adding data quality constraints...")
    
    # Ensure asset amounts are not negative (except for specific cases)
    op.execute("""
        ALTER TABLE financial_entries 
        ADD CONSTRAINT chk_asset_amounts_positive 
        CHECK (
            category != 'assets' OR 
            amount >= 0 OR 
            description ILIKE '%loss%' OR 
            description ILIKE '%depreciation%'
        );
    """)
    
    # Ensure reasonable amount limits (catch data entry errors)
    op.execute("""
        ALTER TABLE financial_entries 
        ADD CONSTRAINT chk_reasonable_amounts 
        CHECK (amount BETWEEN -100000000 AND 100000000);
    """)
    
    # 4. Add constraints for user profiles
    print("Adding user profile constraints...")
    
    # Ensure reasonable age limits
    op.execute("""
        ALTER TABLE user_profiles 
        ADD CONSTRAINT chk_reasonable_age 
        CHECK (age IS NULL OR (age >= 16 AND age <= 120));
    """)
    
    # 5. Add constraints for financial goals
    print("Adding financial goal constraints...")
    
    # Ensure goal amounts are positive
    op.execute("""
        ALTER TABLE financial_goals 
        ADD CONSTRAINT chk_positive_goal_amounts 
        CHECK (target_amount > 0);
    """)
    
    # Ensure target dates are in the future (at time of creation)
    op.execute("""
        ALTER TABLE financial_goals 
        ADD CONSTRAINT chk_future_target_dates 
        CHECK (target_date > created_at::date);
    """)
    
    # 6. Create indexes for better performance
    print("Creating performance indexes...")
    
    # Index for common queries
    op.create_index(
        'idx_financial_entries_user_category_active',
        'financial_entries',
        ['user_id', 'category', 'is_active']
    )
    
    op.create_index(
        'idx_financial_entries_subcategory',
        'financial_entries',
        ['subcategory']
    )
    
    op.create_index(
        'idx_financial_goals_user_type',
        'financial_goals',
        ['user_id', 'goal_type']
    )
    
    print("Data integrity constraints applied successfully!")


def downgrade() -> None:
    """
    Remove the constraints and indexes added in upgrade()
    """
    
    # Remove indexes
    op.drop_index('idx_financial_goals_user_type')
    op.drop_index('idx_financial_entries_subcategory')
    op.drop_index('idx_financial_entries_user_category_active')
    
    # Remove constraints
    op.execute("ALTER TABLE financial_goals DROP CONSTRAINT IF EXISTS chk_future_target_dates;")
    op.execute("ALTER TABLE financial_goals DROP CONSTRAINT IF EXISTS chk_positive_goal_amounts;")
    op.execute("ALTER TABLE user_profiles DROP CONSTRAINT IF EXISTS chk_reasonable_age;")
    op.execute("ALTER TABLE financial_entries DROP CONSTRAINT IF EXISTS chk_reasonable_amounts;")
    op.execute("ALTER TABLE financial_entries DROP CONSTRAINT IF EXISTS chk_asset_amounts_positive;")
    
    # Remove unique index
    op.execute("DROP INDEX IF EXISTS idx_unique_active_accounts;")
    
    print("Data integrity constraints removed!")