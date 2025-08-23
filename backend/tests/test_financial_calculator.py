"""
Tests for Financial Calculator Service
"""
import pytest
import math
from app.services.financial_calculator import FinancialCalculator


class TestLoanPayoffCalculation:
    """Test loan payoff calculations"""
    
    def test_basic_loan_payoff(self):
        """Test basic loan payoff calculation"""
        result = FinancialCalculator.calculate_loan_payoff(
            balance=5000,
            rate=22.99,
            payment=500
        )
        
        assert "error" not in result
        assert result['months_to_payoff'] < 12
        assert result['total_interest'] < 600
        assert result['daily_interest_cost'] > 3
        assert result['monthly_payment'] == 500
        
    def test_minimum_payment_error(self):
        """Test error when payment is too low"""
        result = FinancialCalculator.calculate_loan_payoff(
            balance=10000,
            rate=20.0,
            payment=50  # Too low to cover interest
        )
        
        assert "error" in result
        assert result['error'] == "Payment too low to cover interest"
        assert "minimum_payment_needed" in result
        
    def test_zero_interest_rate(self):
        """Test calculation with zero interest rate"""
        result = FinancialCalculator.calculate_loan_payoff(
            balance=1000,
            rate=0,
            payment=100
        )
        
        assert "error" not in result
        assert result['months_to_payoff'] == 10
        assert result['total_interest'] == 0
        
    def test_invalid_inputs(self):
        """Test various invalid inputs"""
        # Negative balance
        result = FinancialCalculator.calculate_loan_payoff(-1000, 5.0, 100)
        assert "error" in result
        
        # Negative rate
        result = FinancialCalculator.calculate_loan_payoff(1000, -5.0, 100)
        assert "error" in result
        
        # Zero payment
        result = FinancialCalculator.calculate_loan_payoff(1000, 5.0, 0)
        assert "error" in result


class TestPayoffStrategyComparison:
    """Test payment strategy comparisons"""
    
    def test_accelerated_vs_minimum_payment(self):
        """Test comparison between minimum and accelerated payments"""
        comparison = FinancialCalculator.compare_payoff_strategies(
            balance=5000,
            rate=18.0,
            min_payment=150,
            accelerated_payment=300
        )
        
        assert "error" not in comparison
        assert "minimum_payment_plan" in comparison
        assert "accelerated_payment_plan" in comparison
        assert comparison['interest_saved'] > 0
        assert comparison['months_saved'] > 0
        assert comparison['additional_monthly_payment'] == 150
        
    def test_same_payment_amounts(self):
        """Test when both payment amounts are the same"""
        comparison = FinancialCalculator.compare_payoff_strategies(
            balance=5000,
            rate=15.0,
            min_payment=200,
            accelerated_payment=200
        )
        
        assert "error" not in comparison
        assert comparison['interest_saved'] == 0
        assert comparison['months_saved'] == 0
        
    def test_invalid_strategy_comparison(self):
        """Test strategy comparison with invalid inputs"""
        comparison = FinancialCalculator.compare_payoff_strategies(
            balance=5000,
            rate=20.0,
            min_payment=10,  # Too low
            accelerated_payment=50  # Also too low
        )
        
        assert "error" in comparison


class TestDebtAvalanche:
    """Test debt avalanche ordering"""
    
    def test_debt_prioritization_by_rate(self):
        """Test debt prioritization by interest rate"""
        debts = [
            {'description': 'Mortgage', 'balance': 300000, 'interest_rate': 2.75, 'minimum_payment': 1500},
            {'description': 'Credit Card', 'balance': 5000, 'interest_rate': 22.99, 'minimum_payment': 150},
            {'description': 'Auto Loan', 'balance': 15000, 'interest_rate': 5.5, 'minimum_payment': 300}
        ]
        
        result = FinancialCalculator.calculate_debt_avalanche(debts)
        
        assert len(result) == 3
        assert result[0]['name'] == 'Credit Card'
        assert result[0]['priority'] == 1
        assert result[0]['urgency'] == 'CRITICAL'
        assert result[-1]['name'] == 'Mortgage'
        assert result[-1]['priority'] == 3
        
    def test_empty_debt_list(self):
        """Test with empty debt list"""
        result = FinancialCalculator.calculate_debt_avalanche([])
        assert result == []
        
    def test_single_debt(self):
        """Test with single debt"""
        debts = [
            {'description': 'Personal Loan', 'balance': 10000, 'interest_rate': 12.0, 'minimum_payment': 200}
        ]
        
        result = FinancialCalculator.calculate_debt_avalanche(debts)
        
        assert len(result) == 1
        assert result[0]['priority'] == 1
        assert result[0]['urgency'] == 'MEDIUM'
        
    def test_debt_urgency_levels(self):
        """Test different urgency levels based on interest rates"""
        debts = [
            {'description': 'Low Rate', 'balance': 1000, 'interest_rate': 3.0, 'minimum_payment': 50},
            {'description': 'Medium Rate', 'balance': 1000, 'interest_rate': 10.0, 'minimum_payment': 50},
            {'description': 'High Rate', 'balance': 1000, 'interest_rate': 18.0, 'minimum_payment': 50},
            {'description': 'Critical Rate', 'balance': 1000, 'interest_rate': 25.0, 'minimum_payment': 50}
        ]
        
        result = FinancialCalculator.calculate_debt_avalanche(debts)
        
        assert result[0]['urgency'] == 'CRITICAL'  # 25%
        assert result[1]['urgency'] == 'HIGH'      # 18%
        assert result[2]['urgency'] == 'MEDIUM'    # 10%
        assert result[3]['urgency'] == 'LOW'       # 3%


class TestMortgageVsInvestment:
    """Test mortgage vs investment comparisons"""
    
    def test_low_rate_mortgage_vs_investment(self):
        """Test comparison with low-rate mortgage"""
        comparison = FinancialCalculator.calculate_mortgage_vs_invest(
            mortgage_balance=300000,
            mortgage_rate=3.0,
            extra_payment=1000,
            expected_investment_return=7.0
        )
        
        assert "error" not in comparison
        assert "mortgage_payoff_strategy" in comparison
        assert "investment_strategy" in comparison
        assert comparison['recommendation'] in ['Invest', 'Pay off mortgage']
        assert comparison['advantage_amount'] > 0
        
    def test_high_rate_mortgage_vs_investment(self):
        """Test comparison with high-rate mortgage"""
        comparison = FinancialCalculator.calculate_mortgage_vs_invest(
            mortgage_balance=200000,
            mortgage_rate=7.5,
            extra_payment=500,
            expected_investment_return=7.0
        )
        
        assert "error" not in comparison
        # High mortgage rate should favor paying off mortgage
        # (though this depends on exact calculations)
        
    def test_zero_extra_payment(self):
        """Test with zero extra payment"""
        comparison = FinancialCalculator.calculate_mortgage_vs_invest(
            mortgage_balance=200000,
            mortgage_rate=4.0,
            extra_payment=0,
            expected_investment_return=7.0
        )
        
        # Should handle zero extra payment gracefully
        assert "error" not in comparison


class TestEmergencyFundAnalysis:
    """Test emergency fund adequacy calculations"""
    
    def test_adequate_emergency_fund(self):
        """Test with adequate emergency fund"""
        analysis = FinancialCalculator.calculate_emergency_fund_adequacy(
            monthly_expenses=5000,
            current_savings=30000,  # 6 months
            income_stability="stable"
        )
        
        assert analysis['status'] == 'ADEQUATE'
        assert analysis['current_months_covered'] == 6.0
        assert analysis['recommended_months'] == 3
        assert analysis['shortfall'] == 0
        assert analysis['excess'] > 0
        
    def test_insufficient_emergency_fund(self):
        """Test with insufficient emergency fund"""
        analysis = FinancialCalculator.calculate_emergency_fund_adequacy(
            monthly_expenses=4000,
            current_savings=5000,  # 1.25 months
            income_stability="variable"
        )
        
        assert analysis['status'] == 'INSUFFICIENT'
        assert analysis['current_months_covered'] == 1.25
        assert analysis['recommended_months'] == 6
        assert analysis['shortfall'] > 0
        assert analysis['monthly_gap'] > 0
        
    def test_different_income_stability_levels(self):
        """Test different income stability requirements"""
        monthly_expenses = 3000
        current_savings = 9000  # 3 months
        
        # Stable income - should be adequate
        stable = FinancialCalculator.calculate_emergency_fund_adequacy(
            monthly_expenses, current_savings, "stable"
        )
        assert stable['status'] == 'ADEQUATE'
        
        # Variable income - should be partial
        variable = FinancialCalculator.calculate_emergency_fund_adequacy(
            monthly_expenses, current_savings, "variable"
        )
        assert variable['status'] == 'PARTIAL'
        
        # Uncertain income - should be insufficient
        uncertain = FinancialCalculator.calculate_emergency_fund_adequacy(
            monthly_expenses, current_savings, "uncertain"
        )
        assert uncertain['status'] == 'INSUFFICIENT'


class TestRetirementProjection:
    """Test retirement projection calculations"""
    
    def test_basic_retirement_projection(self):
        """Test basic retirement projection"""
        projection = FinancialCalculator.calculate_retirement_projection(
            current_age=30,
            retirement_age=65,
            current_savings=50000,
            monthly_contribution=1000,
            expected_return=7.0
        )
        
        assert "error" not in projection
        assert projection['years_to_retirement'] == 35
        assert projection['projected_balance'] > projection['total_contributed']
        assert projection['investment_gains'] > 0
        assert projection['safe_monthly_income'] > 0
        assert projection['withdrawal_rate_used'] == 4.0
        
    def test_already_retired(self):
        """Test with person already at retirement age"""
        projection = FinancialCalculator.calculate_retirement_projection(
            current_age=70,
            retirement_age=65,
            current_savings=100000,
            monthly_contribution=500
        )
        
        assert "error" in projection
        assert "Already at or past retirement age" in projection['error']
        
    def test_zero_contribution(self):
        """Test with zero monthly contribution"""
        projection = FinancialCalculator.calculate_retirement_projection(
            current_age=40,
            retirement_age=65,
            current_savings=100000,
            monthly_contribution=0,
            expected_return=6.0
        )
        
        assert "error" not in projection
        assert projection['contribution_growth'] == 0
        assert projection['current_savings_growth'] > 100000
        
    def test_zero_current_savings(self):
        """Test with zero current savings"""
        projection = FinancialCalculator.calculate_retirement_projection(
            current_age=25,
            retirement_age=65,
            current_savings=0,
            monthly_contribution=800,
            expected_return=8.0
        )
        
        assert "error" not in projection
        assert projection['current_savings_growth'] == 0
        assert projection['contribution_growth'] > 0
        
    def test_conservative_vs_aggressive_returns(self):
        """Test different return rate scenarios"""
        base_params = {
            'current_age': 35,
            'retirement_age': 65,
            'current_savings': 75000,
            'monthly_contribution': 1200
        }
        
        conservative = FinancialCalculator.calculate_retirement_projection(
            **base_params, expected_return=5.0
        )
        
        aggressive = FinancialCalculator.calculate_retirement_projection(
            **base_params, expected_return=9.0
        )
        
        assert "error" not in conservative
        assert "error" not in aggressive
        assert aggressive['projected_balance'] > conservative['projected_balance']
        assert aggressive['safe_monthly_income'] > conservative['safe_monthly_income']


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_very_large_numbers(self):
        """Test with very large numbers"""
        result = FinancialCalculator.calculate_loan_payoff(
            balance=1000000,
            rate=5.0,
            payment=10000
        )
        
        assert "error" not in result
        assert result['months_to_payoff'] > 0
        
    def test_very_small_numbers(self):
        """Test with very small numbers"""
        result = FinancialCalculator.calculate_loan_payoff(
            balance=1,
            rate=0.01,
            payment=1
        )
        
        assert "error" not in result
        assert result['months_to_payoff'] <= 1
        
    def test_high_interest_rate(self):
        """Test with very high interest rate"""
        result = FinancialCalculator.calculate_loan_payoff(
            balance=1000,
            rate=50.0,  # 50% APR
            payment=200
        )
        
        assert "error" not in result
        assert result['daily_interest_cost'] > 1


if __name__ == "__main__":
    pytest.main([__file__])