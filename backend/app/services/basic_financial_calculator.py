"""
Basic Financial Calculator Service
Simple, pure math functions for core financial calculations
"""
from typing import Optional


class FinancialCalculator:
    """
    Simple financial calculator with pure mathematical functions.
    No side effects, same input always produces same output.
    """
    
    def calculate_savings_rate(self, monthly_income: float, monthly_expenses: float) -> float:
        """
        Calculate savings rate as a percentage.
        
        Args:
            monthly_income: Total monthly income
            monthly_expenses: Total monthly expenses
            
        Returns:
            Savings rate as percentage (0-100)
        """
        # Handle edge cases
        if monthly_income <= 0:
            return 0.0
        
        if monthly_expenses < 0:
            monthly_expenses = 0
        
        # Calculate savings amount
        savings = monthly_income - monthly_expenses
        
        # If expenses exceed income, savings rate is 0
        if savings < 0:
            return 0.0
        
        # Calculate percentage
        savings_rate = (savings / monthly_income) * 100
        
        # Cap at 100% (can't save more than you earn)
        return min(savings_rate, 100.0)
    
    def calculate_emergency_months(self, cash: float, monthly_expenses: float) -> float:
        """
        Calculate how many months of expenses the cash reserves can cover.
        
        Args:
            cash: Total cash reserves available
            monthly_expenses: Monthly expense amount
            
        Returns:
            Number of months expenses can be covered
        """
        # Handle edge cases
        if monthly_expenses <= 0:
            # If no expenses, infinite months (but return high number for practical purposes)
            return 999.0
        
        if cash < 0:
            cash = 0
        
        # Calculate months of coverage
        months = cash / monthly_expenses
        
        # Return with reasonable precision (2 decimal places)
        return round(months, 2)
        
    def calculate_emergency_months_with_outflows(self, cash: float, monthly_expenses: float, monthly_debt_payments: float) -> float:
        """
        Calculate emergency fund coverage using total monthly outflows (expenses + debt payments).
        Some financial models use total outflows instead of just expenses.
        
        Args:
            cash: Available cash reserves
            monthly_expenses: Monthly living expenses
            monthly_debt_payments: Monthly debt payments
            
        Returns:
            Number of months cash will last covering all outflows
        """
        # Handle edge cases
        if cash <= 0:
            return 0.0
            
        total_outflows = monthly_expenses + monthly_debt_payments
        if total_outflows <= 0:
            return float('inf')  # Infinite coverage if no outflows
        
        if cash < 0:
            cash = 0
        
        # Calculate months of coverage
        months = cash / total_outflows
        
        # Return with reasonable precision (2 decimal places)
        return round(months, 2)
    
    def calculate_debt_to_income(self, monthly_debt: float, monthly_income: float) -> float:
        """
        Calculate debt-to-income ratio as a percentage.
        
        Args:
            monthly_debt: Total monthly debt payments
            monthly_income: Total monthly income
            
        Returns:
            Debt-to-income ratio as percentage (0-100+)
        """
        # Handle edge cases
        if monthly_income <= 0:
            # No income means can't calculate meaningful ratio
            return 100.0 if monthly_debt > 0 else 0.0
        
        if monthly_debt < 0:
            monthly_debt = 0
        
        # Calculate debt-to-income percentage
        debt_ratio = (monthly_debt / monthly_income) * 100
        
        # Note: We don't cap this at 100 as debt payments can exceed income
        # But we'll ensure it's not negative
        return max(debt_ratio, 0.0)