"""Production fix for user_benefits missing columns

Revision ID: prod_fix_2025
Revises: 5beed2bb881f
Create Date: 2025-01-07 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'prod_fix_2025'
down_revision = '5beed2bb881f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add missing columns for production deployment"""
    
    # Use IF NOT EXISTS to avoid conflicts with existing columns
    connection = op.get_bind()
    
    # Check and add each column only if it doesn't exist
    columns_to_add = [
        ('social_security_estimated_benefit', 'NUMERIC(8, 2)'),
        ('social_security_claiming_age', 'INTEGER'),
        ('employer_401k_match_formula', 'VARCHAR(200)'),
        ('employer_401k_vesting_schedule', 'VARCHAR(200)'),
        ('max_401k_contribution', 'NUMERIC(12, 2)'),
        ('pension_details', 'TEXT'),
        ('other_benefits', 'TEXT'),
        ('notes', 'TEXT')
    ]
    
    for column_name, column_type in columns_to_add:
        try:
            connection.execute(sa.text(f"""
                ALTER TABLE user_benefits 
                ADD COLUMN IF NOT EXISTS {column_name} {column_type}
            """))
        except Exception as e:
            print(f"Column {column_name} may already exist: {e}")


def downgrade() -> None:
    """Remove the added columns"""
    
    # Remove columns if they exist
    connection = op.get_bind()
    
    columns_to_remove = [
        'notes',
        'other_benefits', 
        'pension_details',
        'max_401k_contribution',
        'employer_401k_vesting_schedule',
        'employer_401k_match_formula',
        'social_security_claiming_age',
        'social_security_estimated_benefit'
    ]
    
    for column_name in columns_to_remove:
        try:
            connection.execute(sa.text(f"""
                ALTER TABLE user_benefits 
                DROP COLUMN IF EXISTS {column_name}
            """))
        except Exception as e:
            print(f"Column {column_name} may not exist: {e}")