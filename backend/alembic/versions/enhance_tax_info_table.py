"""enhance tax info table

Revision ID: enhance_tax_info_table
Revises: enhance_benefits_table
Create Date: 2025-08-29 03:25:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'enhance_tax_info_table'
down_revision = 'enhance_benefits_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add enhanced tax info columns for advanced tax optimization"""
    
    # Add state tax and optimization columns
    op.add_column('user_tax_info', sa.Column('state_tax_rate', sa.Numeric(5, 2), nullable=True))
    op.add_column('user_tax_info', sa.Column('charitable_giving_annual', sa.Numeric(10, 2), nullable=True))
    op.add_column('user_tax_info', sa.Column('tax_loss_harvesting_enabled', sa.Boolean(), nullable=True, default=False))
    op.add_column('user_tax_info', sa.Column('backdoor_roth_eligible', sa.Boolean(), nullable=True, default=False))
    op.add_column('user_tax_info', sa.Column('itemized_deduction_total', sa.Numeric(10, 2), nullable=True))
    
    # Add business income details (JSONB for flexibility)
    op.add_column('user_tax_info', sa.Column('business_income_details', postgresql.JSONB(), nullable=True))
    
    # Add additional advanced tax strategy columns
    op.add_column('user_tax_info', sa.Column('mega_backdoor_roth_available', sa.Boolean(), nullable=True, default=False))
    op.add_column('user_tax_info', sa.Column('state_tax_deductions', postgresql.JSONB(), nullable=True))
    op.add_column('user_tax_info', sa.Column('tax_planning_strategies', postgresql.JSONB(), nullable=True))
    
    # Add indexes for better query performance
    op.create_index('ix_user_tax_info_state_tax_rate', 'user_tax_info', ['state_tax_rate'])
    op.create_index('ix_user_tax_info_tax_year_enhanced', 'user_tax_info', ['tax_year'])
    op.create_index('ix_user_tax_info_backdoor_roth_eligible', 'user_tax_info', ['backdoor_roth_eligible'])


def downgrade() -> None:
    """Remove enhanced tax info columns"""
    
    # Drop indexes
    op.drop_index('ix_user_tax_info_backdoor_roth_eligible')
    op.drop_index('ix_user_tax_info_tax_year_enhanced')
    op.drop_index('ix_user_tax_info_state_tax_rate')
    
    # Drop added columns
    op.drop_column('user_tax_info', 'tax_planning_strategies')
    op.drop_column('user_tax_info', 'state_tax_deductions')
    op.drop_column('user_tax_info', 'mega_backdoor_roth_available')
    op.drop_column('user_tax_info', 'business_income_details')
    op.drop_column('user_tax_info', 'itemized_deduction_total')
    op.drop_column('user_tax_info', 'backdoor_roth_eligible')
    op.drop_column('user_tax_info', 'tax_loss_harvesting_enabled')
    op.drop_column('user_tax_info', 'charitable_giving_annual')
    op.drop_column('user_tax_info', 'state_tax_rate')