"""
WealthPath AI - Financial Calculator Engine
Provides deterministic financial calculations for precise advisory responses
"""
from typing import Dict, List, Optional
import math
from decimal import Decimal, ROUND_HALF_UP


class AdvancedFinancialCalculator:
    """Advanced financial calculations for complex scenarios and health scoring"""
    
    @staticmethod
    def calculate_financial_health_score(context: Dict) -> Dict:
        """
        Calculate a 0-100 financial health score based on key metrics
        
        Args:
            context: Smart context dictionary with financial data
            
        Returns:
            Dict with total score, component breakdown, and grade
        """
        components = {}
        
        # 1. Emergency Fund (20 points)
        emergency_analysis = context.get('emergency_analysis', {})
        emergency_months = emergency_analysis.get('current_months_covered', 0)
        
        if emergency_months >= 6:
            components['emergency_fund'] = {'score': 20, 'status': 'Excellent'}
        elif emergency_months >= 3:
            components['emergency_fund'] = {'score': 15, 'status': 'Good'}
        elif emergency_months >= 1:
            components['emergency_fund'] = {'score': int(emergency_months * 5), 'status': 'Fair'}
        else:
            components['emergency_fund'] = {'score': 0, 'status': 'Poor'}
        
        # 2. Debt Management (25 points)
        debt_strategy = context.get('debt_strategy', [])
        high_interest_debts = [d for d in debt_strategy if d.get('rate', 0) > 15]
        total_debt = sum(d.get('balance', 0) for d in debt_strategy)
        monthly_income = context.get('monthly_income', 1)
        
        if not high_interest_debts:
            components['debt_management'] = {'score': 25, 'status': 'Excellent'}
        elif total_debt / monthly_income <= 2:  # Less than 2 months income in debt
            components['debt_management'] = {'score': 15, 'status': 'Good'}  
        elif total_debt / monthly_income <= 6:  # Less than 6 months income
            components['debt_management'] = {'score': 10, 'status': 'Fair'}
        else:
            components['debt_management'] = {'score': 5, 'status': 'Poor'}
        
        # 3. Cash Flow & Savings Rate (25 points)
        monthly_surplus = context.get('monthly_surplus', 0)
        surplus_rate = (monthly_surplus / monthly_income * 100) if monthly_income > 0 else 0
        
        if surplus_rate >= 20:
            components['cash_flow'] = {'score': 25, 'status': 'Excellent'}
        elif surplus_rate >= 15:
            components['cash_flow'] = {'score': 20, 'status': 'Very Good'}
        elif surplus_rate >= 10:
            components['cash_flow'] = {'score': 15, 'status': 'Good'}
        elif surplus_rate >= 5:
            components['cash_flow'] = {'score': 10, 'status': 'Fair'}
        else:
            components['cash_flow'] = {'score': 0, 'status': 'Poor'}
        
        # 4. Portfolio Diversification (15 points)
        portfolio = context.get('portfolio_breakdown', {})
        stocks_pct = portfolio.get('stocks_percentage', 0)
        bonds_pct = portfolio.get('bonds_percentage', 0)
        real_estate_pct = portfolio.get('real_estate_percentage', 0)
        
        # Check for reasonable diversification
        if 40 <= stocks_pct <= 80 and bonds_pct >= 10 and real_estate_pct <= 40:
            components['diversification'] = {'score': 15, 'status': 'Well Diversified'}
        elif stocks_pct >= 20 and (bonds_pct >= 5 or real_estate_pct <= 60):
            components['diversification'] = {'score': 10, 'status': 'Adequately Diversified'}
        else:
            components['diversification'] = {'score': 5, 'status': 'Needs Improvement'}
        
        # 5. Financial Stability (15 points)
        net_worth = context.get('net_worth', 0)
        total_assets = context.get('total_assets', 1)
        debt_to_asset_ratio = (total_debt / total_assets) if total_assets > 0 else 1
        
        if debt_to_asset_ratio <= 0.20 and net_worth > 0:
            components['stability'] = {'score': 15, 'status': 'Very Stable'}
        elif debt_to_asset_ratio <= 0.40 and net_worth > 0:
            components['stability'] = {'score': 12, 'status': 'Stable'}
        elif net_worth > 0:
            components['stability'] = {'score': 8, 'status': 'Moderately Stable'}
        else:
            components['stability'] = {'score': 0, 'status': 'Unstable'}
        
        # Calculate total score
        total_score = sum(comp['score'] for comp in components.values())
        
        # Determine grade
        if total_score >= 90:
            grade = 'A'
            rating = 'Excellent'
        elif total_score >= 80:
            grade = 'B'
            rating = 'Good'
        elif total_score >= 70:
            grade = 'C'
            rating = 'Fair'
        elif total_score >= 60:
            grade = 'D'
            rating = 'Below Average'
        else:
            grade = 'F'
            rating = 'Poor'
        
        return {
            'total_score': round(total_score),
            'grade': grade,
            'rating': rating,
            'components': components,
            'recommendations': FinancialCalculator._get_health_score_recommendations(components, context)
        }
    
    @staticmethod
    def _get_health_score_recommendations(components: Dict, context: Dict) -> List[str]:
        """Generate specific recommendations based on component scores"""
        recommendations = []
        
        # Emergency fund recommendations
        if components['emergency_fund']['score'] < 15:
            emergency_gap = context.get('emergency_analysis', {}).get('shortfall', 0)
            if emergency_gap > 0:
                recommendations.append(f"Build emergency fund by ${emergency_gap:,.0f}")
        
        # Debt recommendations  
        if components['debt_management']['score'] < 20:
            high_interest_debts = [d for d in context.get('debt_strategy', []) if d.get('rate', 0) > 15]
            if high_interest_debts:
                top_debt = high_interest_debts[0]
                recommendations.append(f"Pay off {top_debt['name']} (${top_debt['balance']:,.0f} @ {top_debt['rate']}%)")
        
        # Cash flow recommendations
        if components['cash_flow']['score'] < 15:
            recommendations.append("Increase monthly savings rate to 15%+ of income")
        
        # Diversification recommendations
        if components['diversification']['score'] < 12:
            portfolio = context.get('portfolio_breakdown', {})
            if portfolio.get('stocks_percentage', 0) < 30:
                recommendations.append("Consider increasing stock allocation for growth")
            elif portfolio.get('real_estate_percentage', 0) > 50:
                recommendations.append("Consider reducing real estate concentration")
        
        return recommendations[:3]  # Top 3 recommendations
    
    @staticmethod
    def calculate_loan_payoff(balance: float, rate: float, payment: float) -> Dict:
        """
        Calculate exact payoff timeline and interest paid
        
        Args:
            balance: Current loan balance
            rate: Annual interest rate (e.g., 22.99 for 22.99%)
            payment: Monthly payment amount
            
        Returns:
            Dict with months_to_payoff, total_interest, total_paid
        """
        if balance <= 0:
            return {"error": "Balance must be positive"}
        
        if rate < 0:
            return {"error": "Interest rate cannot be negative"}
            
        if payment <= 0:
            return {"error": "Payment must be positive"}
            
        monthly_rate = rate / 100 / 12
        
        if payment <= balance * monthly_rate:
            return {
                "error": "Payment too low to cover interest",
                "minimum_payment_needed": round(balance * monthly_rate + 1, 2)
            }
        
        # Calculate months to payoff using amortization formula
        try:
            if monthly_rate == 0:
                # Zero interest rate - simple division
                months = balance / payment
            else:
                months = -math.log(1 - (balance * monthly_rate) / payment) / math.log(1 + monthly_rate)
        except (ValueError, ZeroDivisionError):
            return {"error": "Invalid calculation parameters"}
            
        total_paid = payment * months
        total_interest = total_paid - balance
        
        return {
            "months_to_payoff": round(months, 1),
            "years_to_payoff": round(months / 12, 1),
            "total_interest": round(total_interest, 2),
            "total_paid": round(total_paid, 2),
            "monthly_payment": payment,
            "daily_interest_cost": round((balance * rate / 100) / 365, 2),
            "monthly_interest_cost": round(balance * monthly_rate, 2)
        }
    
    @staticmethod
    def compare_payoff_strategies(balance: float, rate: float, 
                                 min_payment: float, accelerated_payment: float) -> Dict:
        """Compare minimum vs accelerated payment strategies"""
        min_scenario = FinancialCalculator.calculate_loan_payoff(balance, rate, min_payment)
        fast_scenario = FinancialCalculator.calculate_loan_payoff(balance, rate, accelerated_payment)
        
        if "error" in min_scenario or "error" in fast_scenario:
            return {
                "error": "Unable to calculate comparison",
                "min_scenario_error": min_scenario.get("error"),
                "fast_scenario_error": fast_scenario.get("error")
            }
        
        return {
            "minimum_payment_plan": min_scenario,
            "accelerated_payment_plan": fast_scenario,
            "interest_saved": round(min_scenario["total_interest"] - fast_scenario["total_interest"], 2),
            "months_saved": round(min_scenario["months_to_payoff"] - fast_scenario["months_to_payoff"], 1),
            "years_saved": round((min_scenario["months_to_payoff"] - fast_scenario["months_to_payoff"]) / 12, 1),
            "additional_monthly_payment": accelerated_payment - min_payment,
            "return_on_extra_payment": round(
                (min_scenario["total_interest"] - fast_scenario["total_interest"]) / 
                ((accelerated_payment - min_payment) * fast_scenario["months_to_payoff"]) * 100, 2
            ) if fast_scenario["months_to_payoff"] > 0 and (accelerated_payment - min_payment) > 0 else 0
        }
    
    @staticmethod
    def calculate_debt_avalanche(debts: List[Dict]) -> List[Dict]:
        """
        Order debts by interest rate (highest first) for optimal payoff
        
        Args:
            debts: List of debt dictionaries with balance, rate, min_payment
            
        Returns:
            Ordered list with payoff priority and savings calculations
        """
        if not debts:
            return []
            
        # Filter out debts without valid data
        valid_debts = []
        for debt in debts:
            if (debt.get('balance', 0) > 0 and 
                debt.get('interest_rate', 0) > 0 and 
                debt.get('description')):
                valid_debts.append(debt)
        
        if not valid_debts:
            return []
        
        # Sort by interest rate descending (avalanche method)
        sorted_debts = sorted(valid_debts, key=lambda x: x.get('interest_rate', 0), reverse=True)
        
        payoff_order = []
        
        for i, debt in enumerate(sorted_debts):
            balance = debt.get('balance', 0)
            rate = debt.get('interest_rate', 0)
            monthly_interest = (balance * rate / 100) / 12
            
            # Determine urgency level
            if rate >= 20:
                urgency = "CRITICAL"
                reason = f"Extremely high rate at {rate}% - costs ${monthly_interest * 12:,.0f}/year"
            elif rate >= 15:
                urgency = "HIGH"
                reason = f"High rate at {rate}% - costs ${monthly_interest * 12:,.0f}/year"
            elif rate >= 8:
                urgency = "MEDIUM"
                reason = f"Above-average rate at {rate}%"
            else:
                urgency = "LOW"
                reason = f"Low rate at {rate}% - consider other priorities"
            
            payoff_order.append({
                "priority": i + 1,
                "name": debt['description'],
                "balance": balance,
                "rate": rate,
                "urgency": urgency,
                "monthly_interest_cost": round(monthly_interest, 2),
                "annual_interest_cost": round(monthly_interest * 12, 2),
                "daily_interest_cost": round(monthly_interest / 30, 2),
                "reason": reason,
                "minimum_payment": debt.get('minimum_payment', 0),
                "loan_term_months": debt.get('loan_term_months'),
                "recommended_action": "Pay extra on this debt" if i == 0 else f"Pay minimum only (#{i+1} priority)"
            })
        
        return payoff_order
    
    @staticmethod
    def calculate_mortgage_vs_invest(mortgage_balance: float, mortgage_rate: float,
                                   extra_payment: float, expected_investment_return: float = 7.0) -> Dict:
        """
        Compare paying extra on mortgage vs investing the money
        
        Args:
            mortgage_balance: Current mortgage balance
            mortgage_rate: Mortgage interest rate
            extra_payment: Extra amount available monthly
            expected_investment_return: Expected annual investment return (default 7%)
            
        Returns:
            Comparison of both strategies over time
        """
        # Estimate a reasonable mortgage payment (assuming 30-year mortgage)
        monthly_rate = mortgage_rate / 100 / 12
        if monthly_rate > 0:
            # Standard mortgage payment formula for 30 years
            n_payments = 360  # 30 years * 12 months
            current_payment = mortgage_balance * (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)
        else:
            # Zero interest case - just principal over 30 years
            current_payment = mortgage_balance / 360
        
        # Make sure payment is reasonable (at least covers interest + some principal)
        min_payment_needed = mortgage_balance * monthly_rate + 50  # Interest + $50 principal
        current_payment = max(current_payment, min_payment_needed)
        
        mortgage_result = FinancialCalculator.calculate_loan_payoff(
            mortgage_balance, mortgage_rate, current_payment + extra_payment
        )
        
        if "error" in mortgage_result:
            return {"error": f"Invalid mortgage calculation: {mortgage_result.get('error', 'Unknown error')}"}
        
        # Calculate investment growth
        months = mortgage_result["months_to_payoff"]
        monthly_investment_return = expected_investment_return / 100 / 12
        
        # Future value of monthly investments
        if monthly_investment_return > 0:
            investment_value = extra_payment * (
                ((1 + monthly_investment_return) ** months - 1) / monthly_investment_return
            )
        else:
            investment_value = extra_payment * months
        
        # Interest saved by paying off mortgage early
        standard_mortgage = FinancialCalculator.calculate_loan_payoff(
            mortgage_balance, mortgage_rate, current_payment
        )
        
        if "error" in standard_mortgage:
            return {"error": f"Invalid standard mortgage calculation: {standard_mortgage.get('error', 'Unknown error')}"}
            
        interest_saved = standard_mortgage["total_interest"] - mortgage_result["total_interest"]
        
        return {
            "mortgage_payoff_strategy": {
                "months_to_payoff": mortgage_result["months_to_payoff"],
                "interest_saved": round(interest_saved, 2),
                "guaranteed_return_rate": mortgage_rate,
                "net_benefit": round(interest_saved, 2)
            },
            "investment_strategy": {
                "projected_value": round(investment_value, 2),
                "total_invested": round(extra_payment * months, 2),
                "projected_gains": round(investment_value - (extra_payment * months), 2),
                "assumed_return_rate": expected_investment_return,
                "net_benefit": round(investment_value - (extra_payment * months), 2)
            },
            "recommendation": "Invest" if investment_value - (extra_payment * months) > interest_saved else "Pay off mortgage",
            "advantage_amount": round(abs((investment_value - (extra_payment * months)) - interest_saved), 2),
            "risk_consideration": "Investment returns are not guaranteed, mortgage payoff provides certain savings"
        }
    
    @staticmethod
    def calculate_emergency_fund_adequacy(monthly_expenses: float, current_savings: float,
                                        income_stability: str = "stable") -> Dict:
        """
        Calculate emergency fund adequacy and recommendations
        
        Args:
            monthly_expenses: Monthly living expenses
            current_savings: Current emergency fund amount
            income_stability: "stable", "variable", or "uncertain"
            
        Returns:
            Emergency fund analysis and recommendations
        """
        # Recommended months based on income stability
        recommended_months = {
            "stable": 3,
            "variable": 6,
            "uncertain": 12
        }.get(income_stability, 6)
        
        recommended_amount = monthly_expenses * recommended_months
        current_months = current_savings / monthly_expenses if monthly_expenses > 0 else 0
        
        if current_savings >= recommended_amount:
            status = "ADEQUATE"
            action = "Emergency fund is sufficient"
        elif current_savings >= monthly_expenses * 3:
            status = "PARTIAL"
            action = f"Add ${recommended_amount - current_savings:,.0f} to reach {recommended_months} months"
        else:
            status = "INSUFFICIENT"
            action = f"PRIORITY: Build emergency fund to ${recommended_amount:,.0f}"
        
        return {
            "current_months_covered": round(current_months, 1),
            "recommended_months": recommended_months,
            "current_amount": current_savings,
            "recommended_amount": recommended_amount,
            "shortfall": max(0, recommended_amount - current_savings),
            "excess": max(0, current_savings - recommended_amount),
            "status": status,
            "action_needed": action,
            "monthly_gap": round((recommended_amount - current_savings) / 12, 2) if current_savings < recommended_amount else 0
        }
    
    @staticmethod
    def calculate_retirement_projection(current_age: int, retirement_age: int,
                                      current_savings: float, monthly_contribution: float,
                                      expected_return: float = 7.0) -> Dict:
        """
        Project retirement savings growth
        
        Args:
            current_age: Current age
            retirement_age: Target retirement age
            current_savings: Current retirement account balance
            monthly_contribution: Monthly retirement contributions
            expected_return: Expected annual return percentage
            
        Returns:
            Retirement projection analysis
        """
        years_to_retirement = retirement_age - current_age
        months_to_retirement = years_to_retirement * 12
        
        if years_to_retirement <= 0:
            return {"error": "Already at or past retirement age"}
        
        monthly_return = expected_return / 100 / 12
        
        # Future value of current savings
        future_value_current = current_savings * ((1 + monthly_return) ** months_to_retirement)
        
        # Future value of monthly contributions
        if monthly_return > 0:
            future_value_contributions = monthly_contribution * (
                ((1 + monthly_return) ** months_to_retirement - 1) / monthly_return
            )
        else:
            future_value_contributions = monthly_contribution * months_to_retirement
        
        total_projected = future_value_current + future_value_contributions
        total_contributed = current_savings + (monthly_contribution * months_to_retirement)
        
        # Calculate safe withdrawal amount (4% rule)
        safe_annual_withdrawal = total_projected * 0.04
        safe_monthly_income = safe_annual_withdrawal / 12
        
        return {
            "years_to_retirement": years_to_retirement,
            "projected_balance": round(total_projected, 2),
            "total_contributed": round(total_contributed, 2),
            "investment_gains": round(total_projected - total_contributed, 2),
            "safe_annual_withdrawal": round(safe_annual_withdrawal, 2),
            "safe_monthly_income": round(safe_monthly_income, 2),
            "current_savings_growth": round(future_value_current, 2),
            "contribution_growth": round(future_value_contributions, 2),
            "monthly_contribution": monthly_contribution,
            "assumed_return": expected_return,
            "withdrawal_rate_used": 4.0
        }