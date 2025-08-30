"""enhance benefits table

Revision ID: enhance_benefits_table
Revises: add_investment_preferences
Create Date: 2025-08-29 03:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'enhance_benefits_table'
down_revision = 'add_investment_preferences'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add enhanced benefits columns for advanced retirement planning"""
    
    # Add Social Security enhancement columns
    op.add_column('user_benefits', sa.Column('social_security_estimated_benefit', sa.Numeric(8, 2), nullable=True))
    op.add_column('user_benefits', sa.Column('social_security_claiming_age', sa.Integer(), nullable=True))
    
    # Add 401k enhancement columns
    op.add_column('user_benefits', sa.Column('employer_401k_match_formula', sa.String(200), nullable=True))
    op.add_column('user_benefits', sa.Column('employer_401k_vesting_schedule', sa.String(200), nullable=True))
    
    # Add pension and other benefits details (JSONB for flexibility)
    op.add_column('user_benefits', sa.Column('pension_details', postgresql.JSONB(), nullable=True))
    op.add_column('user_benefits', sa.Column('other_benefits', postgresql.JSONB(), nullable=True))
    
    # Add indexes for better query performance
    op.create_index('ix_user_benefits_social_security_claiming_age', 'user_benefits', ['social_security_claiming_age'])
    op.create_index('ix_user_benefits_benefit_type_enhanced', 'user_benefits', ['benefit_type'])


def downgrade() -> None:
    """Remove enhanced benefits columns"""
    
    # Drop indexes
    op.drop_index('ix_user_benefits_benefit_type_enhanced')
    op.drop_index('ix_user_benefits_social_security_claiming_age')
    
    # Drop added columns
    op.drop_column('user_benefits', 'other_benefits')
    op.drop_column('user_benefits', 'pension_details')
    op.drop_column('user_benefits', 'employer_401k_vesting_schedule')
    op.drop_column('user_benefits', 'employer_401k_match_formula')
    op.drop_column('user_benefits', 'social_security_claiming_age')
    op.drop_column('user_benefits', 'social_security_estimated_benefit')