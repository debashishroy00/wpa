"""
WealthPath AI - Financial Data Endpoints
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from datetime import datetime, timezone
from decimal import Decimal
import structlog
import uuid
import json

from app.db.session import get_db
from app.models.user import User
from app.models.financial import (
    FinancialEntry, FinancialAccount, AccountBalance, NetWorthSnapshot,
    EntryCategory, DataQuality, FrequencyType
)
from app.schemas.financial import (
    FinancialSummary, FinancialEntryCreate, FinancialEntryResponse,
    FinancialEntryUpdate, FinancialAccountResponse, AccountBalanceResponse,
    NetWorthSnapshot as NetWorthSnapshotSchema, AssetBreakdown, LiabilityBreakdown
)
from app.api.v1.endpoints.auth import get_current_active_user
from app.services.financial_calculator import FinancialCalculator
from app.services.complete_financial_context_service import CompleteFinancialContextService
from app.services.vector_db_service import get_vector_db

logger = structlog.get_logger()
router = APIRouter()

# Initialize services
calculator = FinancialCalculator()
context_service = CompleteFinancialContextService()

async def sync_to_vector_db(entry):
    """Helper function to sync entry to vector DB"""
    try:
        vector_db = get_vector_db()
        await vector_db.sync_financial_entry(entry)
        # Update sync timestamp
        entry.last_synced_to_vector = datetime.now(timezone.utc)
        logger.info(f"Successfully synced entry {entry.id} to vector DB")
    except Exception as e:
        logger.warning(f"Vector sync failed for entry {entry.id}: {e}")
        # Don't fail the request if sync fails


def categorize_financial_entry(category: str, description: str, subcategory: str = None) -> str:
    """
    Map user entries to proper display categories based on description and category
    """
    description_lower = description.lower()
    
    # Debug logging
    print(f"🔍 CATEGORIZE: description='{description}', category='{category}', subcategory='{subcategory}'")
    
    # If a valid subcategory is already provided that matches our expected values, use it
    if subcategory and category == "assets":
        if subcategory in ['retirement_accounts', 'investment_accounts', 'cash_bank_accounts', 
                          'real_estate', 'personal_property', 'business_assets']:
            print(f"✅ Using existing subcategory: {subcategory}")
            return subcategory
    
    # Check for valid expense subcategories
    if subcategory and category == "expenses":
        if subcategory in ['housing', 'utilities', 'transportation', 'food', 'healthcare', 'personal']:
            print(f"✅ Using existing expense subcategory: {subcategory}")
            return subcategory
    
    if category == "assets":
        # Retirement Accounts (check first - highest priority)
        if any(keyword in description_lower for keyword in ['401k', '401(k)', '401 k', 'ira', 'roth', 'retirement', 'pension', 'sep', '403b', 'tsp', '529']):
            print(f"➡️ Matched retirement: {description}")
            return "retirement_accounts"
        # Investment Accounts (check before cash accounts to avoid conflicts)
        elif any(keyword in description_lower for keyword in ['mutual fund', 'etf', 'stock', 'bond', 'brokerage', 'investment', 'portfolio', 'crypto', 'bitcoin', 'btc', 'ethereum', 'equity', 'securities', 'etrade', 'e-trade', 'robinhood', 'vanguard', 'fidelity', 'schwab', 'ameritrade', 'pacific life']):
            print(f"➡️ Matched investment: {description}")
            return "investment_accounts"
        # Cash & Bank Accounts (only pure cash/bank products)
        elif any(keyword in description_lower for keyword in ['checking', 'savings', 'money market', 'cd', 'certificate', 'offshore']) and not any(keyword in description_lower for keyword in ['mutual', 'fund', 'etf', 'stock', 'investment']):
            return "cash_bank_accounts"
        # Real Estate
        elif any(keyword in description_lower for keyword in ['home', 'house', 'property', 'real estate', 'residence', 'rental', 'mortgage']):
            return "real_estate"
        # Personal Property
        elif any(keyword in description_lower for keyword in ['jewelry', 'art', 'collectible', 'vehicle', 'car', 'electronics', 'furniture']):
            return "personal_property"
        # Business Assets
        elif any(keyword in description_lower for keyword in ['business', 'company', 'llc', 'corporation', 'equipment', 'inventory']):
            return "business_assets"
        else:
            print(f"⚠️ No match found, defaulting to other_assets: {description}")
            return "other_assets"
    
    elif category == "income":
        # Employment Income
        if any(keyword in description_lower for keyword in ['salary', 'wage', 'payroll', 'employment', 'job', 'work', 'employer', 'paycheck']):
            return "employment_income"
        # Investment Income (including rental)
        elif any(keyword in description_lower for keyword in ['rental', 'rent', 'dividend', 'interest', 'capital gain', 'investment', 'crypto']):
            return "investment_income"
        # Stock/RSU Income (treat as employment)
        elif any(keyword in description_lower for keyword in ['rsu', 'stock', 'equity', 'shares', 'vesting']):
            return "employment_income"
        # 401K contributions (treat as employment benefit)
        elif any(keyword in description_lower for keyword in ['401k', '401(k)', 'contribution', 'retirement']):
            return "employment_income"
        # Business Income
        elif any(keyword in description_lower for keyword in ['business', 'self-employment', 'consulting', 'freelance', 'contractor']):
            return "business_income"
        else:
            return "other_income"
    
    elif category == "liabilities":
        # Mortgages
        if any(keyword in description_lower for keyword in ['mortgage', 'home loan', 'house loan', 'property loan']):
            return "mortgage_real_estate"
        # Student Loans
        elif any(keyword in description_lower for keyword in ['student', 'education', 'tuition']):
            return "student_loans"
        # Credit Cards
        elif any(keyword in description_lower for keyword in ['credit card', 'visa', 'mastercard', 'amex']):
            return "credit_cards"
        # Auto Loans
        elif any(keyword in description_lower for keyword in ['auto', 'car', 'vehicle', 'truck']):
            return "auto_loans"
        # Personal Loans
        elif any(keyword in description_lower for keyword in ['personal', 'loan']):
            return "personal_loans"
        else:
            return "other_debt"
    
    elif category == "expenses":
        # Housing Expenses (remove utilities from here)
        if any(keyword in description_lower for keyword in ['mortgage', 'rent', 'property tax', 'insurance', 'hoa']) and not any(keyword in description_lower for keyword in ['electricity', 'gas', 'water', 'internet', 'phone', 'trash', 'sewer']):
            return "housing"
        # Utilities (separate from housing) - be more specific with gas
        elif any(keyword in description_lower for keyword in ['electricity', 'electric', 'water', 'internet', 'phone', 'trash', 'sewer', 'utilities', 'cable', 'wifi']) or ('gas' in description_lower and any(keyword in description_lower for keyword in ['bill', 'utility', 'home', 'house', 'heating', 'natural'])):
            return "utilities"
        # Transportation - gas for cars goes here
        elif any(keyword in description_lower for keyword in ['car', 'auto', 'vehicle', 'transportation', 'uber', 'lyft', 'taxi', 'bus', 'train', 'parking']) or ('gas' in description_lower and any(keyword in description_lower for keyword in ['station', 'fuel', 'gasoline', 'car', 'vehicle', 'auto'])):
            return "transportation"
        # Food & Dining (changed from "food" to match frontend)
        elif any(keyword in description_lower for keyword in ['restaurant', 'food', 'grocery', 'dining', 'meal', 'coffee', 'lunch', 'dinner', 'breakfast']):
            return "food"
        # Healthcare
        elif any(keyword in description_lower for keyword in ['medical', 'health', 'doctor', 'prescription', 'dental', 'vision', 'hospital', 'clinic']):
            return "healthcare"
        # Personal (combines shopping and entertainment)
        elif any(keyword in description_lower for keyword in ['merchandise', 'shopping', 'clothing', 'amazon', 'retail', 'entertainment', 'movie', 'subscription', 'netflix', 'spotify', 'personal care', 'beauty', 'gym', 'fitness', 'travel', 'vacation']):
            return "personal"
        else:
            return "other_expenses"
    
    elif category == "income":
        # Employment Income
        if any(keyword in description_lower for keyword in ['salary', 'wage', 'employment', 'job', 'paycheck']):
            return "employment_income"
        # Business Income
        elif any(keyword in description_lower for keyword in ['business', 'self-employed', 'freelance', 'consulting']):
            return "business_income"
        # Investment Income
        elif any(keyword in description_lower for keyword in ['dividend', 'interest', 'capital gains', 'rental']):
            return "investment_income"
        else:
            return "other_income"
    
    return subcategory or "other"


def classify_asset_for_portfolio(description: str, subcategory: str = None) -> str:
    """
    Classify assets specifically for portfolio analysis by asset class.
    This is different from categorize_financial_entry which groups by account type.
    
    Asset Classes for Portfolio Analysis:
    - stocks: Equities, ETFs, individual stocks
    - bonds: Fixed income, bonds, bond funds
    - real_estate: Real estate, REITs, property
    - cash: Cash equivalents, savings, checking
    - alternative: Crypto, commodities, private equity
    - retirement: Mixed retirement accounts (to be broken down further)
    """
    description_lower = description.lower()
    
    # Real Estate (including REITs)
    if any(keyword in description_lower for keyword in [
        'home', 'house', 'property', 'real estate', 'residence', 'rental', 
        'mortgage', 'reit', 'real estate investment trust'
    ]):
        return "real_estate"
    
    # Alternative Investments (Crypto, Commodities, etc.)
    elif any(keyword in description_lower for keyword in [
        'bitcoin', 'crypto', 'btc', 'eth', 'ethereum', 'dogecoin', 'cryptocurrency',
        'gold', 'silver', 'commodity', 'precious metals', 'hedge fund', 'private equity'
    ]):
        return "alternative"
    
    # Cash & Cash Equivalents
    elif any(keyword in description_lower for keyword in [
        'checking', 'savings', 'money market', 'cd', 'certificate of deposit',
        'cash', 'offshore', 'high yield savings'
    ]) and not any(keyword in description_lower for keyword in ['mutual', 'fund', 'etf', 'stock', 'investment', 'bond']):
        return "cash"
    
    # Bonds & Fixed Income
    elif any(keyword in description_lower for keyword in [
        'bond', 'treasury', 'fixed income', 'government bond', 'corporate bond',
        'municipal bond', 'bond fund', 'bnd', 'agg', 'fixed', 'pacific life'
    ]):
        return "bonds"
    
    # Stocks & Equities (including brokerages and equity funds)
    elif any(keyword in description_lower for keyword in [
        'stock', 'equity', 'etf', 'mutual fund', 'brokerage', 'investment', 
        'portfolio', 'securities', 'etrade', 'robinhood', 'vanguard', 'fidelity',
        'spy', 'voo', 'qqq', 'growth', 'value', 'international', 'emerging',
        'index fund', 'total stock'
    ]):
        return "stocks"
    
    # Retirement Accounts (mixed - need further breakdown)
    elif any(keyword in description_lower for keyword in [
        '401k', '401(k)', 'ira', 'roth', 'retirement', 'pension', 'sep', 
        '403b', 'tsp', '529', 'hsa', 'health savings'
    ]):
        return "retirement"
    
    # Default to other if can't classify
    else:
        return "other"


def calculate_portfolio_allocation(entries: List[FinancialEntry]) -> dict:
    """
    Calculate portfolio allocation percentages by asset class for portfolio analysis.
    This addresses the core issue where everything was lumped into "Other Assets".
    """
    allocation = {
        'stocks': 0,
        'bonds': 0, 
        'real_estate': 0,
        'cash': 0,
        'alternative': 0,
        'retirement': 0,  # Will be broken down further
        'other': 0
    }
    
    for entry in entries:
        if entry.category == EntryCategory.assets:
            asset_class = classify_asset_for_portfolio(entry.description, entry.subcategory)
            allocation[asset_class] += float(entry.amount)
    
    # For retirement accounts, use actual breakdown if available, otherwise default allocation
    retirement_entries = [e for e in entries if e.category == EntryCategory.assets and 
                         classify_asset_for_portfolio(e.description, e.subcategory) == "retirement"]
    
    for entry in retirement_entries:
        entry_amount = float(entry.amount)
        
        # Check if user provided asset breakdown
        if (entry.stock_percentage is not None and entry.bond_percentage is not None and
            entry.cash_percentage is not None and entry.other_percentage is not None):
            
            # Use user-provided breakdown
            allocation['stocks'] += entry_amount * (entry.stock_percentage / 100)
            allocation['bonds'] += entry_amount * (entry.bond_percentage / 100)
            allocation['cash'] += entry_amount * (entry.cash_percentage / 100)
            allocation['other'] += entry_amount * (entry.other_percentage / 100)
            
        else:
            # Use default allocation (60/40 stocks/bonds) for retirement accounts without breakdown
            allocation['stocks'] += entry_amount * 0.6  # 60% stocks
            allocation['bonds'] += entry_amount * 0.4   # 40% bonds
    
    # Remove retirement as separate category since we've allocated it
    allocation['retirement'] = 0
    
    # Calculate total for percentages
    total = sum(allocation.values())
    
    if total > 0:
        # Convert to percentages and round
        percentages = {
            asset_class: round((amount / total) * 100, 1) 
            for asset_class, amount in allocation.items()
            if amount > 0  # Only include asset classes with actual amounts
        }
        
        # Also return absolute amounts for calculations
        return {
            'percentages': percentages,
            'amounts': {k: v for k, v in allocation.items() if v > 0},
            'total': total
        }
    else:
        return {
            'percentages': {},
            'amounts': {},
            'total': 0
        }


def calculate_data_quality_score(entries: List[FinancialEntry]) -> DataQuality:
    """
    Calculate overall data quality score based on entry mix
    DQ1: >50% real-time API data
    DQ2: >50% daily sync data
    DQ3: >50% verified manual entries  
    DQ4: Mostly unverified manual entries
    """
    if not entries:
        return DataQuality.DQ4
    
    dq_counts = {dq: 0 for dq in DataQuality}
    for entry in entries:
        dq_counts[entry.data_quality] += 1
    
    total = len(entries)
    if dq_counts[DataQuality.DQ1] / total > 0.5:
        return DataQuality.DQ1
    elif dq_counts[DataQuality.DQ2] / total > 0.5:
        return DataQuality.DQ2
    elif dq_counts[DataQuality.DQ3] / total > 0.5:
        return DataQuality.DQ3
    else:
        return DataQuality.DQ4


@router.get("/summary", response_model=FinancialSummary)
def get_financial_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get user's financial summary (net worth breakdown)
    """
    # Get latest net worth snapshot
    latest_snapshot = db.query(NetWorthSnapshot).filter(
        NetWorthSnapshot.user_id == current_user.id
    ).order_by(desc(NetWorthSnapshot.snapshot_date)).first()
    
    if latest_snapshot:
        # Use existing snapshot
        return FinancialSummary(
            user_id=current_user.id,
            net_worth=latest_snapshot.net_worth,
            total_assets=latest_snapshot.total_assets,
            total_liabilities=latest_snapshot.total_liabilities,
            last_updated=latest_snapshot.snapshot_date,
            data_quality_score=DataQuality(latest_snapshot.data_quality_score),
            liquid_assets=latest_snapshot.liquid_assets,
            investment_assets=latest_snapshot.investment_assets,
            real_estate_assets=latest_snapshot.real_estate_assets,
            other_assets=latest_snapshot.other_assets,
            connected_accounts=db.query(FinancialAccount).filter(
                and_(FinancialAccount.user_id == current_user.id, FinancialAccount.is_active == True)
            ).count(),
            manual_entries=db.query(FinancialEntry).filter(
                and_(FinancialEntry.user_id == current_user.id, FinancialEntry.source == "manual")
            ).count()
        )
    else:
        # Calculate on-the-fly with proper categorization
        entries = db.query(FinancialEntry).filter(
            and_(FinancialEntry.user_id == current_user.id, FinancialEntry.is_active == True)
        ).all()
        
        # Separate assets, liabilities, and income
        asset_entries = [e for e in entries if e.category == EntryCategory.assets]
        liability_entries = [e for e in entries if e.category == EntryCategory.liabilities]
        income_entries = [e for e in entries if e.category == EntryCategory.income]
        
        # Calculate totals (exclude income from net worth)
        total_assets = sum(e.amount for e in asset_entries)
        total_liabilities = sum(e.amount for e in liability_entries)
        net_worth = total_assets - total_liabilities
        
        # Categorize assets properly
        real_estate_assets = Decimal('0.00')
        retirement_assets = Decimal('0.00') 
        investment_assets = Decimal('0.00')
        cash_assets = Decimal('0.00')
        other_assets = Decimal('0.00')
        
        for entry in asset_entries:
            category_type = categorize_financial_entry(entry.category.value, entry.description, entry.subcategory)
            if category_type == "real_estate":
                real_estate_assets += entry.amount
            elif category_type == "retirement":
                retirement_assets += entry.amount
            elif category_type == "investments":
                investment_assets += entry.amount
            elif category_type == "cash":
                cash_assets += entry.amount
            else:
                other_assets += entry.amount
        
        return FinancialSummary(
            user_id=current_user.id,
            net_worth=net_worth,
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            last_updated=datetime.now(timezone.utc),
            data_quality_score=calculate_data_quality_score(entries),
            liquid_assets=cash_assets,
            investment_assets=investment_assets,
            real_estate_assets=real_estate_assets,
            other_assets=other_assets,
            connected_accounts=db.query(FinancialAccount).filter(
                and_(FinancialAccount.user_id == current_user.id, FinancialAccount.is_active == True)
            ).count(),
            manual_entries=len([e for e in entries if e.source == "manual"])
        )


def map_legacy_subcategory(category: str, subcategory: str, description: str) -> str:
    """
    Map legacy subcategories and descriptions to standardized subcategory values
    """
    if not subcategory:
        subcategory = ""
    
    subcategory_lower = subcategory.lower()
    description_lower = description.lower()
    
    if category == "assets":
        # If already using new format, keep it
        if subcategory in ['cash_bank_accounts', 'investment_accounts', 'retirement_accounts', 
                          'real_estate', 'personal_property', 'business_assets', 'other_assets']:
            return subcategory
        
        # Map legacy categories and descriptions
        if any(keyword in description_lower for keyword in ['401k', '401(k)', 'retirement']):
            return 'retirement_accounts'
        elif any(keyword in description_lower for keyword in ['checking', 'savings', 'money market', 'cd']):
            return 'cash_bank_accounts'
        elif any(keyword in subcategory_lower for keyword in ['cash']) or 'checking' in description_lower:
            return 'cash_bank_accounts'
        elif any(keyword in description_lower for keyword in ['mutual fund', 'etf', "etf's"]) or 'investments' in subcategory_lower:
            return 'investment_accounts'
        elif any(keyword in description_lower for keyword in ['home', 'house', 'property', 'residence']):
            return 'real_estate'
        elif any(keyword in description_lower for keyword in ['jewelry']):
            return 'personal_property'
        else:
            return 'other_assets'
    
    elif category == "liabilities":
        if subcategory in ['mortgage_real_estate', 'credit_cards', 'auto_loans', 'student_loans', 'personal_loans', 'other_debt']:
            return subcategory
        elif any(keyword in description_lower for keyword in ['credit', 'card']):
            return 'credit_cards'
        elif any(keyword in description_lower for keyword in ['mortgage', 'home loan']):
            return 'mortgage_real_estate'
        else:
            return 'other_debt'
    
    elif category == "income":
        if subcategory in ['employment_income', 'business_income', 'investment_income', 'rental_income', 'passive_income', 'other_income']:
            return subcategory
        elif any(keyword in description_lower for keyword in ['salary', 'rsu', 'contribution']):
            return 'employment_income'
        elif 'rental' in description_lower:
            return 'rental_income'
        else:
            return 'other_income'
    
    elif category == "expenses":
        if subcategory in ['housing', 'utilities', 'transportation', 'food', 'healthcare', 'personal', 'other_expenses']:
            return subcategory
        elif any(keyword in subcategory_lower for keyword in ['food', 'entertainment', 'shopping', 'subscription']):
            return 'personal'
        elif 'utilities' in subcategory_lower:
            return 'utilities'
        elif 'transportation' in subcategory_lower:
            return 'transportation'
        elif 'healthcare' in subcategory_lower:
            return 'healthcare'
        elif any(keyword in description_lower for keyword in ['merchandise', 'shopping', 'retail', 'amazon', 'walmart', 'target']):
            return 'personal'
        elif any(keyword in description_lower for keyword in ['mortgage', 'rent', 'property tax']):
            return 'housing'
        elif any(keyword in description_lower for keyword in ['restaurant', 'grocery', 'food', 'dining']):
            return 'food'
        elif any(keyword in description_lower for keyword in ['gas', 'uber', 'lyft', 'parking']):
            return 'transportation'
        elif any(keyword in description_lower for keyword in ['doctor', 'medical', 'pharmacy', 'gym']):
            return 'healthcare'
        elif any(keyword in description_lower for keyword in ['electric', 'water', 'internet', 'phone', 'utilities']):
            return 'utilities'
        else:
            return 'personal'  # Default to personal for general expenses
    
    return 'other_assets'  # Default fallback


@router.get("/entries/categorized")
def get_categorized_entries(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get all entries properly categorized for structured display
    """
    entries = db.query(FinancialEntry).filter(
        and_(
            FinancialEntry.user_id == current_user.id,
            FinancialEntry.is_active == True
        )
    ).all()
    
    print(f"🔍 DEBUG: Found {len(entries)} entries in database for user {current_user.id}")
    for entry in entries:
        print(f"🔍 Entry: {entry.description} | Category: {entry.category.value} | Subcategory: {entry.subcategory}")
    
    # Initialize structured response with new subcategory organization
    categorized = {
        'categories': {
            'assets': {
                'cash_bank_accounts': [],
                'investment_accounts': [],
                'retirement_accounts': [],
                'real_estate': [],
                'personal_property': [],
                'business_assets': [],
                'other_assets': []
            },
            'liabilities': {
                'mortgage_real_estate': [],
                'credit_cards': [],
                'auto_loans': [],
                'student_loans': [],
                'personal_loans': [],
                'other_debt': []
            },
            'income': {
                'employment_income': [],
                'business_income': [],
                'investment_income': [],
                'rental_income': [],
                'passive_income': [],
                'other_income': []
            },
            'expenses': {
                'housing': [],
                'utilities': [],
                'transportation': [],
                'food': [],
                'healthcare': [],
                'personal': [],
                'other_expenses': []
            }
        }
    }
    
    processed_count = 0
    for entry in entries:
        # Use the main categorization function instead of legacy mapping
        subcategory = categorize_financial_entry(entry.category.value, entry.description, entry.subcategory)
        print(f"🔍 CATEGORIZATION: {entry.description} -> {entry.category.value} -> {subcategory}")
        
        entry_data = {
            'id': str(entry.id),
            'description': entry.description,
            'category': entry.category.value,
            'subcategory': subcategory,
            'amount': float(entry.amount),
            'frequency': entry.frequency.value if entry.frequency else 'one_time',
            'notes': entry.notes,
            'created_at': entry.created_at.isoformat() if entry.created_at else None,
            # Include allocation fields for form editing
            'real_estate_percentage': entry.real_estate_percentage,
            'stocks_percentage': entry.stocks_percentage,
            'bonds_percentage': entry.bonds_percentage,
            'cash_percentage': entry.cash_percentage,
            'alternative_percentage': entry.alternative_percentage,
            # Include enhanced liability fields for form editing
            'interest_rate': entry.interest_rate,
            'loan_term_months': entry.loan_term_months,
            'remaining_months': entry.remaining_months,
            'minimum_payment': float(entry.minimum_payment) if entry.minimum_payment else None,
            'is_fixed_rate': entry.is_fixed_rate,
            'loan_start_date': entry.loan_start_date.isoformat() if entry.loan_start_date else None,
            'original_amount': float(entry.original_amount) if entry.original_amount else None,
            'loan_details': entry.loan_details
        }
        
        # Map to the correct category and subcategory
        if entry.category == EntryCategory.assets:
            if subcategory in categorized['categories']['assets']:
                categorized['categories']['assets'][subcategory].append(entry_data)
                print(f"✅ MAPPED: {entry.description} -> assets.{subcategory}")
            else:
                categorized['categories']['assets']['other_assets'].append(entry_data)
                print(f"⚠️ FALLBACK: {entry.description} -> assets.other_assets (subcategory '{subcategory}' not found)")
        elif entry.category == EntryCategory.liabilities:
            if subcategory in categorized['categories']['liabilities']:
                categorized['categories']['liabilities'][subcategory].append(entry_data)
            else:
                categorized['categories']['liabilities']['other_debt'].append(entry_data)
        elif entry.category == EntryCategory.income:
            # Use smart categorization based on description instead of subcategory
            smart_category = categorize_financial_entry("income", entry.description, entry.subcategory)
            print(f"🎯 Smart income categorization: '{entry.description}' -> '{smart_category}'")
            if smart_category in categorized['categories']['income']:
                categorized['categories']['income'][smart_category].append(entry_data)
            else:
                categorized['categories']['income']['other_income'].append(entry_data)
        elif entry.category == EntryCategory.expenses:
            if subcategory in categorized['categories']['expenses']:
                categorized['categories']['expenses'][subcategory].append(entry_data)
            else:
                categorized['categories']['expenses']['other_expenses'].append(entry_data)
        
        processed_count += 1
    
    # Calculate totals with proper frequency handling
    def calculate_monthly_amount(amount: float, frequency: str) -> float:
        """Convert any frequency to monthly amount"""
        if frequency == 'monthly':
            return amount
        elif frequency == 'annually':
            return amount / 12
        elif frequency == 'quarterly':
            return amount / 3
        elif frequency == 'weekly':
            return amount * 4.33  # Average weeks per month
        else:  # one_time or other
            return 0  # Don't include one-time in monthly calculations
    
    # Calculate monthly income from all subcategories
    monthly_income = 0
    for subcategory, entries in categorized['categories']['income'].items():
        monthly_income += sum(calculate_monthly_amount(e['amount'], e['frequency']) for e in entries)
    
    # Calculate monthly expenses from all subcategories
    monthly_expenses = 0
    for subcategory, entries in categorized['categories']['expenses'].items():
        monthly_expenses += sum(calculate_monthly_amount(e['amount'], e['frequency']) for e in entries)
    
    # Calculate total assets from all subcategories
    total_assets = 0
    for subcategory, entries in categorized['categories']['assets'].items():
        total_assets += sum(e['amount'] for e in entries)
    
    # Calculate total liabilities from all subcategories
    total_liabilities = 0
    for subcategory, entries in categorized['categories']['liabilities'].items():
        total_liabilities += sum(e['amount'] for e in entries)
    
    totals = {
        'net_worth': total_assets - total_liabilities,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'monthly_cash_flow': monthly_income - monthly_expenses,
        'total_assets': total_assets,
        'total_liabilities': total_liabilities
    }
    
    # Calculate savings rate
    totals['savings_rate'] = (
        (totals['monthly_cash_flow'] / totals['monthly_income'] * 100) 
        if totals['monthly_income'] > 0 else 0
    )
    
    # Calculate counts for new structure
    asset_count = sum(len(entries) for entries in categorized['categories']['assets'].values())
    liability_count = sum(len(entries) for entries in categorized['categories']['liabilities'].values())
    income_count = sum(len(entries) for entries in categorized['categories']['income'].values())
    expense_count = sum(len(entries) for entries in categorized['categories']['expenses'].values())
    
    # Debug logging to see what we're returning
    print(f"🔍 API Response Summary:")
    print(f"  - Total entries processed: {processed_count}")
    print(f"  - Asset count: {asset_count}")
    print(f"  - Liability count: {liability_count}")
    print(f"  - Income count: {income_count}")
    print(f"  - Expense count: {expense_count}")
    print(f"  - Total assets value: ${totals['total_assets']}")
    print(f"  - Total liabilities value: ${totals['total_liabilities']}")
    
    return {
        'categories': categorized['categories'],
        'summary': totals,
        'counts': {
            'assets': asset_count,
            'liabilities': liability_count,
            'income': income_count,
            'expenses': expense_count,
            'total': len(entries)
        }
    }


@router.post("/entries", response_model=FinancialEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_financial_entry(
    entry_data: FinancialEntryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create new financial entry with automatic DQ scoring
    """
    # Determine data quality based on validation and source
    data_quality = DataQuality.DQ4  # Default for manual entries
    confidence_score = Decimal('1.00')
    
    # Enhanced validation for better DQ scoring
    if entry_data.amount and entry_data.description:
        # Check if description suggests automatic categorization
        desc_lower = entry_data.description.lower()
        high_confidence_keywords = ['bank', 'statement', 'official', 'verified']
        if any(keyword in desc_lower for keyword in high_confidence_keywords):
            data_quality = DataQuality.DQ3  # Verified manual entry
            confidence_score = Decimal('0.90')
    
    # Create the financial entry
    db_entry = FinancialEntry(
        user_id=current_user.id,
        category=entry_data.category,
        subcategory=entry_data.subcategory,
        description=entry_data.description,
        amount=entry_data.amount,
        currency=entry_data.currency,
        frequency=entry_data.frequency,
        entry_date=entry_data.entry_date or datetime.now(timezone.utc),
        data_quality=data_quality,
        confidence_score=confidence_score,
        source="manual",
        notes=entry_data.notes,
        is_active=True,
        is_recurring=entry_data.frequency != FrequencyType.one_time,
        # New 5-asset allocation system
        real_estate_percentage=entry_data.real_estate_percentage,
        stocks_percentage=entry_data.stocks_percentage,
        bonds_percentage=entry_data.bonds_percentage,
        cash_percentage=entry_data.cash_percentage,
        alternative_percentage=entry_data.alternative_percentage,
        # Enhanced Liability Fields
        interest_rate=entry_data.interest_rate,
        loan_term_months=entry_data.loan_term_months,
        remaining_months=entry_data.remaining_months,
        minimum_payment=entry_data.minimum_payment,
        is_fixed_rate=entry_data.is_fixed_rate,
        loan_start_date=entry_data.loan_start_date,
        original_amount=entry_data.original_amount,
        loan_details=entry_data.loan_details
    )
    
    # Calculate derived fields for liabilities with interest rates
    if db_entry.category == EntryCategory.liabilities and db_entry.interest_rate:
        # Calculate daily interest cost
        daily_rate = float(db_entry.interest_rate) / 100 / 365
        db_entry.daily_interest_cost = Decimal(str(float(db_entry.amount) * daily_rate))
        
        # Calculate total lifetime interest if we have monthly payment
        if db_entry.minimum_payment:
            try:
                payoff_calc = calculator.calculate_loan_payoff(
                    float(db_entry.amount),
                    float(db_entry.interest_rate),
                    float(db_entry.minimum_payment)
                )
                if 'total_interest' in payoff_calc:
                    db_entry.total_interest_lifetime = Decimal(str(payoff_calc['total_interest']))
                if 'months_to_payoff' in payoff_calc:
                    # Calculate payoff date
                    months_to_payoff = payoff_calc['months_to_payoff']
                    if months_to_payoff > 0:
                        from dateutil.relativedelta import relativedelta
                        payoff_date = datetime.now().date() + relativedelta(months=int(months_to_payoff))
                        db_entry.payoff_date = payoff_date
            except Exception as e:
                logger.warning(f"Could not calculate payoff details: {e}")
    
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    
    # Sync to vector DB
    await sync_to_vector_db(db_entry)
    db.commit()  # Save sync timestamp
    
    logger.info(
        "Financial entry created",
        user_id=current_user.id,
        entry_id=db_entry.id,
        category=entry_data.category.value,
        amount=float(entry_data.amount),
        data_quality=data_quality.value
    )
    
    return FinancialEntryResponse(
        id=str(db_entry.id),
        user_id=db_entry.user_id,
        category=db_entry.category,
        subcategory=db_entry.subcategory,
        description=db_entry.description,
        amount=db_entry.amount,
        currency=db_entry.currency,
        frequency=db_entry.frequency,
        entry_date=db_entry.entry_date,
        notes=db_entry.notes,
        data_quality=db_entry.data_quality,
        confidence_score=db_entry.confidence_score,
        source=db_entry.source,
        is_active=db_entry.is_active,
        is_recurring=db_entry.is_recurring,
        created_at=db_entry.created_at,
        updated_at=db_entry.updated_at,
        # Include allocation fields in response
        real_estate_percentage=db_entry.real_estate_percentage,
        stocks_percentage=db_entry.stocks_percentage,
        bonds_percentage=db_entry.bonds_percentage,
        cash_percentage=db_entry.cash_percentage,
        alternative_percentage=db_entry.alternative_percentage,
        # Include enhanced liability fields in response
        interest_rate=db_entry.interest_rate,
        loan_term_months=db_entry.loan_term_months,
        remaining_months=db_entry.remaining_months,
        minimum_payment=db_entry.minimum_payment,
        is_fixed_rate=db_entry.is_fixed_rate,
        loan_start_date=db_entry.loan_start_date,
        original_amount=db_entry.original_amount,
        loan_details=db_entry.loan_details
    )


@router.get("/entries/detailed")
async def get_detailed_entries(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Returns ALL entries with proper categorization for UI display
    """
    entries = db.query(FinancialEntry).filter(
        and_(FinancialEntry.user_id == current_user.id, FinancialEntry.is_active == True)
    ).all()
    
    # Group entries properly
    result = {
        'assets': {
            'real_estate': [],
            'retirement': [],
            'investments': [],
            'other': []
        },
        'liabilities': {
            'mortgage': [],
            'credit_cards': [],
            'loans': [],
            'other': []
        },
        'income': {
            'employment': [],
            'investment': [],
            'business': [],
            'other': []
        },
        'expenses': {
            'housing': [],
            'food': [],
            'transportation': [],
            'other': []
        }
    }
    
    # Calculate totals
    total_assets = 0
    total_liabilities = 0
    monthly_income = 0
    monthly_expenses = 0
    
    for entry in entries:
        data = {
            'id': entry.id,
            'description': entry.description,
            'amount': float(entry.amount),
            'category': entry.category.value,
            'frequency': entry.frequency.value if entry.frequency else 'one_time'
        }
        
        # Map to correct category based on description/category
        if entry.category.value == 'assets':
            total_assets += float(entry.amount)
            category_type = categorize_financial_entry('assets', entry.description, entry.subcategory)
            if category_type == 'real_estate':
                result['assets']['real_estate'].append(data)
            elif category_type == 'retirement':
                result['assets']['retirement'].append(data)
            elif category_type == 'investments':
                result['assets']['investments'].append(data)
            else:
                result['assets']['other'].append(data)
                
        elif entry.category.value == 'liabilities':
            total_liabilities += float(entry.amount)
            category_type = categorize_financial_entry('liabilities', entry.description, entry.subcategory)
            if category_type == 'mortgage':
                result['liabilities']['mortgage'].append(data)
            elif category_type == 'credit_cards':
                result['liabilities']['credit_cards'].append(data)
            elif category_type in ['auto_loans', 'student_loans', 'personal_loans']:
                result['liabilities']['loans'].append(data)
            else:
                result['liabilities']['other'].append(data)
            
        elif entry.category.value == 'income':
            # Convert to monthly for cash flow calculations
            if entry.frequency and entry.frequency.value == 'monthly':
                monthly_income += float(entry.amount)
            elif entry.frequency and entry.frequency.value == 'annually':
                monthly_income += float(entry.amount) / 12
                
            category_type = categorize_financial_entry('income', entry.description, entry.subcategory)
            if category_type == 'employment_income':
                result['income']['employment'].append(data)
            elif category_type == 'investment_income':
                result['income']['investment'].append(data)
            elif category_type == 'business_income':
                result['income']['business'].append(data)
            else:
                result['income']['other'].append(data)
                
        elif entry.category.value == 'expenses':
            # Convert to monthly for cash flow calculations
            if entry.frequency and entry.frequency.value == 'monthly':
                monthly_expenses += float(entry.amount)
            elif entry.frequency and entry.frequency.value == 'annually':
                monthly_expenses += float(entry.amount) / 12
            
            category_type = categorize_financial_entry('expenses', entry.description, entry.subcategory)
            if category_type == 'housing':
                result['expenses']['housing'].append(data)
            elif category_type == 'food':
                result['expenses']['food'].append(data)
            elif category_type == 'transportation':
                result['expenses']['transportation'].append(data)
            else:
                result['expenses']['other'].append(data)
    
    # Add summary to the result
    result['summary'] = {
        'total_assets': total_assets,
        'total_liabilities': total_liabilities,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'net_worth': total_assets - total_liabilities,
        'cash_flow': monthly_income - monthly_expenses,
        'savings_rate': (monthly_income - monthly_expenses) / monthly_income * 100 if monthly_income > 0 else 0
    }
    
    return result


@router.get("/categorized-summary", response_model=dict)
def get_categorized_financial_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get categorized financial summary for detailed display
    """
    entries = db.query(FinancialEntry).filter(
        and_(FinancialEntry.user_id == current_user.id, FinancialEntry.is_active == True)
    ).all()
    
    # Categorize entries
    categorized = {
        "assets": {
            "real_estate": [],
            "retirement": [],
            "investments": [],
            "cash": [],
            "business": [],
            "other": []
        },
        "liabilities": {
            "mortgage": [],
            "student_loans": [],
            "credit_cards": [],
            "auto_loans": [],
            "personal_loans": [],
            "other": []
        },
        "income": {
            "employment_income": [],
            "business_income": [],
            "investment_income": [],
            "other": []
        },
        "expenses": {
            "housing": [],
            "food": [],
            "transportation": [],
            "shopping": [],
            "healthcare": [],
            "entertainment": [],
            "other": []
        }
    }
    
    totals = {
        "assets": Decimal('0.00'),
        "liabilities": Decimal('0.00'),
        "income": Decimal('0.00'),
        "expenses": Decimal('0.00'),
        "net_worth": Decimal('0.00'),
        "monthly_income": Decimal('0.00'),
        "monthly_expenses": Decimal('0.00'),
        "monthly_cash_flow": Decimal('0.00'),
        "annual_savings_potential": Decimal('0.00'),
        "savings_rate": Decimal('0.00')
    }
    
    print(f"🔍 Processing {len(entries)} entries for categorized summary")
    
    for entry in entries:
        category_main = entry.category.value
        category_sub = categorize_financial_entry(category_main, entry.description, entry.subcategory)
        
        print(f"🔍 Entry: {entry.description} | Main: {category_main} | Sub: {category_sub}")
        
        entry_data = {
            "id": entry.id,
            "description": entry.description,
            "amount": float(entry.amount),
            "frequency": entry.frequency.value,
            "data_quality": entry.data_quality.value,
            "created_at": entry.created_at.isoformat(),
            # Include allocation fields for form editing
            "real_estate_percentage": entry.real_estate_percentage,
            "stocks_percentage": entry.stocks_percentage,
            "bonds_percentage": entry.bonds_percentage,
            "cash_percentage": entry.cash_percentage,
            "alternative_percentage": entry.alternative_percentage
        }
        
        if category_main == "assets":
            totals["assets"] += entry.amount
            # Map from categorize_financial_entry output to expected names
            if category_sub == "real_estate":
                categorized["assets"]["real_estate"].append(entry_data)
            elif category_sub == "retirement_accounts":
                categorized["assets"]["retirement"].append(entry_data)
            elif category_sub == "investment_accounts":
                categorized["assets"]["investments"].append(entry_data)
            elif category_sub == "cash_bank_accounts":
                categorized["assets"]["cash"].append(entry_data)
            elif category_sub == "business_assets":
                categorized["assets"]["business"].append(entry_data)
            else:
                categorized["assets"]["other"].append(entry_data)
                
        elif category_main == "liabilities":
            totals["liabilities"] += entry.amount
            if category_sub == "mortgage_real_estate":
                categorized["liabilities"]["mortgage"].append(entry_data)
            elif category_sub == "student_loans":
                categorized["liabilities"]["student_loans"].append(entry_data)
            elif category_sub == "credit_cards":
                categorized["liabilities"]["credit_cards"].append(entry_data)
            elif category_sub == "auto_loans":
                categorized["liabilities"]["auto_loans"].append(entry_data)
            elif category_sub == "personal_loans":
                categorized["liabilities"]["personal_loans"].append(entry_data)
            else:
                categorized["liabilities"]["other"].append(entry_data)
                
        elif category_main == "income":
            totals["income"] += entry.amount
            # Convert to monthly for cash flow
            if entry.frequency.value == "annually":
                totals["monthly_income"] += entry.amount / 12
            elif entry.frequency.value == "monthly":
                totals["monthly_income"] += entry.amount
            
            if category_sub == "employment_income":
                categorized["income"]["employment_income"].append(entry_data)
            elif category_sub == "business_income":
                categorized["income"]["business_income"].append(entry_data)
            elif category_sub == "investment_income":
                categorized["income"]["investment_income"].append(entry_data)
            else:
                categorized["income"]["other"].append(entry_data)
                
        elif category_main == "expenses":
            totals["expenses"] += entry.amount
            # Convert to monthly for cash flow
            if entry.frequency.value == "annually":
                totals["monthly_expenses"] += entry.amount / 12
            elif entry.frequency.value == "monthly":
                totals["monthly_expenses"] += entry.amount
            
            if category_sub == "housing":
                categorized["expenses"]["housing"].append(entry_data)
            elif category_sub == "food":
                categorized["expenses"]["food"].append(entry_data)
            elif category_sub == "transportation":
                categorized["expenses"]["transportation"].append(entry_data)
            elif category_sub == "shopping":
                categorized["expenses"]["shopping"].append(entry_data)
            elif category_sub == "healthcare":
                categorized["expenses"]["healthcare"].append(entry_data)
            elif category_sub == "entertainment":
                categorized["expenses"]["entertainment"].append(entry_data)
            else:
                categorized["expenses"]["other"].append(entry_data)
    
    # Calculate net worth (assets minus liabilities, excluding income and expenses)
    totals["net_worth"] = totals["assets"] - totals["liabilities"]
    
    # Calculate cash flow analysis
    totals["monthly_cash_flow"] = totals["monthly_income"] - totals["monthly_expenses"]
    totals["annual_savings_potential"] = totals["monthly_cash_flow"] * 12
    
    # Calculate savings rate
    if totals["monthly_income"] > 0:
        totals["savings_rate"] = (totals["monthly_cash_flow"] / totals["monthly_income"]) * 100
    else:
        totals["savings_rate"] = Decimal('0.00')
    
    return {
        "categories": categorized,
        "totals": {
            "assets": float(totals["assets"]),
            "liabilities": float(totals["liabilities"]),
            "income": float(totals["income"]),
            "expenses": float(totals["expenses"]),
            "net_worth": float(totals["net_worth"]),
            "monthly_income": float(totals["monthly_income"]),
            "monthly_expenses": float(totals["monthly_expenses"]),
            "monthly_cash_flow": float(totals["monthly_cash_flow"]),
            "annual_savings_potential": float(totals["annual_savings_potential"]),
            "savings_rate": float(totals["savings_rate"])
        }
    }


@router.get("/entries", response_model=List[FinancialEntryResponse])
def get_financial_entries(
    category: Optional[EntryCategory] = Query(None, description="Filter by category"),
    data_quality: Optional[DataQuality] = Query(None, description="Filter by data quality"),
    limit: int = Query(100, ge=1, le=1000, description="Limit number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get user financial entries with filtering and pagination
    """
    query = db.query(FinancialEntry).filter(
        and_(
            FinancialEntry.user_id == current_user.id,
            FinancialEntry.is_active == True
        )
    )
    
    # Apply filters
    if category:
        query = query.filter(FinancialEntry.category == category)
    if data_quality:
        query = query.filter(FinancialEntry.data_quality == data_quality)
    
    # Order by most recent first
    query = query.order_by(desc(FinancialEntry.entry_date))
    
    # Apply pagination
    entries = query.offset(offset).limit(limit).all()
    
    return [
        FinancialEntryResponse(
            id=str(entry.id),
            user_id=entry.user_id,
            category=entry.category,
            subcategory=entry.subcategory,
            description=entry.description,
            amount=float(entry.amount),  # Convert Decimal to float
            currency=entry.currency,
            frequency=entry.frequency,
            entry_date=entry.entry_date,
            notes=entry.notes,
            data_quality=entry.data_quality,
            confidence_score=entry.confidence_score,
            source=entry.source,
            is_active=entry.is_active,
            is_recurring=entry.is_recurring,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
            # Include allocation fields in response
            real_estate_percentage=entry.real_estate_percentage,
            stocks_percentage=entry.stocks_percentage,
            bonds_percentage=entry.bonds_percentage,
            cash_percentage=entry.cash_percentage,
            alternative_percentage=entry.alternative_percentage,
            # Include enhanced liability fields in response
            interest_rate=entry.interest_rate,
            loan_term_months=entry.loan_term_months,
            remaining_months=entry.remaining_months,
            minimum_payment=entry.minimum_payment,
            is_fixed_rate=entry.is_fixed_rate,
            loan_start_date=entry.loan_start_date,
            original_amount=entry.original_amount,
            loan_details=entry.loan_details
        ) for entry in entries
    ]


@router.put("/entries/{entry_id}", response_model=FinancialEntryResponse)
async def update_financial_entry(
    entry_id: int,
    entry_update: FinancialEntryUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update financial entry
    """
    print(f"🔍 UPDATE REQUEST: entry_id={entry_id}, user_id={current_user.id}")
    print(f"🔍 UPDATE DATA: {entry_update.model_dump()}")
    # Get existing entry
    db_entry = db.query(FinancialEntry).filter(
        and_(
            FinancialEntry.id == entry_id,
            FinancialEntry.user_id == current_user.id,
            FinancialEntry.is_active == True
        )
    ).first()
    
    if not db_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial entry not found"
        )
    
    # Update fields if provided
    update_data = entry_update.model_dump(exclude_unset=True)
    
    # Update all fields directly (allocation fields are now database columns)
    for field, value in update_data.items():
        setattr(db_entry, field, value)
        print(f"🔄 Setting {field} = {value}")
    
    # Recalculate derived fields if liability data changed
    if (db_entry.category == EntryCategory.liabilities and 
        any(field in update_data for field in ['interest_rate', 'amount', 'minimum_payment'])):
        
        if db_entry.interest_rate:
            # Recalculate daily interest cost
            daily_rate = float(db_entry.interest_rate) / 100 / 365
            db_entry.daily_interest_cost = Decimal(str(float(db_entry.amount) * daily_rate))
            
            # Recalculate total lifetime interest if we have monthly payment
            if db_entry.minimum_payment:
                try:
                    payoff_calc = calculator.calculate_loan_payoff(
                        float(db_entry.amount),
                        float(db_entry.interest_rate),
                        float(db_entry.minimum_payment)
                    )
                    if 'total_interest' in payoff_calc:
                        db_entry.total_interest_lifetime = Decimal(str(payoff_calc['total_interest']))
                    if 'months_to_payoff' in payoff_calc:
                        months_to_payoff = payoff_calc['months_to_payoff']
                        if months_to_payoff > 0:
                            from dateutil.relativedelta import relativedelta
                            payoff_date = datetime.now().date() + relativedelta(months=int(months_to_payoff))
                            db_entry.payoff_date = payoff_date
                except Exception as e:
                    logger.warning(f"Could not recalculate payoff details: {e}")
    
    # Update metadata
    db_entry.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(db_entry)
    
    # Sync to vector DB
    await sync_to_vector_db(db_entry)
    db.commit()  # Save sync timestamp
    
    # Debug: Check what was actually saved
    print(f"🔍 AFTER COMMIT: entry.details = {db_entry.details}")
    
    logger.info(
        "Financial entry updated", 
        user_id=current_user.id, 
        entry_id=entry_id,
        updated_fields=list(update_data.keys())
    )
    
    return FinancialEntryResponse(
        id=str(db_entry.id),
        user_id=db_entry.user_id,
        category=db_entry.category,
        subcategory=db_entry.subcategory,
        description=db_entry.description,
        amount=db_entry.amount,
        currency=db_entry.currency,
        frequency=db_entry.frequency,
        entry_date=db_entry.entry_date,
        notes=db_entry.notes,
        data_quality=db_entry.data_quality,
        confidence_score=db_entry.confidence_score,
        source=db_entry.source,
        is_active=db_entry.is_active,
        is_recurring=db_entry.is_recurring,
        created_at=db_entry.created_at,
        updated_at=db_entry.updated_at,
        # Include allocation fields in response
        real_estate_percentage=db_entry.real_estate_percentage,
        stocks_percentage=db_entry.stocks_percentage,
        bonds_percentage=db_entry.bonds_percentage,
        cash_percentage=db_entry.cash_percentage,
        alternative_percentage=db_entry.alternative_percentage,
        # Include enhanced liability fields in response
        interest_rate=db_entry.interest_rate,
        loan_term_months=db_entry.loan_term_months,
        remaining_months=db_entry.remaining_months,
        minimum_payment=db_entry.minimum_payment,
        is_fixed_rate=db_entry.is_fixed_rate,
        loan_start_date=db_entry.loan_start_date,
        original_amount=db_entry.original_amount,
        loan_details=db_entry.loan_details
    )


@router.delete("/entries/{entry_id}")
def delete_financial_entry(
    entry_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Soft delete financial entry (mark as inactive)
    """
    db_entry = db.query(FinancialEntry).filter(
        and_(
            FinancialEntry.id == entry_id,
            FinancialEntry.user_id == current_user.id,
            FinancialEntry.is_active == True
        )
    ).first()
    
    if not db_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial entry not found"
        )
    
    # Soft delete
    db_entry.is_active = False
    db_entry.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    
    logger.info("Financial entry deleted", user_id=current_user.id, entry_id=entry_id)
    return {"message": "Financial entry deleted successfully"}


@router.get("/accounts", response_model=List[FinancialAccountResponse])
def get_financial_accounts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get all connected financial accounts
    """
    accounts = db.query(FinancialAccount).filter(
        and_(
            FinancialAccount.user_id == current_user.id,
            FinancialAccount.is_active == True
        )
    ).order_by(FinancialAccount.created_at.desc()).all()
    
    return [
        FinancialAccountResponse(
            id=account.id,
            user_id=account.user_id,
            account_type=account.account_type,
            institution_name=account.institution_name,
            account_name=account.account_name,
            account_number_masked=account.account_number_masked,
            data_quality=account.data_quality,
            last_sync_at=account.last_sync_at,
            is_active=account.is_active,
            is_manual=account.is_manual,
            created_at=account.created_at
        ) for account in accounts
    ]


@router.get("/data-quality", response_model=dict)
def get_data_quality_breakdown(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get data quality breakdown by category and source
    """
    entries = db.query(FinancialEntry).filter(
        and_(
            FinancialEntry.user_id == current_user.id,
            FinancialEntry.is_active == True
        )
    ).all()
    
    # Count entries by data quality level
    dq_breakdown = {dq.value: 0 for dq in DataQuality}
    category_breakdown = {}
    source_breakdown = {}
    
    for entry in entries:
        dq_breakdown[entry.data_quality.value] += 1
        
        if entry.category.value not in category_breakdown:
            category_breakdown[entry.category.value] = {dq.value: 0 for dq in DataQuality}
        category_breakdown[entry.category.value][entry.data_quality.value] += 1
        
        if entry.source not in source_breakdown:
            source_breakdown[entry.source] = {dq.value: 0 for dq in DataQuality}
        source_breakdown[entry.source][entry.data_quality.value] += 1
    
    total_entries = len(entries)
    overall_score = calculate_data_quality_score(entries).value
    
    return {
        "overall_score": overall_score,
        "total_entries": total_entries,
        "data_quality_breakdown": dq_breakdown,
        "by_category": category_breakdown,
        "by_source": source_breakdown,
        "recommendations": [
            "Connect bank accounts for DQ1/DQ2 scoring" if dq_breakdown["DQ4"] > total_entries * 0.5 else None,
            "Verify manual entries for better accuracy" if dq_breakdown["DQ4"] > 20 else None,
            "Enable automatic sync for real-time updates" if dq_breakdown["DQ1"] < total_entries * 0.2 else None
        ]
    }


@router.get("/net-worth/history", response_model=List[NetWorthSnapshotSchema])
def get_net_worth_history(
    days: int = Query(30, ge=1, le=365, description="Number of days to retrieve"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get net worth history over time
    """
    from datetime import timedelta
    
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    snapshots = db.query(NetWorthSnapshot).filter(
        and_(
            NetWorthSnapshot.user_id == current_user.id,
            NetWorthSnapshot.snapshot_date >= cutoff_date
        )
    ).order_by(NetWorthSnapshot.snapshot_date.desc()).all()
    
    return [
        NetWorthSnapshotSchema(
            id=snapshot.id,
            user_id=snapshot.user_id,
            total_assets=snapshot.total_assets,
            total_liabilities=snapshot.total_liabilities,
            net_worth=snapshot.net_worth,
            liquid_assets=snapshot.liquid_assets,
            investment_assets=snapshot.investment_assets,
            real_estate_assets=snapshot.real_estate_assets,
            other_assets=snapshot.other_assets,
            confidence_score=snapshot.confidence_score,
            data_quality_score=DataQuality(snapshot.data_quality_score),
            snapshot_date=snapshot.snapshot_date
        ) for snapshot in snapshots
    ]


@router.post("/net-worth/snapshot")
def create_net_worth_snapshot(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new net worth snapshot based on current financial data
    """
    # Get all active entries
    entries = db.query(FinancialEntry).filter(
        and_(
            FinancialEntry.user_id == current_user.id,
            FinancialEntry.is_active == True
        )
    ).all()
    
    # Calculate totals by category
    assets = sum(e.amount for e in entries if e.category == EntryCategory.assets)
    liabilities = sum(e.amount for e in entries if e.category == EntryCategory.liabilities)
    net_worth = assets - liabilities
    
    # Calculate asset breakdown (simplified)
    liquid_assets = sum(
        e.amount for e in entries 
        if e.category == EntryCategory.assets and e.subcategory in ['checking', 'savings', 'cash']
    )
    investment_assets = sum(
        e.amount for e in entries 
        if e.category == EntryCategory.assets and e.subcategory in ['investment', 'retirement', 'stocks', 'bonds']
    )
    real_estate_assets = sum(
        e.amount for e in entries 
        if e.category == EntryCategory.assets and e.subcategory in ['real_estate', 'property']
    )
    other_assets = assets - liquid_assets - investment_assets - real_estate_assets
    
    # Calculate confidence score based on data quality
    total_amount = assets + liabilities
    weighted_confidence = sum(
        float(e.amount) * float(e.confidence_score) for e in entries
    )
    avg_confidence = Decimal(str(weighted_confidence / float(total_amount))) if total_amount > 0 else Decimal('1.00')
    
    # Create snapshot
    snapshot = NetWorthSnapshot(
        user_id=current_user.id,
        total_assets=assets,
        total_liabilities=liabilities,
        net_worth=net_worth,
        liquid_assets=liquid_assets,
        investment_assets=investment_assets,
        real_estate_assets=real_estate_assets,
        other_assets=other_assets,
        confidence_score=avg_confidence,
        data_quality_score=calculate_data_quality_score(entries).value,
        snapshot_date=datetime.now(timezone.utc)
    )
    
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    
    logger.info(
        "Net worth snapshot created",
        user_id=current_user.id,
        snapshot_id=snapshot.id,
        net_worth=float(net_worth),
        data_quality=snapshot.data_quality_score
    )
    
    return {
        "message": "Net worth snapshot created successfully",
        "snapshot_id": snapshot.id,
        "net_worth": snapshot.net_worth,
        "data_quality_score": snapshot.data_quality_score
    }


@router.get("/portfolio-allocation", response_model=dict)
def get_portfolio_allocation(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    SIMPLIFIED: Get portfolio allocation using user-provided allocation percentages.
    No complex classification - just simple math from user input.
    """
    # Get all active asset entries for the user
    entries = db.query(FinancialEntry).filter(
        and_(
            FinancialEntry.user_id == current_user.id,
            FinancialEntry.is_active == True,
            FinancialEntry.category == EntryCategory.assets
        )
    ).all()
    
    if not entries:
        return {
            "percentages": {},
            "amounts": {},
            "total": 0,
            "message": "No asset entries found"
        }
    
    # Simple calculation using allocation percentages
    total_stocks = 0
    total_bonds = 0
    total_real_estate = 0
    total_cash = 0
    total_alternative = 0
    
    for entry in entries:
        amount = float(entry.amount)
        
        # Use database columns directly (more reliable than JSONB)
        real_estate_pct = (entry.real_estate_percentage or 0) / 100
        stocks_pct = (entry.stocks_percentage or 0) / 100
        bonds_pct = (entry.bonds_percentage or 0) / 100
        cash_pct = (entry.cash_percentage or 0) / 100
        alternative_pct = (entry.alternative_percentage or 0) / 100
        
        # Calculate allocations
        entry_real_estate = amount * real_estate_pct
        entry_stocks = amount * stocks_pct
        entry_bonds = amount * bonds_pct
        entry_cash = amount * cash_pct
        entry_alternative = amount * alternative_pct
        
        print(f"🔍 PORTFOLIO: {entry.description} -> RE: {real_estate_pct:.1%}, Stocks: {stocks_pct:.1%}, Bonds: {bonds_pct:.1%}")
        
        total_real_estate += entry_real_estate
        total_stocks += entry_stocks
        total_bonds += entry_bonds
        total_cash += entry_cash
        total_alternative += entry_alternative
    
    # Calculate total and percentages
    total = total_stocks + total_bonds + total_real_estate + total_cash + total_alternative
    
    if total == 0:
        return {
            "percentages": {},
            "amounts": {},
            "total": 0,
            "message": "No allocation data found - entries need allocation percentages"
        }
    
    return {
        "percentages": {
            "stocks": round(total_stocks / total * 100, 1) if total > 0 else 0,
            "bonds": round(total_bonds / total * 100, 1) if total > 0 else 0,
            "real_estate": round(total_real_estate / total * 100, 1) if total > 0 else 0,
            "cash": round(total_cash / total * 100, 1) if total > 0 else 0,
            "alternative": round(total_alternative / total * 100, 1) if total > 0 else 0
        },
        "amounts": {
            "stocks": total_stocks,
            "bonds": total_bonds,
            "real_estate": total_real_estate,
            "cash": total_cash,
            "alternative": total_alternative
        },
        "total": total,
        "entry_count": len(entries),
        "message": "Portfolio allocation calculated successfully"
    }


@router.get("/debug/entries")
def debug_entries(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Debug endpoint to check what's in the database
    """
    entries = db.query(FinancialEntry).filter(
        and_(
            FinancialEntry.user_id == current_user.id,
            FinancialEntry.is_active == True
        )
    ).limit(5).all()
    
    result = []
    for entry in entries:
        result.append({
            "id": entry.id,
            "description": entry.description,
            "amount": float(entry.amount),
            "details": entry.details,
            "has_details_attr": hasattr(entry, 'details')
        })
    
    return {
        "entries": result,
        "count": len(entries)
    }


@router.post("/sync")
def trigger_data_sync(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Trigger manual data synchronization for connected accounts
    """
    # Get connected accounts
    accounts = db.query(FinancialAccount).filter(
        and_(
            FinancialAccount.user_id == current_user.id,
            FinancialAccount.is_active == True,
            FinancialAccount.is_manual == False  # Only sync non-manual accounts
        )
    ).all()
    
    sync_id = str(uuid.uuid4())
    
    # TODO: Implement actual data sync logic here
    # For now, just update last_sync_at timestamp
    for account in accounts:
        account.last_sync_at = datetime.now(timezone.utc)
    
    db.commit()
    
    logger.info(
        "Data sync triggered", 
        user_id=current_user.id,
        sync_id=sync_id,
        accounts_count=len(accounts)
    )
    
    return {
        "message": "Data synchronization started",
        "sync_id": sync_id,
        "accounts_to_sync": len(accounts),
        "estimated_completion": "2-5 minutes"
    }


# ============================================================================
# NEW CLEAN API ENDPOINTS FOR PHASE 1
# ============================================================================

@router.get("/entries/{user_id}", response_model=dict)
def get_all_financial_entries(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get ALL financial entries for a user - Clean API for rebuild
    Returns entries grouped by category with live calculations
    NO SNAPSHOTS, NO FALLBACKS, REAL DATA ONLY
    """
    # Verify user access
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to user data"
        )
    
    # Get ALL active entries
    entries = db.query(FinancialEntry).filter(
        and_(
            FinancialEntry.user_id == user_id,
            FinancialEntry.is_active == True
        )
    ).all()
    
    if not entries:
        # Return empty data structure instead of 404
        return {
            "user_id": user_id,
            "entries": {
                "assets": [],
                "liabilities": [],
                "income": [],
                "expenses": []
            },
            "summary": {
                "total_entries": 0,
                "total_assets": 0.0,
                "total_liabilities": 0.0,
                "net_worth": 0.0
            },
            "message": "No financial data found. Please add your financial information.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    # Group entries by category
    grouped_entries = {
        "assets": [],
        "liabilities": [],
        "income": [],
        "expenses": []
    }
    
    for entry in entries:
        entry_data = {
            "id": entry.id,
            "category": entry.category.value,
            "subcategory": entry.subcategory,
            "description": entry.description,
            "amount": float(entry.amount),
            "frequency": entry.frequency.value if entry.frequency else "one_time",
            "created_at": entry.created_at.isoformat() if entry.created_at else None
        }
        
        if entry.category == EntryCategory.assets:
            grouped_entries["assets"].append(entry_data)
        elif entry.category == EntryCategory.liabilities:
            grouped_entries["liabilities"].append(entry_data)
        elif entry.category == EntryCategory.income:
            grouped_entries["income"].append(entry_data)
        elif entry.category == EntryCategory.expenses:
            grouped_entries["expenses"].append(entry_data)
    
    return {
        "user_id": user_id,
        "entries": grouped_entries,
        "count": {
            "assets": len(grouped_entries["assets"]),
            "liabilities": len(grouped_entries["liabilities"]),
            "income": len(grouped_entries["income"]),
            "expenses": len(grouped_entries["expenses"]),
            "total": len(entries)
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/live-summary/{user_id}", response_model=dict)
def get_live_financial_summary(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Calculate LIVE net worth from actual entries
    NO SNAPSHOTS - Real calculations only
    Should return $5,966,409 for Debashish, not $2,565,545
    """
    # Verify user access
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to user data"
        )
    
    # Get all active entries
    entries = db.query(FinancialEntry).filter(
        and_(
            FinancialEntry.user_id == user_id,
            FinancialEntry.is_active == True
        )
    ).all()
    
    if not entries:
        # Return empty data structure instead of 404
        return {
            "user_id": user_id,
            "summary": {
                "total_assets": 0.0,
                "total_liabilities": 0.0,
                "net_worth": 0.0,
                "liquid_assets": 0.0,
                "investment_assets": 0.0,
                "retirement_assets": 0.0,
                "real_estate_assets": 0.0
            },
            "entries_count": 0,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "message": "No financial data found. Please add your financial information."
        }
    
    # Calculate totals from ACTUAL entries
    total_assets = sum(
        float(e.amount) for e in entries 
        if e.category == EntryCategory.assets
    )
    
    total_liabilities = sum(
        float(e.amount) for e in entries 
        if e.category == EntryCategory.liabilities
    )
    
    net_worth = total_assets - total_liabilities
    
    # Calculate asset breakdown
    liquid_assets = sum(
        float(e.amount) for e in entries 
        if e.category == EntryCategory.assets and 
        e.subcategory in ['cash', 'checking', 'savings', 'cash_savings', 'cash_bank_accounts']
    )
    
    investment_assets = sum(
        float(e.amount) for e in entries 
        if e.category == EntryCategory.assets and 
        e.subcategory in ['investment', 'stocks', 'bonds', 'crypto', 'retirement_accounts', 'investment_accounts', 'brokerage']
    )
    
    real_estate_assets = sum(
        float(e.amount) for e in entries 
        if e.category == EntryCategory.assets and 
        e.subcategory in ['real_estate', 'property', 'home']
    )
    
    return {
        "user_id": user_id,
        "net_worth": net_worth,
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "asset_breakdown": {
            "liquid": liquid_assets,
            "invested": investment_assets,
            "real_estate": real_estate_assets,
            "other": total_assets - liquid_assets - investment_assets - real_estate_assets
        },
        "calculation_time": datetime.now(timezone.utc).isoformat(),
        "data_source": "live_calculation",
        "entry_count": len(entries)
    }


@router.get("/cash-flow/{user_id}", response_model=dict)
def get_cash_flow_analysis(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Calculate monthly cash flow from income and expense entries
    Handles different frequencies (monthly, annual, etc)
    Should return $17,744 monthly income for Debashish
    """
    # Verify user access
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to user data"
        )
    
    # Get income and expense entries
    entries = db.query(FinancialEntry).filter(
        and_(
            FinancialEntry.user_id == user_id,
            FinancialEntry.is_active == True,
            FinancialEntry.category.in_([EntryCategory.income, EntryCategory.expenses])
        )
    ).all()
    
    def to_monthly(amount: float, frequency: str) -> float:
        """Convert any frequency to monthly amount"""
        if frequency == 'monthly':
            return amount
        elif frequency == 'annually' or frequency == 'annual':
            return amount / 12
        elif frequency == 'quarterly':
            return amount / 3
        elif frequency == 'weekly':
            return amount * 4.33
        elif frequency == 'bi_weekly':
            return amount * 2.17
        else:  # one_time or unknown
            return 0
    
    # Calculate monthly income
    monthly_income = sum(
        to_monthly(float(e.amount), e.frequency.value if e.frequency else 'one_time')
        for e in entries if e.category == EntryCategory.income
    )
    
    # Calculate monthly expenses
    monthly_expenses = sum(
        to_monthly(float(e.amount), e.frequency.value if e.frequency else 'one_time')
        for e in entries if e.category == EntryCategory.expenses
    )
    
    monthly_surplus = monthly_income - monthly_expenses
    savings_rate = (monthly_surplus / monthly_income * 100) if monthly_income > 0 else 0
    
    # Get detailed breakdown
    income_breakdown = {}
    expense_breakdown = {}
    
    for entry in entries:
        monthly_amt = to_monthly(float(entry.amount), entry.frequency.value if entry.frequency else 'one_time')
        
        if entry.category == EntryCategory.income:
            subcategory = entry.subcategory or 'other'
            if subcategory not in income_breakdown:
                income_breakdown[subcategory] = 0
            income_breakdown[subcategory] += monthly_amt
        
        elif entry.category == EntryCategory.expenses:
            subcategory = entry.subcategory or 'other'
            if subcategory not in expense_breakdown:
                expense_breakdown[subcategory] = 0
            expense_breakdown[subcategory] += monthly_amt
    
    return {
        "user_id": user_id,
        "monthly_income": monthly_income,
        "monthly_expenses": monthly_expenses,
        "monthly_surplus": monthly_surplus,
        "savings_rate": savings_rate,
        "annual_income": monthly_income * 12,
        "annual_expenses": monthly_expenses * 12,
        "annual_surplus": monthly_surplus * 12,
        "income_breakdown": income_breakdown,
        "expense_breakdown": expense_breakdown,
        "calculation_time": datetime.now(timezone.utc).isoformat()
    }


# ============================================================================
# FINANCIAL CALCULATOR ENDPOINTS
# ============================================================================

@router.post("/calculator/payoff")
async def calculate_payoff(
    balance: float,
    interest_rate: float,
    monthly_payment: float,
    current_user: User = Depends(get_current_active_user)
):
    """Calculate loan payoff timeline with specific numbers"""
    try:
        result = calculator.calculate_loan_payoff(balance, interest_rate, monthly_payment)
        
        logger.info(
            "Payoff calculation performed",
            user_id=current_user.id,
            balance=balance,
            rate=interest_rate,
            payment=monthly_payment,
            has_error="error" in result
        )
        
        return result
    except Exception as e:
        logger.error(f"Payoff calculation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Calculation error: {str(e)}"
        )


@router.post("/calculator/compare-strategies")
async def compare_strategies(
    balance: float,
    interest_rate: float,
    min_payment: float,
    target_payment: float,
    current_user: User = Depends(get_current_active_user)
):
    """Compare different payment strategies"""
    try:
        comparison = calculator.compare_payoff_strategies(
            balance, interest_rate, min_payment, target_payment
        )
        
        logger.info(
            "Payment strategy comparison performed",
            user_id=current_user.id,
            balance=balance,
            rate=interest_rate,
            min_payment=min_payment,
            target_payment=target_payment,
            has_error="error" in comparison
        )
        
        return comparison
    except Exception as e:
        logger.error(f"Strategy comparison failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Calculation error: {str(e)}"
        )


@router.post("/calculator/debt-avalanche")
async def calculate_debt_avalanche(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Calculate optimal debt payoff order using debt avalanche method"""
    try:
        # Get user's debt entries with interest rates
        debt_entries = db.query(FinancialEntry).filter(
            and_(
                FinancialEntry.user_id == current_user.id,
                FinancialEntry.category == EntryCategory.LIABILITIES,
                FinancialEntry.interest_rate.isnot(None),
                FinancialEntry.interest_rate > 0,
                FinancialEntry.is_active == True
            )
        ).all()
        
        if not debt_entries:
            return {
                "message": "No debts with interest rates found",
                "debt_count": 0,
                "strategy": []
            }
        
        # Convert to calculator format
        debts = []
        for entry in debt_entries:
            debts.append({
                'description': entry.description,
                'balance': float(entry.amount),
                'interest_rate': float(entry.interest_rate),
                'minimum_payment': float(entry.minimum_payment) if entry.minimum_payment else 0,
                'loan_term_months': entry.loan_term_months,
                'remaining_months': entry.remaining_months
            })
        
        strategy = calculator.calculate_debt_avalanche(debts)
        
        logger.info(
            "Debt avalanche calculation performed",
            user_id=current_user.id,
            debt_count=len(debts),
            total_debt=sum(d['balance'] for d in debts)
        )
        
        return {
            "user_id": current_user.id,
            "debt_count": len(debts),
            "total_debt_balance": sum(d['balance'] for d in debts),
            "strategy": strategy,
            "calculation_time": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Debt avalanche calculation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Calculation error: {str(e)}"
        )


@router.post("/calculator/mortgage-vs-invest")
async def calculate_mortgage_vs_invest(
    mortgage_balance: float,
    mortgage_rate: float,
    extra_payment: float,
    expected_return: float = 7.0,
    current_user: User = Depends(get_current_active_user)
):
    """Compare paying extra on mortgage vs investing the money"""
    try:
        comparison = calculator.calculate_mortgage_vs_invest(
            mortgage_balance, mortgage_rate, extra_payment, expected_return
        )
        
        logger.info(
            "Mortgage vs investment comparison performed",
            user_id=current_user.id,
            mortgage_balance=mortgage_balance,
            mortgage_rate=mortgage_rate,
            extra_payment=extra_payment,
            expected_return=expected_return,
            has_error="error" in comparison
        )
        
        return comparison
    except Exception as e:
        logger.error(f"Mortgage vs investment calculation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Calculation error: {str(e)}"
        )


@router.post("/calculator/emergency-fund")
async def calculate_emergency_fund(
    monthly_expenses: float,
    current_savings: float,
    income_stability: str = "stable",
    current_user: User = Depends(get_current_active_user)
):
    """Calculate emergency fund adequacy and recommendations"""
    try:
        if income_stability not in ["stable", "variable", "uncertain"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="income_stability must be 'stable', 'variable', or 'uncertain'"
            )
        
        analysis = calculator.calculate_emergency_fund_adequacy(
            monthly_expenses, current_savings, income_stability
        )
        
        logger.info(
            "Emergency fund analysis performed",
            user_id=current_user.id,
            monthly_expenses=monthly_expenses,
            current_savings=current_savings,
            income_stability=income_stability,
            status=analysis.get('status')
        )
        
        return analysis
    except Exception as e:
        logger.error(f"Emergency fund calculation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Calculation error: {str(e)}"
        )


@router.post("/calculator/retirement-projection")
async def calculate_retirement_projection(
    current_age: int,
    retirement_age: int,
    current_savings: float,
    monthly_contribution: float,
    expected_return: float = 7.0,
    current_user: User = Depends(get_current_active_user)
):
    """Project retirement savings growth"""
    try:
        projection = calculator.calculate_retirement_projection(
            current_age, retirement_age, current_savings, monthly_contribution, expected_return
        )
        
        logger.info(
            "Retirement projection performed",
            user_id=current_user.id,
            current_age=current_age,
            retirement_age=retirement_age,
            current_savings=current_savings,
            monthly_contribution=monthly_contribution,
            expected_return=expected_return,
            has_error="error" in projection
        )
        
        return projection
    except Exception as e:
        logger.error(f"Retirement projection calculation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Calculation error: {str(e)}"
        )


@router.get("/advisor/smart-context/{user_id}")
async def get_smart_context(
    user_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Get enhanced context with calculations for AI advisor"""
    try:
        # Ensure user can only access their own context or they're an admin
        if current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this user's context"
            )
        
        context = context_service.build_smart_context(user_id)
        
        logger.info(
            "Smart context generated",
            user_id=user_id,
            net_worth=context.get('net_worth', 0),
            debt_count=context.get('debt_count', 0),
            opportunities_count=len(context.get('opportunities', [])),
            has_error='error' in context
        )
        
        return context
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Smart context generation failed for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Context generation error: {str(e)}"
        )


@router.post("/sync/vector-db")
async def sync_vector_database(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Manually sync all financial data to vector DB"""
    
    try:
        # Get all user entries
        entries = db.query(FinancialEntry).filter(
            FinancialEntry.user_id == current_user.id,
            FinancialEntry.is_active == True
        ).all()
        
        # Sync all entries
        vector_db = get_vector_db()
        synced = await vector_db.sync_all_user_entries(current_user.id, entries)
        
        # Update sync timestamps
        for entry in entries:
            entry.last_synced_to_vector = datetime.now(timezone.utc)
        db.commit()
        
        logger.info(f"Manual vector sync completed for user {current_user.id}: {synced} entries")
        
        return {
            "status": "success",
            "entries_synced": synced,
            "total_entries": len(entries),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Manual vector sync failed for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


@router.post("/sync/complete")
async def complete_vector_sync(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Complete vector database refresh with current calculated values.
    Fixes stale data issues by clearing all vector entries and rebuilding with fresh calculations.
    """
    
    try:
        from app.services.complete_financial_context_service import CompleteFinancialContextService
        from app.services.financial_summary_service import financial_summary_service
        
        logger.info(f"Starting complete vector sync for user {current_user.id}")
        
        # Step 1: Get current correct calculations
        enhanced_service = CompleteFinancialContextService()
        smart_context = enhanced_service.build_smart_context(current_user.id)
        
        # Also get the financial summary for validation
        financial_summary = financial_summary_service.get_user_financial_summary(current_user.id, db)
        
        # Step 2: Clear ALL existing vector documents for this user
        from app.services.vector_db_service import get_vector_db
        vector_db_service = get_vector_db()
        
        # Get count before clearing
        try:
            # Try to query existing documents to count them
            existing_docs = vector_db_service.search_context(current_user.id, "financial")
            documents_removed = len(existing_docs) if existing_docs else 0
        except Exception:
            documents_removed = 0  # If we can't count, assume 0
        
        # Step 3: Get all user entries for rebuilding
        entries = db.query(FinancialEntry).filter(
            FinancialEntry.user_id == current_user.id,
            FinancialEntry.is_active == True
        ).all()
        
        # Step 4: Use comprehensive summary with profile data instead of individual entries
        from app.api.v1.endpoints.financial_clean import get_comprehensive_summary
        
        # Get comprehensive financial summary including all preferences
        comprehensive_summary = await get_comprehensive_summary(current_user.id, db, current_user)
        
        # Use the new method that includes profile data
        result = vector_db_service.index_comprehensive_summary_with_profile(current_user.id, comprehensive_summary, db)
        documents_indexed = result['documents_indexed']
        
        # Step 5: Profile data and comprehensive summary are now included via index_comprehensive_summary_with_profile
        # No need for additional manual context as the comprehensive method handles everything
        
        # Step 6: Update sync timestamps for all entries
        for entry in entries:
            entry.last_synced_to_vector = datetime.now(timezone.utc)
        
        db.commit()
        
        # Step 7: Validation - ensure correct DTI is now in vector DB
        validation_search = vector_db_service.search_context(current_user.id, "DTI debt-to-income ratio")
        dti_found_in_vector = False
        vector_dti_value = None
        
        if validation_search:
            for doc_result in validation_search[:3]:  # Check top 3 results
                doc_content = doc_result.get('content', '') if isinstance(doc_result, dict) else str(doc_result)
                if "debt-to-income ratio" in doc_content.lower() or "dti" in doc_content.lower():
                    # Try to extract DTI value from the document
                    import re
                    dti_match = re.search(r'debt-to-income ratio:\s*(\d+\.?\d*)%', doc_content.lower())
                    if dti_match:
                        vector_dti_value = float(dti_match.group(1))
                        dti_found_in_vector = True
                        break
        
        logger.info(f"Complete sync finished for user {current_user.id}: {documents_indexed} documents indexed")
        
        return {
            "status": "success",
            "documents_removed": documents_removed,
            "documents_indexed": documents_indexed,
            "metrics": {
                "dti_ratio": smart_context.get('debt_to_income_ratio', 0),
                "net_worth": smart_context.get('net_worth', 0),
                "total_assets": smart_context.get('total_assets', 0),
                "total_liabilities": smart_context.get('total_liabilities', 0),
                "monthly_surplus": smart_context.get('monthly_surplus', 0),
                "debt_count": smart_context.get('debt_count', 0),
                "high_interest_debt_count": len([d for d in smart_context.get('debt_strategy', []) if d.get('rate', 0) > 15])
            },
            "validation": {
                "dti_found_in_vector": dti_found_in_vector,
                "vector_dti_value": vector_dti_value,
                "expected_dti": smart_context.get('debt_to_income_ratio', 0)
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        import traceback
        logger.error(f"Complete vector sync failed for user {current_user.id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Complete sync failed: {str(e)}"
        )


@router.get("/sync/status")
async def get_sync_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Check if financial data needs syncing to vector DB"""
    
    try:
        # Find entries modified after last sync
        unsynced = db.query(FinancialEntry).filter(
            FinancialEntry.user_id == current_user.id,
            FinancialEntry.is_active == True,
            or_(
                FinancialEntry.last_synced_to_vector == None,
                FinancialEntry.updated_at > FinancialEntry.last_synced_to_vector
            )
        ).count()
        
        total_entries = db.query(FinancialEntry).filter(
            FinancialEntry.user_id == current_user.id,
            FinancialEntry.is_active == True
        ).count()
        
        return {
            "needs_sync": unsynced > 0,
            "unsynced_count": unsynced,
            "total_entries": total_entries,
            "sync_percentage": round((total_entries - unsynced) / total_entries * 100, 1) if total_entries > 0 else 100,
            "last_check": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Sync status check failed for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Status check failed: {str(e)}"
        )