"""
Financial Summary Service
Provides financial summary calculations without circular imports
Extracted from chat.py to avoid dependency issues
"""
from typing import Dict
from sqlalchemy.orm import Session
from decimal import Decimal
import logging
from ..models.financial import FinancialEntry, EntryCategory, FrequencyType

logger = logging.getLogger(__name__)


class FinancialSummaryService:
    """Service for calculating user financial summaries"""
    
    def get_user_financial_summary(self, user_id: int, db: Session) -> Dict:
        """
        Get user financial summary for context building (without FastAPI dependencies)
        This is the same calculation as in chat.py but without circular imports
        """
        try:
            logger.info(f"Calculating financial summary for user {user_id}")
            
            # Get ALL financial entries for live calculations
            entries = db.query(FinancialEntry).filter(
                FinancialEntry.user_id == user_id,
                FinancialEntry.is_active == True
            ).all()
            
            if not entries:
                logger.warning(f"No financial entries found for user {user_id}")
                return {}
            
            # Calculate live financial data
            assets_by_category = {}
            liabilities = []
            monthly_income = Decimal('0')
            monthly_expenses = Decimal('0')
            
            for entry in entries:
                if entry.category == EntryCategory.assets:
                    subcategory = entry.subcategory or ('real_estate' if float(entry.amount) > 100000 else 'other_assets')
                    if subcategory not in assets_by_category:
                        assets_by_category[subcategory] = []
                    assets_by_category[subcategory].append({
                        "name": entry.description,
                        "value": float(entry.amount),
                        "subcategory": subcategory
                    })
                elif entry.category == EntryCategory.liabilities:
                    liability_data = {
                        "name": entry.description,
                        "balance": float(entry.amount),
                        "subcategory": entry.subcategory or 'other_debt',
                        "type": entry.subcategory or 'debt'
                    }
                    
                    # Add enhanced liability details if available
                    if entry.interest_rate is not None:
                        liability_data["interest_rate"] = float(entry.interest_rate)
                    if entry.minimum_payment is not None:
                        liability_data["minimum_payment"] = float(entry.minimum_payment)
                    
                    liabilities.append(liability_data)
                elif entry.category == EntryCategory.income:
                    # FIXED: Include ALL income entries (Salary + RSU + 401K + Rental)
                    # This matches the corrected categorized API logic
                    if entry.frequency == FrequencyType.monthly:
                        monthly_income += entry.amount
                    elif entry.frequency == FrequencyType.annually:
                        monthly_income += entry.amount / 12
                    elif entry.frequency == FrequencyType.weekly:
                        monthly_income += entry.amount * 52 / 12
                elif entry.category == EntryCategory.expenses:
                    if entry.frequency == FrequencyType.monthly:
                        monthly_expenses += entry.amount
                    elif entry.frequency == FrequencyType.annually:
                        monthly_expenses += entry.amount / 12
                    elif entry.frequency == FrequencyType.weekly:
                        monthly_expenses += entry.amount * 52 / 12
            
            # NET WORTH CALCULATION
            # =====================
            # Standard Formula: total_assets - total_liabilities
            # Assets include: real_estate + retirement + investments + cash + other_assets
            # Liabilities include: mortgages + loans + credit_cards + other_debt
            # Note: All user-specific values pulled from database
            total_assets = sum(asset['value'] for category in assets_by_category.values() for asset in category)
            total_liabilities = sum(liability['balance'] for liability in liabilities)
            net_worth = total_assets - total_liabilities
            
            # CASH FLOW & SAVINGS RATE CALCULATION
            # ====================================
            # Monthly Surplus = total_monthly_income - total_monthly_expenses
            # Savings Rate = (monthly_surplus / total_monthly_income) * 100
            # Income sources: employment + rental + investment_income + other
            # Expense categories: all tracked monthly expenses
            # Note: Calculations are user-specific from financial_entries table
            monthly_surplus = float(monthly_income - monthly_expenses)
            savings_rate = (monthly_surplus / float(monthly_income)) * 100 if monthly_income > 0 else 0
            
            # Log calculated values for verification
            logger.debug(f"User {user_id}: Net Worth=${net_worth:,.0f}, Monthly Surplus=${monthly_surplus:,.0f}, Savings Rate={savings_rate:.1f}%")
            
            # Calculate monthly debt payments
            monthly_debt_payments = self._calculate_monthly_debt_payments(entries, user_id)
            
            # Calculate debt-to-income ratio
            debt_to_income_ratio = (monthly_debt_payments / float(monthly_income)) * 100 if monthly_income > 0 else 0
            
            # Build summary
            summary = {
                'netWorth': float(net_worth),
                'totalAssets': float(total_assets),
                'totalLiabilities': float(total_liabilities),
                'monthlyIncome': float(monthly_income),
                'monthlyExpenses': float(monthly_expenses),
                'monthlySurplus': monthly_surplus,
                'monthlyDebtPayments': monthly_debt_payments,
                'debtToIncomeRatio': debt_to_income_ratio,
                'savingsRate': savings_rate,
                'assetsBreakdown': assets_by_category,
                'liabilitiesBreakdown': liabilities
            }
            
            logger.info(f"Financial summary calculated: Net Worth=${net_worth:,.0f}, DTI={debt_to_income_ratio:.1f}%")
            return summary
            
        except Exception as e:
            logger.error(f"Error calculating financial summary for user {user_id}: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_monthly_debt_payments(self, entries, user_id: int) -> float:
        """Calculate monthly debt payments properly for all users"""
        monthly_debt_total = Decimal('0')
        
        # Method 1: Use minimum_payment from liability entries
        liabilities = [e for e in entries if e.category == EntryCategory.liabilities]
        
        # Group by balance to avoid duplicates, keep the one with highest minimum payment
        unique_liabilities = {}
        for liability in liabilities:
            balance_key = float(liability.amount)
            if balance_key not in unique_liabilities:
                unique_liabilities[balance_key] = liability
            else:
                # Keep the one with higher minimum payment
                existing = unique_liabilities[balance_key]
                if (liability.minimum_payment or 0) > (existing.minimum_payment or 0):
                    unique_liabilities[balance_key] = liability
        
        for liability in unique_liabilities.values():
            if liability.minimum_payment and liability.minimum_payment > 0:
                frequency = liability.frequency if liability.frequency else FrequencyType.monthly
                amount = Decimal(str(liability.minimum_payment))
                
                # Convert to monthly - treat 'one_time' as monthly for minimum payments
                if frequency in [FrequencyType.monthly, FrequencyType.one_time]:
                    monthly_debt_total += amount
                elif frequency == FrequencyType.annually:
                    monthly_debt_total += amount / 12
                elif frequency == FrequencyType.quarterly:
                    monthly_debt_total += amount / 3
                elif frequency == FrequencyType.weekly:
                    monthly_debt_total += amount * Decimal('4.33')  # Average weeks per month
                elif frequency == FrequencyType.daily:
                    monthly_debt_total += amount * 30
        
        # Method 2: If no minimum payments, look for debt payment expenses
        if monthly_debt_total == 0:
            expenses = [e for e in entries if e.category == EntryCategory.expenses]
            debt_payment_keywords = [
                'mortgage', 'home loan', 'credit card', 'loan payment', 
                'car payment', 'student loan', 'debt payment', 'installment'
            ]
            
            for expense in expenses:
                expense_desc_lower = expense.description.lower()
                if any(keyword in expense_desc_lower for keyword in debt_payment_keywords):
                    frequency = expense.frequency if expense.frequency else FrequencyType.monthly
                    amount = Decimal(str(expense.amount))
                    
                    # Convert to monthly
                    if frequency == FrequencyType.monthly:
                        monthly_debt_total += amount
                    elif frequency == FrequencyType.annually:
                        monthly_debt_total += amount / 12
                    elif frequency == FrequencyType.quarterly:
                        monthly_debt_total += amount / 3
                    elif frequency == FrequencyType.weekly:
                        monthly_debt_total += amount * Decimal('4.33')
                    elif frequency == FrequencyType.daily:
                        monthly_debt_total += amount * 30
        
        logger.info(f"Calculated monthly debt payments for user {user_id}: ${monthly_debt_total}")
        return float(monthly_debt_total)


# Global instance
financial_summary_service = FinancialSummaryService()