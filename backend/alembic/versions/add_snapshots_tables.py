"""Add financial snapshots tables

Revision ID: add_snapshots_001
Revises: 
Create Date: 2024-01-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_snapshots_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create financial_snapshots table
    op.create_table('financial_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('snapshot_date', sa.Date(), server_default=sa.text('CURRENT_DATE'), nullable=True),
        sa.Column('snapshot_name', sa.String(length=255), nullable=True),
        sa.Column('net_worth', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('total_assets', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('total_liabilities', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('monthly_income', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('monthly_expenses', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('savings_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('employment_status', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_financial_snapshots_id'), 'financial_snapshots', ['id'], unique=False)
    op.create_index(op.f('ix_financial_snapshots_user_id'), 'financial_snapshots', ['user_id'], unique=False)

    # Create snapshot_entries table
    op.create_table('snapshot_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('snapshot_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('subcategory', sa.String(length=50), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('institution', sa.String(length=255), nullable=True),
        sa.Column('account_type', sa.String(length=50), nullable=True),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('interest_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('asset_allocation', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['snapshot_id'], ['financial_snapshots.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create snapshot_goals table
    op.create_table('snapshot_goals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('snapshot_id', sa.Integer(), nullable=False),
        sa.Column('goal_name', sa.String(length=255), nullable=False),
        sa.Column('target_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('current_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('target_date', sa.Date(), nullable=True),
        sa.Column('completion_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.ForeignKeyConstraint(['snapshot_id'], ['financial_snapshots.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('snapshot_goals')
    op.drop_table('snapshot_entries')
    op.drop_index(op.f('ix_financial_snapshots_user_id'), table_name='financial_snapshots')
    op.drop_index(op.f('ix_financial_snapshots_id'), table_name='financial_snapshots')
    op.drop_table('financial_snapshots')