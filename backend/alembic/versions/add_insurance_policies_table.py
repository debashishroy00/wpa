"""add insurance policies table

Revision ID: add_insurance_policies
Revises: add_chat_session_tables
Create Date: 2025-08-28 23:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = 'add_insurance_policies'
down_revision = 'add_chat_session_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add insurance policies table"""
    op.create_table(
        'user_insurance_policies',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('policy_type', sa.String(50), nullable=False),
        sa.Column('policy_name', sa.String(100), nullable=False),
        sa.Column('coverage_amount', sa.Numeric(12, 2), nullable=True),
        sa.Column('annual_premium', sa.Numeric(8, 2), nullable=True),
        sa.Column('beneficiary_primary', sa.String(100), nullable=True),
        sa.Column('beneficiary_secondary', sa.String(100), nullable=True),
        sa.Column('policy_details', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'), onupdate=sa.text('NOW()')),
    )
    
    # Add indexes for better query performance
    op.create_index('ix_insurance_policies_user_id', 'user_insurance_policies', ['user_id'])
    op.create_index('ix_insurance_policies_type', 'user_insurance_policies', ['policy_type'])


def downgrade() -> None:
    """Drop insurance policies table"""
    op.drop_index('ix_insurance_policies_type')
    op.drop_index('ix_insurance_policies_user_id')
    op.drop_table('user_insurance_policies')