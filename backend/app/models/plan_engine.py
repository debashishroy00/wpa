"""
Step 4: Deterministic Plan Engine Models
Pure calculation models with no subjective language
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator
from decimal import Decimal


class CurrentState(BaseModel):
    """Current financial state input"""
    net_worth: Decimal
    assets: Dict[str, Decimal]
    liabilities: Dict[str, Decimal]
    income: Dict[str, Decimal]
    expenses: Dict[str, Decimal]
    current_allocation: Dict[str, float] = Field(
        default_factory=dict,
        description="Current portfolio allocation percentages"
    )
    
    @validator('current_allocation')
    def validate_allocation(cls, v):
        if v and abs(sum(v.values()) - 1.0) > 0.01:
            raise ValueError("Allocation percentages must sum to 1.0")
        return v


class Goals(BaseModel):
    """Financial goals and targets"""
    target_net_worth: Decimal
    retirement_age: int
    annual_spending: Decimal
    risk_tolerance: int = Field(ge=1, le=10)
    current_age: Optional[int] = None


class Constraints(BaseModel):
    """Planning constraints and limits"""
    min_emergency_fund: Decimal
    max_single_asset_pct: float = Field(le=1.0)
    tax_bracket: float = Field(le=1.0)
    state_tax_rate: Optional[float] = Field(default=0.0, le=1.0)
    max_debt_to_income: Optional[float] = Field(default=0.36)


class PlanInput(BaseModel):
    """Complete input for plan engine"""
    current_state: CurrentState
    goals: Goals
    constraints: Constraints


class GapAnalysis(BaseModel):
    """Gap between current and target state"""
    target_amount: Decimal
    current_amount: Decimal
    gap: Decimal
    time_horizon_years: int
    monte_carlo_success_rate: float = Field(ge=0, le=1)
    percentile_95_amount: Optional[Decimal] = None
    percentile_50_amount: Optional[Decimal] = None
    percentile_5_amount: Optional[Decimal] = None


class TargetAllocation(BaseModel):
    """Target portfolio allocation"""
    us_stocks: float = Field(ge=0, le=1)
    intl_stocks: float = Field(ge=0, le=1)
    bonds: float = Field(ge=0, le=1)
    reits: float = Field(ge=0, le=1)
    cash: float = Field(ge=0, le=1)
    commodities: float = Field(default=0, ge=0, le=1)
    crypto: float = Field(default=0, ge=0, le=1)
    
    @validator('crypto')
    def validate_total(cls, v, values):
        total = sum([
            values.get('us_stocks', 0),
            values.get('intl_stocks', 0),
            values.get('bonds', 0),
            values.get('reits', 0),
            values.get('cash', 0),
            values.get('commodities', 0),
            v
        ])
        if abs(total - 1.0) > 0.01:
            raise ValueError("Allocation must sum to 1.0")
        return v


class RebalancingTrade(BaseModel):
    """Single rebalancing trade"""
    action: str = Field(pattern="^(buy|sell)$")
    symbol: str
    amount: Decimal
    account: Optional[str] = None
    tax_impact: Optional[Decimal] = None


class ContributionSchedule(BaseModel):
    """Savings and contribution plan"""
    retirement_401k_percent: float
    retirement_401k_annual: Decimal
    roth_ira_annual: Decimal
    hsa_annual: Optional[Decimal] = Field(default=Decimal(0))
    taxable_monthly: Decimal
    total_monthly: Decimal
    employer_match_annual: Optional[Decimal] = None
    tax_savings_annual: Optional[Decimal] = None


class DebtAction(BaseModel):
    """Debt management action"""
    debt: str
    balance: Decimal
    rate: float
    action: str
    monthly_payment: Optional[Decimal] = None
    payoff_months: Optional[int] = None
    total_interest: Optional[Decimal] = None
    refinance_rate: Optional[float] = None
    refinance_savings: Optional[Decimal] = None


class PlanMetrics(BaseModel):
    """Key plan performance metrics"""
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float
    required_savings_rate: float
    stress_test_30pct_drop: float
    stress_test_50pct_drop: Optional[float] = None
    max_drawdown_expected: float
    years_to_goal: float
    inflation_assumption: float = Field(default=0.03)


class TaxStrategy(BaseModel):
    """Tax optimization details"""
    tax_loss_harvest_annual: Optional[Decimal] = None
    roth_conversion_annual: Optional[Decimal] = None
    tax_efficient_placement: Dict[str, str] = Field(default_factory=dict)
    estimated_tax_savings: Decimal


class ClientInfo(BaseModel):
    """Client information for LLM context"""
    name: str
    age: int
    current_income: float
    user_id: int


class PlanOutput(BaseModel):
    """Complete deterministic plan output"""
    gap_analysis: GapAnalysis
    target_allocation: TargetAllocation
    rebalancing_trades: List[RebalancingTrade]
    contribution_schedule: ContributionSchedule
    debt_schedule: List[DebtAction]
    plan_metrics: PlanMetrics
    tax_strategy: Optional[TaxStrategy] = None
    client_info: Optional[ClientInfo] = None  # Added for LLM context
    calculation_timestamp: str
    calculation_version: str = Field(default="1.0.0")