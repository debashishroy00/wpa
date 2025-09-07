"""Add missing user_benefits columns for production deployment

Revision ID: prod_benefits_fix
Revises: 5beed2bb881f, social_security_fix
Create Date: 2025-01-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'prod_benefits_fix'
down_revision = ('5beed2bb881f', 'social_security_fix')
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add all missing columns that exist in the SQLAlchemy model but not in production database"""
    
    # Check if columns exist before adding them (production database may have some)
    
    # Social Security fields (may already exist from social_security_fix migration)
    try:
        op.add_column('user_benefits', sa.Column('social_security_estimated_benefit', sa.Numeric(precision=8, scale=2), nullable=True))
    except Exception:
        pass  # Column may already exist
    
    try:
        op.add_column('user_benefits', sa.Column('social_security_claiming_age', sa.Integer(), nullable=True))
    except Exception:
        pass  # Column may already exist
    
    # 401k and employer benefit fields
    try:
        op.add_column('user_benefits', sa.Column('employer_401k_match_formula', sa.String(length=200), nullable=True))
    except Exception:
        pass  # Column may already exist
    
    try:
        op.add_column('user_benefits', sa.Column('employer_401k_vesting_schedule', sa.String(length=200), nullable=True))
    except Exception:
        pass  # Column may already exist
    
    try:
        op.add_column('user_benefits', sa.Column('max_401k_contribution', sa.Numeric(precision=12, scale=2), nullable=True))
    except Exception:
        pass  # Column may already exist
    
    # Additional benefit detail fields
    try:
        op.add_column('user_benefits', sa.Column('pension_details', sa.Text(), nullable=True))
    except Exception:
        pass  # Column may already exist
    
    try:
        op.add_column('user_benefits', sa.Column('other_benefits', sa.Text(), nullable=True))
    except Exception:
        pass  # Column may already exist
    
    # Notes field (may already exist)
    try:
        op.add_column('user_benefits', sa.Column('notes', sa.Text(), nullable=True))
    except Exception:
        pass  # Column may already exist


def downgrade() -> None:
    """Remove the added columns"""
    
    # Remove columns in reverse order
    try:
        op.drop_column('user_benefits', 'notes')
    except Exception:
        pass
    
    try:
        op.drop_column('user_benefits', 'other_benefits')
    except Exception:
        pass
    
    try:
        op.drop_column('user_benefits', 'pension_details')
    except Exception:
        pass
    
    try:
        op.drop_column('user_benefits', 'max_401k_contribution')
    except Exception:
        pass
    
    try:
        op.drop_column('user_benefits', 'employer_401k_vesting_schedule')
    except Exception:
        pass
    
    try:
        op.drop_column('user_benefits', 'employer_401k_match_formula')
    except Exception:
        pass
    
    try:
        op.drop_column('user_benefits', 'social_security_claiming_age')
    except Exception:
        pass
    
    try:
        op.drop_column('user_benefits', 'social_security_estimated_benefit')
    except Exception:
        pass