"""
Unit tests for Step 4 Deterministic Plan Engine
Ensures calculations are consistent and accurate
"""
import pytest
from decimal import Decimal
from app.models.plan_engine import (
    PlanInput, CurrentState, Goals, Constraints,
    PlanOutput, GapAnalysis, TargetAllocation
)
from app.services.plan_engine import DeterministicPlanEngine


class TestPlanEngine:
    """Test suite for deterministic plan engine"""
    
    @pytest.fixture
    def sample_input(self):
        """Create sample input for testing"""
        return PlanInput(
            current_state=CurrentState(
                net_worth=Decimal('485750'),
                assets={
                    '401k': Decimal('185000'),
                    'brokerage': Decimal('125000'),
                    'savings': Decimal('45000'),
                    'real_estate': Decimal('450000')
                },
                liabilities={
                    'mortgage': Decimal('285000'),
                    'student_loans': Decimal('35000')
                },
                income={
                    'salary': Decimal('125000'),
                    'bonus': Decimal('15000')
                },
                expenses={
                    'monthly': Decimal('7200')
                },
                current_allocation={
                    'us_stocks': 0.40,
                    'intl_stocks': 0.20,
                    'bonds': 0.25,
                    'reits': 0.10,
                    'cash': 0.05
                }
            ),
            goals=Goals(
                target_net_worth=Decimal('2500000'),
                retirement_age=55,
                annual_spending=Decimal('100000'),
                risk_tolerance=7,
                current_age=38
            ),
            constraints=Constraints(
                min_emergency_fund=Decimal('30000'),
                max_single_asset_pct=0.10,
                tax_bracket=0.24,
                state_tax_rate=0.05
            )
        )
    
    def test_deterministic_output(self, sample_input):
        """Test that same input produces same output"""
        engine = DeterministicPlanEngine()
        
        output1 = engine.calculate_plan(sample_input)
        output2 = engine.calculate_plan(sample_input)
        
        # Key metrics should be identical
        assert output1.gap_analysis.gap == output2.gap_analysis.gap
        assert output1.target_allocation.us_stocks == output2.target_allocation.us_stocks
        assert output1.contribution_schedule.retirement_401k_percent == output2.contribution_schedule.retirement_401k_percent
        assert len(output1.debt_schedule) == len(output2.debt_schedule)
    
    def test_gap_analysis(self, sample_input):
        """Test gap analysis calculations"""
        engine = DeterministicPlanEngine()
        output = engine.calculate_plan(sample_input)
        
        gap = output.gap_analysis
        
        # Verify basic calculations
        assert gap.current_amount == sample_input.current_state.net_worth
        assert gap.target_amount == sample_input.goals.target_net_worth
        assert gap.gap == gap.target_amount - gap.current_amount
        assert gap.time_horizon_years == 17  # 55 - 38
        
        # Monte Carlo should produce reasonable results
        assert 0 <= gap.monte_carlo_success_rate <= 1
        assert gap.percentile_5_amount < gap.percentile_50_amount < gap.percentile_95_amount
    
    def test_target_allocation(self, sample_input):
        """Test allocation calculation"""
        engine = DeterministicPlanEngine()
        output = engine.calculate_plan(sample_input)
        
        allocation = output.target_allocation
        
        # Allocation should sum to 1.0
        total = (
            allocation.us_stocks + allocation.intl_stocks +
            allocation.bonds + allocation.reits + allocation.cash +
            allocation.commodities + allocation.crypto
        )
        assert abs(total - 1.0) < 0.01
        
        # Risk tolerance 7 should be moderately aggressive
        equity_pct = allocation.us_stocks + allocation.intl_stocks + allocation.reits
        assert 0.6 <= equity_pct <= 0.85
    
    def test_contribution_optimization(self, sample_input):
        """Test contribution schedule optimization"""
        engine = DeterministicPlanEngine()
        output = engine.calculate_plan(sample_input)
        
        contributions = output.contribution_schedule
        
        # 401k should be optimized but not exceed 50% of income
        assert 0 < contributions.retirement_401k_percent <= 0.5
        
        # Annual 401k shouldn't exceed IRS limit
        assert contributions.retirement_401k_annual <= Decimal('23000')
        
        # Roth IRA should be at limit
        assert contributions.roth_ira_annual == Decimal('7000')
        
        # Total monthly should be reasonable
        monthly_income = Decimal('140000') / 12
        monthly_expenses = Decimal('7200')
        available = monthly_income - monthly_expenses
        assert contributions.total_monthly <= available
    
    def test_debt_prioritization(self, sample_input):
        """Test debt schedule prioritization"""
        engine = DeterministicPlanEngine()
        output = engine.calculate_plan(sample_input)
        
        debt_schedule = output.debt_schedule
        
        # Should have entries for each liability
        assert len(debt_schedule) == len(sample_input.current_state.liabilities)
        
        # High-rate debt should be prioritized (avalanche method)
        if len(debt_schedule) > 1:
            for i in range(len(debt_schedule) - 1):
                assert debt_schedule[i].rate >= debt_schedule[i + 1].rate
    
    def test_stress_testing(self, sample_input):
        """Test stress test calculations"""
        engine = DeterministicPlanEngine()
        output = engine.calculate_plan(sample_input)
        
        metrics = output.plan_metrics
        
        # Stress tests should show impact
        assert 0 <= metrics.stress_test_30pct_drop <= 1
        assert metrics.stress_test_30pct_drop < 1.0  # Should show some impact
        
        if metrics.stress_test_50pct_drop is not None:
            assert metrics.stress_test_50pct_drop <= metrics.stress_test_30pct_drop
    
    def test_no_subjective_language(self, sample_input):
        """Ensure output contains no subjective language"""
        engine = DeterministicPlanEngine()
        output = engine.calculate_plan(sample_input)
        
        # Convert output to dict and check for subjective terms
        output_dict = output.dict()
        subjective_terms = [
            'recommend', 'should', 'consider', 'suggest',
            'advice', 'opinion', 'believe', 'think',
            'good', 'bad', 'better', 'worse'
        ]
        
        def check_dict_for_terms(d, terms):
            for key, value in d.items():
                if isinstance(value, str):
                    lower_value = value.lower()
                    for term in terms:
                        assert term not in lower_value, f"Found subjective term '{term}' in {key}: {value}"
                elif isinstance(value, dict):
                    check_dict_for_terms(value, terms)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            check_dict_for_terms(item, terms)
        
        check_dict_for_terms(output_dict, subjective_terms)
    
    def test_tax_optimization(self, sample_input):
        """Test tax strategy calculations"""
        engine = DeterministicPlanEngine()
        output = engine.calculate_plan(sample_input)
        
        if output.tax_strategy:
            tax = output.tax_strategy
            
            # Tax loss harvesting should be reasonable
            if tax.tax_loss_harvest_annual:
                taxable_assets = sum(
                    v for k, v in sample_input.current_state.assets.items()
                    if 'brokerage' in k.lower()
                )
                assert tax.tax_loss_harvest_annual <= taxable_assets * Decimal('0.01')
            
            # Roth conversion should consider tax bracket
            if tax.roth_conversion_annual and sample_input.constraints.tax_bracket >= 0.24:
                assert tax.roth_conversion_annual <= Decimal('50000')
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        engine = DeterministicPlanEngine()
        
        # Test with zero net worth
        zero_input = PlanInput(
            current_state=CurrentState(
                net_worth=Decimal('0'),
                assets={},
                liabilities={},
                income={'salary': Decimal('50000')},
                expenses={'monthly': Decimal('3000')}
            ),
            goals=Goals(
                target_net_worth=Decimal('1000000'),
                retirement_age=65,
                annual_spending=Decimal('40000'),
                risk_tolerance=5
            ),
            constraints=Constraints(
                min_emergency_fund=Decimal('10000'),
                max_single_asset_pct=0.25,
                tax_bracket=0.12
            )
        )
        
        output = engine.calculate_plan(zero_input)
        assert output.gap_analysis.gap == Decimal('1000000')
        
        # Test with already achieved goal
        achieved_input = PlanInput(
            current_state=CurrentState(
                net_worth=Decimal('3000000'),
                assets={'portfolio': Decimal('3000000')},
                liabilities={},
                income={'salary': Decimal('200000')},
                expenses={'monthly': Decimal('10000')}
            ),
            goals=Goals(
                target_net_worth=Decimal('2500000'),
                retirement_age=55,
                annual_spending=Decimal('100000'),
                risk_tolerance=5,
                current_age=50
            ),
            constraints=Constraints(
                min_emergency_fund=Decimal('50000'),
                max_single_asset_pct=0.20,
                tax_bracket=0.35
            )
        )
        
        output = engine.calculate_plan(achieved_input)
        assert output.gap_analysis.monte_carlo_success_rate > 0.9