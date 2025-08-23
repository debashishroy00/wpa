"""
WealthPath AI - Financial Data Models
"""
from sqlalchemy import Boolean, Column, Integer, String, DateTime, Date, Text, Numeric, Enum as SQLEnum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from decimal import Decimal

from app.db.session import Base


class AccountType(enum.Enum):
    checking = "checking"
    savings = "savings"
    investment = "investment"
    retirement = "retirement"
    credit = "credit"
    loan = "loan"
    mortgage = "mortgage"
    crypto = "crypto"


class EntryCategory(enum.Enum):
    assets = "assets"
    liabilities = "liabilities"
    income = "income"
    expenses = "expenses"


class DataQuality(enum.Enum):
    DQ1 = "DQ1"  # Real-time API data (highest quality)
    DQ2 = "DQ2"  # Daily API sync
    DQ3 = "DQ3"  # Manual entry with validation
    DQ4 = "DQ4"  # Manual entry, unverified


class FrequencyType(enum.Enum):
    one_time = "one_time"
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    quarterly = "quarterly"
    annually = "annually"


class FinancialAccount(Base):
    """
    Financial accounts (bank accounts, investment accounts, etc.)
    """
    __tablename__ = "financial_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Account Information
    account_type = Column(SQLEnum(AccountType), nullable=False)
    institution_name = Column(String(100), nullable=False)
    account_name = Column(String(100), nullable=False)
    account_number_masked = Column(String(20), nullable=True)  # Last 4 digits only
    
    # Integration Details
    plaid_account_id = Column(String(100), nullable=True, index=True)
    plaid_item_id = Column(String(100), nullable=True)
    external_account_id = Column(String(100), nullable=True)
    
    # Data Quality
    data_quality = Column(SQLEnum(DataQuality), default=DataQuality.DQ4, nullable=False)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    sync_frequency = Column(String(20), default="daily", nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_manual = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="financial_accounts")
    entries = relationship("FinancialEntry", back_populates="account")
    balances = relationship("AccountBalance", back_populates="account")

    def __repr__(self):
        return f"<FinancialAccount(id={self.id}, user_id={self.user_id}, type='{self.account_type.value}')>"


class FinancialEntry(Base):
    """
    Individual financial entries (transactions, balances, manual inputs)
    """
    __tablename__ = "financial_entries"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("financial_accounts.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # Direct user reference for manual entries
    
    # Entry Information
    category = Column(SQLEnum(EntryCategory), nullable=False, index=True)
    subcategory = Column(String(50), nullable=True)  # More specific categorization
    description = Column(String(255), nullable=False)
    
    # Financial Data
    amount = Column(Numeric(12, 2), nullable=False)  # Support up to 999,999,999.99
    currency = Column(String(3), default="USD", nullable=False)
    
    # Frequency and Timing
    frequency = Column(SQLEnum(FrequencyType), default=FrequencyType.one_time, nullable=False)
    entry_date = Column(DateTime(timezone=True), nullable=False, index=True)
    end_date = Column(DateTime(timezone=True), nullable=True)  # For recurring entries
    
    # Data Quality and Source
    data_quality = Column(SQLEnum(DataQuality), default=DataQuality.DQ4, nullable=False)
    confidence_score = Column(Numeric(3, 2), default=Decimal('1.00'), nullable=False)  # 0.00 to 1.00
    source = Column(String(50), default="manual", nullable=False)  # manual, plaid, api, etc.
    
    # External References
    external_transaction_id = Column(String(100), nullable=True, index=True)
    plaid_transaction_id = Column(String(100), nullable=True)
    
    # Asset Allocation columns (from migration)
    stock_percentage = Column(Integer, nullable=True, default=0)
    bond_percentage = Column(Integer, nullable=True, default=0)
    cash_percentage = Column(Integer, nullable=True, default=0)
    other_percentage = Column(Integer, nullable=True, default=0)
    
    # New 5-asset allocation system
    real_estate_percentage = Column(Integer, nullable=True, default=0)
    stocks_percentage = Column(Integer, nullable=True, default=0)
    bonds_percentage = Column(Integer, nullable=True, default=0)
    alternative_percentage = Column(Integer, nullable=True, default=0)
    
    # Enhanced Liability Fields
    interest_rate = Column(Numeric(5, 3), nullable=True)  # e.g., 4.250 for 4.25%
    loan_term_months = Column(Integer, nullable=True)  # Original loan term in months
    remaining_months = Column(Integer, nullable=True)  # Months left on loan
    minimum_payment = Column(Numeric(10, 2), nullable=True)  # Minimum monthly payment
    is_fixed_rate = Column(Boolean, default=True, nullable=True)  # Fixed vs variable rate
    loan_start_date = Column(DateTime(timezone=True), nullable=True)  # When loan started
    original_amount = Column(Numeric(12, 2), nullable=True)  # Original loan amount
    
    # Calculated Fields for Enhanced AI Context
    daily_interest_cost = Column(Numeric(10, 2), nullable=True)  # Daily interest cost
    total_interest_lifetime = Column(Numeric(10, 2), nullable=True)  # Total interest over life of loan
    payoff_date = Column(Date, nullable=True)  # Estimated payoff date
    
    # Vector DB Sync Tracking
    last_synced_to_vector = Column(DateTime(timezone=True), nullable=True)  # Last sync to vector DB
    
    # Metadata  
    details = Column(Text, nullable=True)  # JSONB for additional metadata
    tags = Column(Text, nullable=True)  # JSON array of tags
    notes = Column(Text, nullable=True)
    loan_details = Column(Text, nullable=True)  # JSONB for subcategory-specific data
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_recurring = Column(Boolean, default=False, nullable=False)
    is_estimate = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    account = relationship("FinancialAccount", back_populates="entries")
    user = relationship("User")

    def __repr__(self):
        return f"<FinancialEntry(id={self.id}, category='{self.category.value}', amount={self.amount})>"


class AccountBalance(Base):
    """
    Account balance snapshots over time
    """
    __tablename__ = "account_balances"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("financial_accounts.id"), nullable=False, index=True)
    
    # Balance Information
    balance = Column(Numeric(12, 2), nullable=False)
    available_balance = Column(Numeric(12, 2), nullable=True)  # For credit/checking accounts
    currency = Column(String(3), default="USD", nullable=False)
    
    # Balance Type
    balance_type = Column(String(20), default="current", nullable=False)  # current, available, pending
    
    # Data Source
    as_of_date = Column(DateTime(timezone=True), nullable=False, index=True)
    source_type = Column(String(20), default="api", nullable=False)  # api, manual, calculated
    data_quality = Column(SQLEnum(DataQuality), default=DataQuality.DQ1, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    account = relationship("FinancialAccount", back_populates="balances")

    def __repr__(self):
        return f"<AccountBalance(id={self.id}, account_id={self.account_id}, balance={self.balance})>"


class NetWorthSnapshot(Base):
    """
    Net worth calculations over time
    """
    __tablename__ = "net_worth_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Net Worth Components
    total_assets = Column(Numeric(12, 2), nullable=False)
    total_liabilities = Column(Numeric(12, 2), nullable=False)
    net_worth = Column(Numeric(12, 2), nullable=False)
    
    # Breakdown by Category
    liquid_assets = Column(Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    investment_assets = Column(Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    real_estate_assets = Column(Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    other_assets = Column(Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    
    # Calculation Metadata
    calculation_method = Column(String(20), default="sum", nullable=False)
    confidence_score = Column(Numeric(3, 2), default=Decimal('1.00'), nullable=False)
    data_quality_score = Column(String(3), nullable=False)  # Overall DQ score
    
    # Timestamps
    snapshot_date = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<NetWorthSnapshot(id={self.id}, user_id={self.user_id}, net_worth={self.net_worth})>"