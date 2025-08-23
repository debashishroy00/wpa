"""Add asset breakdown columns to financial_entries

Revision ID: add_asset_breakdown
Revises: 6ab6b908bdb7
Create Date: 2025-08-15 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_asset_breakdown'
down_revision = '6ab6b908bdb7'
branch_labels = None
depends_on = None


def upgrade():
    """Add asset breakdown columns for mixed investments"""
    # Add new columns to financial_entries table
    op.add_column('financial_entries', sa.Column('stock_percentage', sa.Integer(), nullable=True, default=0))
    op.add_column('financial_entries', sa.Column('bond_percentage', sa.Integer(), nullable=True, default=0))
    op.add_column('financial_entries', sa.Column('cash_percentage', sa.Integer(), nullable=True, default=0))
    op.add_column('financial_entries', sa.Column('other_percentage', sa.Integer(), nullable=True, default=0))


def downgrade():
    """Remove asset breakdown columns"""
    op.drop_column('financial_entries', 'other_percentage')
    op.drop_column('financial_entries', 'cash_percentage')
    op.drop_column('financial_entries', 'bond_percentage')
    op.drop_column('financial_entries', 'stock_percentage')