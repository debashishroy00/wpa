"""add_projection_tables

Revision ID: 759dfa32e81b
Revises: af18b908f777
Create Date: 2025-08-10 18:22:36.708320

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '759dfa32e81b'
down_revision = 'af18b908f777'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create projection_assumptions table
    op.create_table(
        'projection_assumptions',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False, index=True),
        
        # Growth Rates
        sa.Column('salary_growth_rate', sa.Float, default=0.04, nullable=False),
        sa.Column('rental_income_growth', sa.Float, default=0.03, nullable=False),
        sa.Column('business_income_growth', sa.Float, default=0.06, nullable=False),
        
        # Asset Appreciation Rates
        sa.Column('real_estate_appreciation', sa.Float, default=0.04, nullable=False),
        sa.Column('stock_market_return', sa.Float, default=0.08, nullable=False),
        sa.Column('retirement_account_return', sa.Float, default=0.065, nullable=False),
        sa.Column('cash_equivalent_return', sa.Float, default=0.02, nullable=False),
        
        # Expense Growth Factors
        sa.Column('inflation_rate', sa.Float, default=0.025, nullable=False),
        sa.Column('lifestyle_inflation', sa.Float, default=0.01, nullable=False),
        sa.Column('healthcare_inflation', sa.Float, default=0.05, nullable=False),
        
        # Volatility Parameters
        sa.Column('stock_volatility', sa.Float, default=0.15, nullable=False),
        sa.Column('real_estate_volatility', sa.Float, default=0.02, nullable=False),
        sa.Column('income_volatility', sa.Float, default=0.05, nullable=False),
        
        # Tax Considerations
        sa.Column('effective_tax_rate', sa.Float, default=0.25, nullable=False),
        sa.Column('capital_gains_rate', sa.Float, default=0.15, nullable=False),
        
        # Advanced Parameters
        sa.Column('rebalancing_frequency', sa.Integer, default=12, nullable=False),
        sa.Column('sequence_risk_factor', sa.Float, default=0.02, nullable=False),
        
        # Metadata
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=True),
    )
    
    # Create projection_snapshots table
    op.create_table(
        'projection_snapshots',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False, index=True),
        
        # Projection Parameters
        sa.Column('projection_years', sa.Integer, nullable=False),
        sa.Column('scenario_type', sa.String(20), nullable=False),
        
        # Results (JSON)
        sa.Column('projected_values', sa.JSON, nullable=False),
        sa.Column('confidence_intervals', sa.JSON, nullable=False),
        sa.Column('growth_components', sa.JSON, nullable=False),
        sa.Column('key_milestones', sa.JSON, nullable=False),
        
        # Assumptions Snapshot
        sa.Column('assumptions_used', sa.JSON, nullable=False),
        
        # Performance Metrics
        sa.Column('monte_carlo_iterations', sa.Integer, default=1000, nullable=False),
        sa.Column('calculation_time_ms', sa.Integer, nullable=False),
        
        # Input Data Snapshot
        sa.Column('starting_financials', sa.JSON, nullable=False),
        
        # Metadata
        sa.Column('created_at', sa.DateTime, nullable=False),
    )
    
    # Create projection_sensitivity table
    op.create_table(
        'projection_sensitivity',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('snapshot_id', sa.Integer, sa.ForeignKey('projection_snapshots.id'), nullable=False),
        
        # Factor Analysis
        sa.Column('factor_name', sa.String(50), nullable=False),
        sa.Column('base_value', sa.Float, nullable=False),
        
        # Results
        sa.Column('sensitivity_results', sa.JSON, nullable=False),
        sa.Column('impact_ranking', sa.Integer, nullable=False),
        
        # Statistical Measures
        sa.Column('correlation_coefficient', sa.Float, nullable=False),
        sa.Column('elasticity', sa.Float, nullable=False),
        
        sa.Column('created_at', sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    op.drop_table('projection_sensitivity')
    op.drop_table('projection_snapshots')
    op.drop_table('projection_assumptions')