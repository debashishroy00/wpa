"""
Formula library for financial calculations
Provides basic formulas for financial planning calculations
"""

class FormulaLibrary:
    """Library of financial formulas and calculations"""
    
    def calculate_retirement_needs(self, annual_expenses: float, years_in_retirement: int = 30) -> float:
        """Calculate retirement needs using 4% rule"""
        return annual_expenses * 25
    
    def calculate_monthly_savings_needed(self, target_amount: float, years: int, rate: float = 0.07) -> float:
        """Calculate monthly savings needed to reach target"""
        if rate == 0:
            return target_amount / (years * 12)
        
        monthly_rate = rate / 12
        months = years * 12
        return target_amount * monthly_rate / ((1 + monthly_rate) ** months - 1)
    
    def calculate_compound_growth(self, principal: float, rate: float, years: int) -> float:
        """Calculate compound growth"""
        return principal * (1 + rate) ** years

# Global instance
formula_library = FormulaLibrary()