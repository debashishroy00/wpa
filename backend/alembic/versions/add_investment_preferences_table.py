"""add investment preferences table

Revision ID: add_investment_preferences
Revises: 6a6755c48c09
Create Date: 2025-08-29 02:25:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = 'add_investment_preferences'
down_revision = '6a6755c48c09'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add investment preferences table"""
    op.create_table(
        'user_investment_preferences',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('risk_tolerance_score', sa.Integer(), nullable=True),
        sa.Column('investment_timeline_years', sa.Integer(), nullable=True),
        sa.Column('rebalancing_frequency', sa.String(20), nullable=True),
        sa.Column('investment_philosophy', sa.String(50), nullable=True),
        sa.Column('esg_preference_level', sa.Integer(), nullable=True),
        sa.Column('international_allocation_target', sa.Numeric(5, 2), nullable=True),
        sa.Column('alternative_investment_interest', sa.Boolean(), default=False),
        sa.Column('cryptocurrency_allocation', sa.Numeric(5, 2), nullable=True),
        sa.Column('individual_stock_tolerance', sa.Boolean(), default=False),
        sa.Column('tax_loss_harvesting_enabled', sa.Boolean(), default=False),
        sa.Column('dollar_cost_averaging_preference', sa.Boolean(), default=True),
        sa.Column('sector_preferences', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'), onupdate=sa.text('NOW()')),
    )
    
    # Add indexes for better query performance
    op.create_index('ix_investment_preferences_user_id', 'user_investment_preferences', ['user_id'])
    op.create_index('ix_investment_preferences_risk_score', 'user_investment_preferences', ['risk_tolerance_score'])


def downgrade() -> None:
    """Drop investment preferences table"""
    op.drop_index('ix_investment_preferences_risk_score')
    op.drop_index('ix_investment_preferences_user_id')
    op.drop_table('user_investment_preferences')