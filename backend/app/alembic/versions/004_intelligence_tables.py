"""Add intelligence analysis tables

Revision ID: 004_intelligence_tables
Revises: 003_audit_triggers
Create Date: 2024-12-14 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '004_intelligence_tables'
down_revision = '003_audit_triggers'  # Adjust based on your latest migration
branch_labels = None
depends_on = None

def upgrade():
    # Create intelligence_analyses table
    op.create_table('intelligence_analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('overall_score', sa.Integer(), nullable=True),
        sa.Column('success_probability', sa.Numeric(5, 4), nullable=True),
        sa.Column('gaps', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('conflicts', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('scenarios', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('recommendations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('selected_scenario_id', sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('idx_user_analyses', 'intelligence_analyses', ['user_id', 'created_at'])

    # Create monte_carlo_simulations table
    op.create_table('monte_carlo_simulations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('analysis_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('scenario_id', sa.String(50), nullable=True),
        sa.Column('iterations', sa.Integer(), nullable=True),
        sa.Column('success_rate', sa.Numeric(5, 4), nullable=True),
        sa.Column('p10_value', sa.Numeric(15, 2), nullable=True),
        sa.Column('p25_value', sa.Numeric(15, 2), nullable=True),
        sa.Column('p50_value', sa.Numeric(15, 2), nullable=True),
        sa.Column('p75_value', sa.Numeric(15, 2), nullable=True),
        sa.Column('p90_value', sa.Numeric(15, 2), nullable=True),
        sa.Column('parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['analysis_id'], ['intelligence_analyses.id'], ondelete='CASCADE')
    )

    # Create recommendation_actions table
    op.create_table('recommendation_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('analysis_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('recommendation_id', sa.String(100), nullable=True),
        sa.Column('action', sa.String(50), nullable=True),
        sa.Column('action_timestamp', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['analysis_id'], ['intelligence_analyses.id'], ondelete='CASCADE')
    )
    op.create_index('idx_user_recommendations', 'recommendation_actions', ['user_id', 'action_timestamp'])


def downgrade():
    op.drop_index('idx_user_recommendations', table_name='recommendation_actions')
    op.drop_table('recommendation_actions')
    op.drop_table('monte_carlo_simulations')
    op.drop_index('idx_user_analyses', table_name='intelligence_analyses')
    op.drop_table('intelligence_analyses')