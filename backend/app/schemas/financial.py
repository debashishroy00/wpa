"""
WealthPath AI - Financial Data Schemas
"""
from typing import Optional, List
from pydantic import BaseModel, field_validator
from datetime import datetime
from decimal import Decimal
from enum import Enum


class AccountType(str, Enum):
    checking = "checking"
    savings = "savings"
    investment = "investment"
    retirement = "retirement"
    credit = "credit"
    loan = "loan"
    mortgage = "mortgage"
    crypto = "crypto"


class EntryCategory(str, Enum):
    assets = "assets"
    liabilities = "liabilities"
    income = "income"
    expenses = "expenses"


class DataQuality(str, Enum):
    DQ1 = "DQ1"  # Real-time API data
    DQ2 = "DQ2"  # Daily API sync
    DQ3 = "DQ3"  # Manual entry with validation
    DQ4 = "DQ4"  # Manual entry, unverified


class FrequencyType(str, Enum):
    one_time = "one_time"
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    quarterly = "quarterly"
    annually = "annually"


class FinancialEntryBase(BaseModel):
    """
    Base schema for financial entries
    """
    category: EntryCategory
    description: str
    amount: Decimal
    frequency: FrequencyType = FrequencyType.one_time
    currency: str = "USD"
    subcategory: Optional[str] = None
    entry_date: Optional[datetime] = None
    notes: Optional[str] = None
    
    # Asset Allocation (database column names)
    real_estate_percentage: Optional[int] = None   # 0-100
    stocks_percentage: Optional[int] = None        # 0-100
    bonds_percentage: Optional[int] = None         # 0-100
    cash_percentage: Optional[int] = None          # 0-100  
    alternative_percentage: Optional[int] = None   # 0-100
    
    # Enhanced Liability Fields
    interest_rate: Optional[Decimal] = None         # Annual interest rate (e.g., 4.25 for 4.25%)
    loan_term_months: Optional[int] = None          # Original loan term in months
    remaining_months: Optional[int] = None          # Months remaining on loan
    minimum_payment: Optional[Decimal] = None       # Minimum monthly payment
    is_fixed_rate: Optional[bool] = True            # Fixed vs variable rate
    loan_start_date: Optional[datetime] = None      # When loan started
    original_amount: Optional[Decimal] = None       # Original loan amount
    loan_details: Optional[str] = None              # JSON string for subcategory-specific data
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if len(v.strip()) < 3:
            raise ValueError('Description must be at least 3 characters')
        return v.strip()
    
    @field_validator('real_estate_percentage', 'stocks_percentage', 'bonds_percentage', 'cash_percentage', 'alternative_percentage')
    @classmethod
    def validate_percentage(cls, v):
        if v is not None:
            if v < 0 or v > 100:
                raise ValueError('Percentage must be between 0 and 100')
        return v
    
    @field_validator('interest_rate')
    @classmethod
    def validate_interest_rate(cls, v):
        if v is not None:
            if v < 0 or v > 50:  # 0% to 50% (max reasonable rate)
                raise ValueError('Interest rate must be between 0% and 50%')
        return v
    
    @field_validator('loan_term_months', 'remaining_months')
    @classmethod
    def validate_months(cls, v):
        if v is not None:
            if v < 0 or v > 600:  # Max 50 years
                raise ValueError('Months must be between 0 and 600')
        return v
    
    @field_validator('minimum_payment', 'original_amount')
    @classmethod
    def validate_payment_amount(cls, v):
        if v is not None:
            if v < 0:
                raise ValueError('Payment amounts must be non-negative')
        return v


class FinancialEntryCreate(FinancialEntryBase):
    """
    Schema for creating financial entries
    """
    pass


class FinancialEntryUpdate(BaseModel):
    """
    Schema for updating financial entries
    """
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    frequency: Optional[FrequencyType] = None
    subcategory: Optional[str] = None
    notes: Optional[str] = None
    
    # Asset Allocation (database column names)
    real_estate_percentage: Optional[int] = None
    stocks_percentage: Optional[int] = None
    bonds_percentage: Optional[int] = None
    cash_percentage: Optional[int] = None
    alternative_percentage: Optional[int] = None
    
    # Enhanced Liability Fields
    interest_rate: Optional[Decimal] = None
    loan_term_months: Optional[int] = None
    remaining_months: Optional[int] = None
    minimum_payment: Optional[Decimal] = None
    is_fixed_rate: Optional[bool] = None
    loan_start_date: Optional[datetime] = None
    original_amount: Optional[Decimal] = None
    loan_details: Optional[str] = None
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Amount must be positive')
        return v


class FinancialEntryResponse(FinancialEntryBase):
    """
    Schema for financial entry responses
    """
    id: str
    user_id: int
    data_quality: DataQuality
    confidence_score: Decimal
    source: str = "manual"
    is_active: bool = True
    is_recurring: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class FinancialAccountBase(BaseModel):
    """
    Base schema for financial accounts
    """
    account_type: AccountType
    institution_name: str
    account_name: str
    account_number_masked: Optional[str] = None


class FinancialAccountCreate(FinancialAccountBase):
    """
    Schema for creating financial accounts
    """
    pass


class FinancialAccountResponse(FinancialAccountBase):
    """
    Schema for financial account responses
    """
    id: int
    user_id: int
    data_quality: DataQuality
    last_sync_at: Optional[datetime] = None
    is_active: bool = True
    is_manual: bool = False
    created_at: datetime
    
    model_config = {"from_attributes": True}


class AccountBalanceResponse(BaseModel):
    """
    Schema for account balance responses
    """
    id: int
    account_id: int
    balance: Decimal
    available_balance: Optional[Decimal] = None
    currency: str = "USD"
    balance_type: str = "current"
    as_of_date: datetime
    source_type: str = "api"
    data_quality: DataQuality
    
    model_config = {"from_attributes": True}


class FinancialSummary(BaseModel):
    """
    Schema for financial summary dashboard
    """
    user_id: int
    net_worth: Decimal
    total_assets: Decimal
    total_liabilities: Decimal
    last_updated: datetime
    data_quality_score: DataQuality
    
    # Detailed breakdowns
    liquid_assets: Optional[Decimal] = None
    investment_assets: Optional[Decimal] = None
    real_estate_assets: Optional[Decimal] = None
    other_assets: Optional[Decimal] = None
    
    # Account counts
    connected_accounts: int = 0
    manual_entries: int = 0
    
    # Change indicators
    net_worth_change: Optional[Decimal] = None
    net_worth_change_percentage: Optional[Decimal] = None


class NetWorthSnapshot(BaseModel):
    """
    Schema for net worth historical snapshots
    """
    id: int
    user_id: int
    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal
    liquid_assets: Decimal
    investment_assets: Decimal
    real_estate_assets: Decimal
    other_assets: Decimal
    confidence_score: Decimal
    data_quality_score: DataQuality
    snapshot_date: datetime
    
    model_config = {"from_attributes": True}


class AssetBreakdown(BaseModel):
    """
    Schema for asset category breakdown
    """
    category: str
    amount: Decimal
    percentage: Decimal
    data_quality: DataQuality
    account_count: int


class LiabilityBreakdown(BaseModel):
    """
    Schema for liability category breakdown
    """
    category: str
    amount: Decimal
    percentage: Decimal
    data_quality: DataQuality
    monthly_payment: Optional[Decimal] = None
    interest_rate: Optional[Decimal] = None


class FinancialHealthScore(BaseModel):
    """
    Schema for overall financial health assessment
    """
    user_id: int
    overall_score: int  # 1-100
    debt_to_income_ratio: Optional[Decimal] = None
    savings_rate: Optional[Decimal] = None
    emergency_fund_months: Optional[Decimal] = None
    investment_diversification: Optional[int] = None
    
    # Component scores
    liquidity_score: int
    debt_management_score: int
    savings_score: int
    investment_score: int
    
    # Recommendations
    top_recommendations: List[str] = []
    calculated_at: datetime


class DataSync(BaseModel):
    """
    Schema for data synchronization requests
    """
    sync_id: str
    status: str = "pending"
    accounts_synced: int = 0
    entries_updated: int = 0
    errors: List[str] = []
    started_at: datetime
    completed_at: Optional[datetime] = None


# Enhanced Liability Type-Specific Schemas

class MortgageFormData(BaseModel):
    """
    Mortgage-specific form data
    """
    # Basic (required)
    description: str
    current_balance: Decimal
    monthly_payment: Decimal
    
    # Loan Details (required)
    interest_rate: Decimal
    loan_term_years: int
    remaining_years: int
    is_fixed_rate: bool = True
    
    # Property Info (optional)
    property_value: Optional[Decimal] = None
    purchase_date: Optional[datetime] = None
    
    # Additional (optional)
    escrow_included: Optional[bool] = None
    tax_deductible: Optional[bool] = None
    refinance_date: Optional[datetime] = None


class CreditCardFormData(BaseModel):
    """
    Credit card-specific form data
    """
    # Basic (required)
    card_name: str
    current_balance: Decimal
    credit_limit: Decimal
    
    # Rate Info (required)
    apr: Decimal
    intro_apr: Optional[Decimal] = None
    intro_apr_end_date: Optional[datetime] = None
    
    # Payment Info
    minimum_payment: Optional[Decimal] = None
    average_monthly_payment: Optional[Decimal] = None
    
    # Usage and rewards
    rewards_type: Optional[str] = None  # "cashback" | "points" | "miles"


class AutoLoanFormData(BaseModel):
    """
    Auto loan-specific form data
    """
    # Basic
    vehicle_description: str
    current_balance: Decimal
    monthly_payment: Decimal
    
    # Loan Details
    interest_rate: Decimal
    original_loan_amount: Decimal
    loan_term_months: int
    remaining_months: int
    
    # Vehicle Info
    vehicle_value: Optional[Decimal] = None
    vehicle_year: Optional[int] = None
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None


class StudentLoanFormData(BaseModel):
    """
    Student loan-specific form data
    """
    # Basic
    loan_servicer: str
    current_balance: Decimal
    monthly_payment: Decimal
    
    # Loan Details
    interest_rate: Decimal
    loan_type: str  # "federal" | "private"
    
    # Federal Loan Specific
    repayment_plan: Optional[str] = None
    subsidized: Optional[bool] = None
    eligible_for_forgiveness: Optional[bool] = None
    
    # Dates
    graduation_date: Optional[datetime] = None
    first_payment_date: Optional[datetime] = None
    expected_payoff_date: Optional[datetime] = None


class PersonalLoanFormData(BaseModel):
    """
    Personal/Other loan-specific form data
    """
    description: str
    current_balance: Decimal
    monthly_payment: Decimal
    interest_rate: Decimal
    loan_term_months: int
    remaining_months: int
    purpose: Optional[str] = None  # "debt consolidation" | "home improvement"
    secured: bool = False


class LiabilityFormData(BaseModel):
    """
    Union type for different liability forms
    """
    subcategory: str
    form_data: dict  # Contains the type-specific data
    
    # Common fields that apply to all liability types
    category: str = "liabilities"
    currency: str = "USD"
    entry_date: datetime = None