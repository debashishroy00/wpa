"""
Clean Architecture Data Contracts
Defines the essential data structures for WealthPath AI services
"""
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from datetime import datetime


# =============================================
# USER FINANCIAL DATA CONTRACT
# =============================================

@dataclass
class UserFinancialData:
    """Core financial data structure for a user"""
    user_id: str
    age: int
    monthly_income: float
    monthly_expenses: float
    monthly_debt_payments: float
    total_assets: float
    total_debts: float
    portfolio_value: float
    cash_reserves: float
    retirement_goal: float = 0.0
    retirement_age: int = 65
    
    def get_monthly_surplus(self) -> float:
        """Calculate monthly surplus (income - expenses)"""
        return self.monthly_income - self.monthly_expenses


# =============================================
# TOOLS OUTPUT CONTRACT
# =============================================

@dataclass
class ToolsOutput:
    """Output from financial calculation tools"""
    savings_rate: float           # 0-100 percentage
    liquidity_months: float       # months of expenses covered by cash
    years_to_retirement: float    # years until retirement age
    debt_to_income_ratio: float   # 0-100 percentage
    net_worth: float              # total assets minus debts
    portfolio_allocation: Dict[str, float] = None  # asset class percentages
    
    def __post_init__(self):
        """Initialize optional fields"""
        if self.portfolio_allocation is None:
            self.portfolio_allocation = {}


# =============================================
# VERIFICATION RESULT CONTRACT
# =============================================

@dataclass
class VerificationResult:
    """Result of response verification and grounding checks"""
    is_valid: bool
    grounded_claims: List[str]
    ungrounded_claims: List[str]
    confidence_score: float  # 0.0 to 1.0
    requires_regeneration: bool = False
    error_messages: List[str] = None
    
    def __post_init__(self):
        """Initialize optional fields"""
        if self.error_messages is None:
            self.error_messages = []