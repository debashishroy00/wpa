"""Restore financial snapshots table

Revision ID: e02b4086a0a3
Revises: 01c2eac84705
Create Date: 2025-09-17 01:51:04.740470

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'e02b4086a0a3'
down_revision = '01c2eac84705'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Recreate financial_snapshots table
    op.create_table('financial_snapshots',
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('financial_snapshots_id_seq'::regclass)"), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('snapshot_name', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.Column('snapshot_date', sa.DATE(), server_default=sa.text('CURRENT_DATE'), autoincrement=False, nullable=False),
    sa.Column('net_worth', sa.NUMERIC(precision=15, scale=2), autoincrement=False, nullable=True),
    sa.Column('total_assets', sa.NUMERIC(precision=15, scale=2), autoincrement=False, nullable=True),
    sa.Column('total_liabilities', sa.NUMERIC(precision=15, scale=2), autoincrement=False, nullable=True),
    sa.Column('monthly_income', sa.NUMERIC(precision=15, scale=2), autoincrement=False, nullable=True),
    sa.Column('monthly_expenses', sa.NUMERIC(precision=15, scale=2), autoincrement=False, nullable=True),
    sa.Column('savings_rate', sa.NUMERIC(precision=5, scale=2), autoincrement=False, nullable=True),
    sa.Column('age', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('employment_status', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=True),
    sa.Column('notes', sa.TEXT(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='financial_snapshots_user_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='financial_snapshots_pkey'),
    postgresql_ignore_search_path=False
    )
    op.create_index('ix_financial_snapshots_user_id', 'financial_snapshots', ['user_id'], unique=False)
    op.create_index('ix_financial_snapshots_snapshot_date', 'financial_snapshots', ['snapshot_date'], unique=False)

    # Recreate snapshot_entries table
    op.create_table('snapshot_entries',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('snapshot_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('category', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('subcategory', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
    sa.Column('name', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.Column('institution', sa.VARCHAR(length=200), autoincrement=False, nullable=True),
    sa.Column('account_type', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
    sa.Column('amount', sa.NUMERIC(precision=15, scale=2), autoincrement=False, nullable=False),
    sa.Column('interest_rate', sa.NUMERIC(precision=5, scale=2), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['snapshot_id'], ['financial_snapshots.id'], name='snapshot_entries_snapshot_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='snapshot_entries_pkey')
    )
    op.create_index('ix_snapshot_entries_snapshot_id', 'snapshot_entries', ['snapshot_id'], unique=False)

    # Recreate snapshot_goals table
    op.create_table('snapshot_goals',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('snapshot_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('goal_name', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.Column('target_amount', sa.NUMERIC(precision=15, scale=2), autoincrement=False, nullable=False),
    sa.Column('current_amount', sa.NUMERIC(precision=15, scale=2), server_default=sa.text('0'), autoincrement=False, nullable=True),
    sa.Column('target_date', sa.DATE(), autoincrement=False, nullable=True),
    sa.Column('completion_percentage', sa.NUMERIC(precision=5, scale=2), server_default=sa.text('0'), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['snapshot_id'], ['financial_snapshots.id'], name='snapshot_goals_snapshot_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='snapshot_goals_pkey')
    )
    op.create_index('ix_snapshot_goals_snapshot_id', 'snapshot_goals', ['snapshot_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('ix_snapshot_goals_snapshot_id', table_name='snapshot_goals')
    op.drop_table('snapshot_goals')
    op.drop_index('ix_snapshot_entries_snapshot_id', table_name='snapshot_entries')
    op.drop_table('snapshot_entries')
    op.drop_index('ix_financial_snapshots_snapshot_date', table_name='financial_snapshots')
    op.drop_index('ix_financial_snapshots_user_id', table_name='financial_snapshots')
    op.drop_table('financial_snapshots')