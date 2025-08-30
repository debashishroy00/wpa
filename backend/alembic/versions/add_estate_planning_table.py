"""add estate planning table

Revision ID: add_estate_planning
Revises: add_insurance_policies
Create Date: 2025-08-28 23:54:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = 'add_estate_planning'
down_revision = 'add_insurance_policies'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add estate planning table"""
    op.create_table(
        'user_estate_planning',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_type', sa.String(50), nullable=False),
        sa.Column('document_name', sa.String(100), nullable=False),
        sa.Column('status', sa.String(30), nullable=False),
        sa.Column('last_updated', sa.Date(), nullable=True),
        sa.Column('next_review_date', sa.Date(), nullable=True),
        sa.Column('attorney_contact', sa.String(200), nullable=True),
        sa.Column('document_location', sa.String(200), nullable=True),
        sa.Column('document_details', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'), onupdate=sa.text('NOW()')),
    )
    
    # Add indexes for better query performance
    op.create_index('ix_estate_planning_user_id', 'user_estate_planning', ['user_id'])
    op.create_index('ix_estate_planning_document_type', 'user_estate_planning', ['document_type'])
    op.create_index('ix_estate_planning_status', 'user_estate_planning', ['status'])


def downgrade() -> None:
    """Drop estate planning table"""
    op.drop_index('ix_estate_planning_status')
    op.drop_index('ix_estate_planning_document_type')
    op.drop_index('ix_estate_planning_user_id')
    op.drop_table('user_estate_planning')