"""Remove hard-coded defaults from user_profile goals and social security

Revision ID: 01545a03be48
Revises: f48f17208b06
Create Date: 2025-09-11 17:44:55.672654

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '01545a03be48'
down_revision = 'f48f17208b06'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Safe migration to remove hard-coded defaults from user_profile.
    
    PRODUCTION SAFETY MEASURES:
    1. Preserves all existing data
    2. Only removes defaults, doesn't change existing values
    3. Makes columns nullable to allow user customization
    4. No data loss risk
    """
    
    # Remove default from retirement_goal (make nullable for user customization)
    # This allows users to set their own retirement goals instead of using $3.5M
    op.alter_column('user_profiles', 'retirement_goal',
                    existing_type=sa.Numeric(12, 2),
                    nullable=True,
                    # Remove the default=3500000, keeping existing values
                    server_default=None)
    
    # Remove default from social_security_monthly (make nullable for user input)  
    # This allows users to enter their actual SS estimates instead of using $4000
    op.alter_column('user_profiles', 'social_security_monthly',
                    existing_type=sa.Numeric(12, 2),
                    nullable=True,
                    # Remove the default=4000, keeping existing values
                    server_default=None)


def downgrade() -> None:
    """
    Rollback migration - restore the hard-coded defaults.
    Only use if absolutely necessary as this re-introduces the hard-coding issue.
    """
    
    # Restore retirement_goal default (re-introduces hard-coding issue)
    op.alter_column('user_profiles', 'retirement_goal',
                    existing_type=sa.Numeric(12, 2),
                    nullable=False,
                    server_default='3500000')
    
    # Restore social_security_monthly default (re-introduces hard-coding issue)
    op.alter_column('user_profiles', 'social_security_monthly',
                    existing_type=sa.Numeric(12, 2),
                    nullable=False,
                    server_default='4000')