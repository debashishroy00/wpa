"""
WealthPath AI - Enhanced Context Service
Builds intelligent context with calculations for AI advisor responses
"""
from typing import Dict, List, Optional
import logging
import asyncio
from .financial_calculator import FinancialCalculator
from ..models.financial import FinancialEntry, EntryCategory
from ..models.goals_v2 import Goal, GoalProgress
from sqlalchemy.orm import Session
from ..db.session import SessionLocal, get_db
from datetime import datetime

logger = logging.getLogger(__name__)


class EnhancedContextService:
    """Service for building smart financial context with calculations"""
    
    def __init__(self):
        self.calculator = FinancialCalculator()
    
    def _get_correct_financial_summary(self, user_id: int, db: Session) -> Dict:
        """
        Get the correct financial summary using the same calculation as frontend
        This matches the frontend's displayed values
        """
        from .financial_summary_service import financial_summary_service
        
        try:
            # Use the financial summary service (no circular imports)
            summary = financial_summary_service.get_user_financial_summary(user_id, db)
            
            # Log the correct values
            logger.info(f"Correct financial summary for user {user_id}:")
            logger.info(f"  Net Worth: ${summary.get('netWorth', 0):,.0f}")
            logger.info(f"  Total Assets: ${summary.get('totalAssets', 0):,.0f}")
            logger.info(f"  Total Liabilities: ${summary.get('totalLiabilities', 0):,.0f}")
            logger.info(f"  DTI Ratio: {summary.get('debtToIncomeRatio', 'NOT_FOUND')}%")
            
            return summary
        except Exception as e:
            logger.error(f"Error getting financial summary: {str(e)}")
            # Fallback to basic calculation if needed
            return {}
    
    def _get_user_goals(self, user_id: int, db: Session) -> List[Dict]:
        """Get user's financial goals with progress calculations"""
        try:
            # Get active goals
            goals = db.query(Goal).filter(
                Goal.user_id == user_id,
                Goal.status == 'active'
            ).all()
            
            goal_data = []
            for goal in goals:
                # Get latest progress
                latest_progress = db.query(GoalProgress).filter(
                    GoalProgress.goal_id == goal.goal_id
                ).order_by(GoalProgress.recorded_at.desc()).first()
                
                current_amount = latest_progress.current_amount if latest_progress else 0
                progress_percent = (current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
                
                # Calculate months to target
                today = datetime.now().date()
                months_remaining = ((goal.target_date.year - today.year) * 12 + 
                                  (goal.target_date.month - today.month))
                
                goal_data.append({
                    "name": goal.name,
                    "category": goal.category,
                    "target_amount": float(goal.target_amount),
                    "current_amount": float(current_amount),
                    "progress_percent": round(progress_percent, 1),
                    "target_date": goal.target_date.strftime("%B %Y"),
                    "months_remaining": months_remaining,
                    "priority": goal.priority
                })
            
            return goal_data
            
        except Exception as e:
            logger.error(f"Error getting goals for user {user_id}: {str(e)}")
            return []
    
    
    def build_smart_context(self, user_id: int) -> Dict:
        """
        Build enriched context with calculations and specific insights
        
        Args:
            user_id: User ID to build context for
            
        Returns:
            Dictionary with comprehensive financial context and calculations
        """
        db = SessionLocal()
        try:
                # Get the correct financial summary (same as frontend)
                summary = self._get_correct_financial_summary(user_id, db)
                
                # Use the correct values from the summary
                net_worth = summary.get('netWorth', 0)
                total_assets = summary.get('totalAssets', 0)
                total_liabilities = summary.get('totalLiabilities', 0)
                monthly_income = summary.get('monthlyIncome', 0)
                monthly_expenses = summary.get('monthlyExpenses', 0)
                monthly_surplus = summary.get('monthlySurplus', 0)
                debt_to_income_ratio = summary.get('debtToIncomeRatio', 0)
                monthly_debt_payments = summary.get('monthlyDebtPayments', 0)
                
                # Log for debugging
                logger.info(f"Building smart context for user {user_id}")
                logger.info(f"Using correct values - Net Worth: ${net_worth:,.0f}")
                
                # Get individual entries for detailed analysis - ONLY ACTIVE ENTRIES
                entries = db.query(FinancialEntry).filter(
                    FinancialEntry.user_id == user_id,
                    FinancialEntry.is_active == True
                ).all()
                
                # Get user's financial goals
                goals = self._get_user_goals(user_id, db)
                
                # Categorize entries for detailed analysis (entries are already filtered for is_active = True)
                assets = [e for e in entries if e.category == EntryCategory.assets]
                liabilities = [e for e in entries if e.category == EntryCategory.liabilities]
                
                # Use the calculated values from the summary (these are already correct)
                
                # Extract debt information with interest rates
                debt_details = self._extract_debt_details(liabilities)
                
                # Calculate debt strategy if debts exist
                debt_strategy = []
                if debt_details:
                    debt_strategy = self.calculator.calculate_debt_avalanche(debt_details)
                
                # Find cash/emergency fund
                emergency_fund = self._calculate_emergency_fund(assets)
                emergency_analysis = self.calculator.calculate_emergency_fund_adequacy(
                    monthly_expenses, emergency_fund, "stable"
                )
                
                # Identify optimization opportunities
                opportunities = self._identify_opportunities(
                    debt_strategy, monthly_surplus, emergency_analysis, assets, liabilities
                )
                
                # Build specific rate context
                rate_context = self._build_rate_context(debt_details)
                
                # Get retirement analysis for context
                retirement_context = self._get_retirement_context(user_id, db)
                
                # Build final context with correct values
                context_result = {
                    "user_id": user_id,
                    "net_worth": round(net_worth, 2),
                    "total_assets": round(total_assets, 2),
                    "total_liabilities": round(total_liabilities, 2),
                    "monthly_income": round(monthly_income, 2),
                    "monthly_expenses": round(monthly_expenses, 2),
                    "monthly_surplus": round(monthly_surplus, 2),
                    "monthly_debt_payments": round(monthly_debt_payments, 2),
                    "debt_to_income_ratio": round(debt_to_income_ratio, 2),
                    "emergency_fund": round(emergency_fund, 2),
                    "emergency_analysis": emergency_analysis,
                    "debt_count": len(debt_details),
                    "debt_strategy": debt_strategy,
                    "opportunities": opportunities,
                    "rate_context": rate_context,
                    "portfolio_breakdown": self._analyze_portfolio(assets),
                    "cash_flow_status": self._analyze_cash_flow(monthly_surplus, monthly_income),
                    "goals": goals,
                    "retirement_context": retirement_context
                }
                
                logger.info(f"Smart context built successfully for user {user_id}: Net Worth=${net_worth:,.0f}")
                
                return context_result
                
        except Exception as e:
            import traceback
            logger.error(f"Error building smart context for user {user_id}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "error": f"Unable to build context: {str(e)}",
                "user_id": user_id,
                "fallback": True
            }
        finally:
            db.close()
    
    def _calculate_monthly_total(self, entries: List[FinancialEntry]) -> float:
        """Convert all entries to monthly amounts"""
        total = 0
        for entry in entries:
            amount = float(entry.amount)
            frequency = entry.frequency.value if entry.frequency else 'one_time'
            
            # Convert to monthly
            if frequency == 'monthly':
                total += amount
            elif frequency == 'annually':
                total += amount / 12
            elif frequency == 'quarterly':
                total += amount / 3
            elif frequency == 'weekly':
                total += amount * 4.33  # Average weeks per month
            elif frequency == 'daily':
                total += amount * 30
            # one_time entries are not included in monthly calculations
            
        return total
    
    def _calculate_monthly_debt_payments(self, entries: List[FinancialEntry], user_id: int) -> float:
        """Calculate monthly debt payments properly for all users"""
        from decimal import Decimal
        
        monthly_debt_total = Decimal('0')
        
        # Method 1: Use minimum_payment from liability entries
        liabilities = [e for e in entries if e.category.value == 'liabilities']
        
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
                frequency = liability.frequency.value if liability.frequency else 'monthly'
                amount = Decimal(str(liability.minimum_payment))
                
                # Convert to monthly - treat 'one_time' as monthly for minimum payments
                if frequency in ['monthly', 'one_time']:
                    monthly_debt_total += amount
                elif frequency == 'annually':
                    monthly_debt_total += amount / 12
                elif frequency == 'quarterly':
                    monthly_debt_total += amount / 3
                elif frequency == 'weekly':
                    monthly_debt_total += amount * Decimal('4.33')  # Average weeks per month
                elif frequency == 'daily':
                    monthly_debt_total += amount * 30
        
        # Method 2: If no minimum payments, look for debt payment expenses
        if monthly_debt_total == 0:
            expenses = [e for e in entries if e.category.value == 'expenses']
            debt_payment_keywords = [
                'mortgage', 'home loan', 'credit card', 'loan payment', 
                'car payment', 'student loan', 'debt payment', 'installment'
            ]
            
            for expense in expenses:
                expense_desc_lower = expense.description.lower()
                if any(keyword in expense_desc_lower for keyword in debt_payment_keywords):
                    frequency = expense.frequency.value if expense.frequency else 'monthly'
                    amount = Decimal(str(expense.amount))
                    
                    # Convert to monthly
                    if frequency == 'monthly':
                        monthly_debt_total += amount
                    elif frequency == 'annually':
                        monthly_debt_total += amount / 12
                    elif frequency == 'quarterly':
                        monthly_debt_total += amount / 3
                    elif frequency == 'weekly':
                        monthly_debt_total += amount * Decimal('4.33')
                    elif frequency == 'daily':
                        monthly_debt_total += amount * 30
        
        logger.info(f"Calculated monthly debt payments for user {user_id}: ${monthly_debt_total}")
        return float(monthly_debt_total)
    
    def _extract_debt_details(self, liabilities: List[FinancialEntry]) -> List[Dict]:
        """Extract debt details with interest rates for calculations"""
        debt_details = []
        
        for liability in liabilities:
            # Only include debts with interest rates for calculation
            if liability.interest_rate and liability.interest_rate > 0:
                debt_info = {
                    'description': liability.description,
                    'balance': float(liability.amount),
                    'interest_rate': float(liability.interest_rate),
                    'minimum_payment': float(liability.minimum_payment) if liability.minimum_payment else 0,
                    'loan_term_months': liability.loan_term_months,
                    'remaining_months': liability.remaining_months,
                    'is_fixed_rate': liability.is_fixed_rate,
                    'loan_start_date': liability.loan_start_date.isoformat() if liability.loan_start_date else None
                }
                debt_details.append(debt_info)
        
        return debt_details
    
    def _calculate_emergency_fund(self, assets: List[FinancialEntry]) -> float:
        """Calculate liquid emergency fund from cash assets"""
        emergency_fund = 0
        
        cash_keywords = ['checking', 'savings', 'money market', 'cash', 'emergency']
        
        for asset in assets:
            description_lower = asset.description.lower()
            
            # Look for cash accounts
            if any(keyword in description_lower for keyword in cash_keywords):
                # Check if this is actually 100% cash (not invested)
                if (asset.cash_percentage == 100 or 
                    (not asset.cash_percentage and 'cash' in description_lower)):
                    emergency_fund += float(asset.amount)
        
        return emergency_fund
    
    def _identify_opportunities(self, debt_strategy: List, monthly_surplus: float,
                              emergency_analysis: Dict, assets: List, liabilities: List) -> List[Dict]:
        """Identify specific financial optimization opportunities"""
        opportunities = []
        
        # 1. High-interest debt payoff opportunity
        if debt_strategy and debt_strategy[0]['rate'] > 15:
            debt = debt_strategy[0]
            extra_payment = min(monthly_surplus * 0.5, 1000)  # Up to 50% of surplus or $1000
            
            if extra_payment > 50:  # Only suggest if meaningful amount
                try:
                    current_payment = debt.get('minimum_payment', debt['balance'] * debt['rate'] / 100 / 12)
                    comparison = self.calculator.compare_payoff_strategies(
                        debt['balance'], debt['rate'], current_payment, current_payment + extra_payment
                    )
                    
                    # Check if calculator returned an error
                    if 'error' in comparison:
                        logger.warning(f"Calculator error for debt opportunity: {comparison['error']}")
                        # Skip this opportunity and continue with fallback
                        pass
                    else:
                        opportunities.append({
                            "type": "high_interest_debt",
                            "priority": "CRITICAL",
                            "action": f"Pay extra ${extra_payment:,.0f}/month on {debt['name']}",
                            "impact": f"Save ${comparison.get('interest_saved', 0):,.0f} in interest",
                            "timeline": f"Pay off {comparison.get('months_saved', 0):.1f} months earlier",
                            "specific_calculation": comparison,
                            "current_cost": f"${debt['daily_interest_cost']:.2f}/day in interest"
                        })
                except Exception as calc_error:
                    logger.warning(f"Error calculating debt opportunity: {str(calc_error)}")
                    # Add simplified opportunity without calculator
                    opportunities.append({
                        "type": "high_interest_debt",
                        "priority": "CRITICAL",
                        "action": f"Pay extra ${extra_payment:,.0f}/month on {debt['name']}",
                        "impact": f"Save significant interest (rate: {debt['rate']:.2f}%)",
                        "timeline": "Accelerated payoff",
                        "current_cost": f"${debt['daily_interest_cost']:.2f}/day in interest"
                    })
        
        # 2. Emergency fund gap
        if emergency_analysis['status'] in ['INSUFFICIENT', 'PARTIAL']:
            monthly_needed = emergency_analysis.get('monthly_gap', 0)
            if monthly_needed > 0 and monthly_surplus > monthly_needed:
                opportunities.append({
                    "type": "emergency_fund",
                    "priority": "HIGH" if emergency_analysis['status'] == 'INSUFFICIENT' else "MEDIUM",
                    "action": f"Add ${monthly_needed:,.0f}/month to emergency fund",
                    "impact": f"Reach {emergency_analysis['recommended_months']} months coverage",
                    "timeline": f"Complete in {emergency_analysis['shortfall'] / monthly_needed:.0f} months",
                    "current_gap": f"${emergency_analysis['shortfall']:,.0f} shortfall"
                })
        
        # 3. Investment rebalancing opportunity
        total_assets = sum(float(a.amount) for a in assets)
        if total_assets > 100000:  # Only for substantial portfolios
            investment_accounts = [a for a in assets if 'investment' in a.description.lower() or 
                                 'brokerage' in a.description.lower()]
            if investment_accounts:
                # Check for concentrated positions or poor allocation
                for account in investment_accounts:
                    if (account.stocks_percentage and account.stocks_percentage > 80 and 
                        float(account.amount) > 50000):
                        opportunities.append({
                            "type": "portfolio_rebalancing",
                            "priority": "MEDIUM",
                            "action": f"Rebalance {account.description} - reduce stock concentration",
                            "impact": "Reduce portfolio risk through diversification",
                            "current_allocation": f"{account.stocks_percentage}% stocks",
                            "recommended_action": "Consider 60-70% stocks, 20-30% bonds"
                        })
        
        # 4. Mortgage vs investment opportunity
        mortgage_debts = [d for d in debt_strategy if 'mortgage' in d['name'].lower()]
        if mortgage_debts and monthly_surplus > 1000:
            mortgage = mortgage_debts[0]
            if mortgage['rate'] < 5:  # Low rate mortgage
                extra_amount = min(monthly_surplus * 0.3, 2000)
                try:
                    comparison = self.calculator.calculate_mortgage_vs_invest(
                        mortgage['balance'], mortgage['rate'], extra_amount
                    )
                    
                    # Only add if calculation succeeded and recommendation is to invest
                    if 'error' not in comparison and comparison.get('recommendation') == 'Invest':
                        opportunities.append({
                            "type": "mortgage_vs_invest",
                            "priority": "MEDIUM",
                            "action": f"Invest ${extra_amount:,.0f}/month instead of extra mortgage payments",
                            "impact": f"Potential ${comparison.get('advantage_amount', 0):,.0f} advantage",
                            "mortgage_rate": f"{mortgage['rate']}%",
                            "investment_assumption": "7% annual return",
                            "risk_note": comparison.get('risk_consideration', '')
                        })
                except Exception as calc_error:
                    logger.warning(f"Error calculating mortgage vs investment opportunity: {str(calc_error)}")
                    # Skip this opportunity - don't add anything
        
        return opportunities
    
    def _build_rate_context(self, debt_details: List[Dict]) -> Dict:
        """Build context about interest rates for smarter responses"""
        if not debt_details:
            return {
                "has_debt": False,
                "debt_count": 0
            }
        
        rates = [d['interest_rate'] for d in debt_details]
        
        # Find specific debt types
        mortgage_rate = None
        credit_card_rates = []
        auto_loan_rates = []
        
        for debt in debt_details:
            desc_lower = debt['description'].lower()
            if 'mortgage' in desc_lower or 'home' in desc_lower:
                mortgage_rate = debt['interest_rate']
            elif 'credit' in desc_lower or 'card' in desc_lower:
                credit_card_rates.append(debt['interest_rate'])
            elif 'auto' in desc_lower or 'car' in desc_lower:
                auto_loan_rates.append(debt['interest_rate'])
        
        return {
            "has_debt": True,
            "debt_count": len(debt_details),
            "highest_rate": max(rates),
            "lowest_rate": min(rates),
            "average_rate": sum(rates) / len(rates),
            "mortgage_rate": mortgage_rate,
            "credit_card_rates": credit_card_rates,
            "auto_loan_rates": auto_loan_rates,
            "high_interest_debt_count": len([r for r in rates if r > 15]),
            "total_high_interest_balance": sum(d['balance'] for d in debt_details if d['interest_rate'] > 15)
        }
    
    def _analyze_portfolio(self, assets: List[FinancialEntry]) -> Dict:
        """Analyze portfolio allocation and concentration"""
        
        total_assets = sum(float(a.amount) for a in assets)
        
        if total_assets == 0:
            return {"total_assets": 0}
        
        # Aggregate allocations
        total_stocks = 0
        total_bonds = 0
        total_real_estate = 0
        total_cash = 0
        total_alternative = 0
        
        for asset in assets:
            amount = float(asset.amount)
            
            # Handle NULL values properly - convert None to 0
            stocks_pct = asset.stocks_percentage if asset.stocks_percentage is not None else 0
            bonds_pct = asset.bonds_percentage if asset.bonds_percentage is not None else 0
            real_estate_pct = asset.real_estate_percentage if asset.real_estate_percentage is not None else 0
            cash_pct = asset.cash_percentage if asset.cash_percentage is not None else 0
            alternative_pct = asset.alternative_percentage if asset.alternative_percentage is not None else 0
            
            # Calculate weighted amounts
            total_stocks += amount * stocks_pct / 100
            total_bonds += amount * bonds_pct / 100
            total_real_estate += amount * real_estate_pct / 100
            total_cash += amount * cash_pct / 100
            total_alternative += amount * alternative_pct / 100
        
        
        return {
            "total_assets": round(total_assets, 2),
            "stocks_percentage": round(total_stocks / total_assets * 100, 1) if total_assets > 0 else 0,
            "bonds_percentage": round(total_bonds / total_assets * 100, 1) if total_assets > 0 else 0,
            "real_estate_percentage": round(total_real_estate / total_assets * 100, 1) if total_assets > 0 else 0,
            "cash_percentage": round(total_cash / total_assets * 100, 1) if total_assets > 0 else 0,
            "alternative_percentage": round(total_alternative / total_assets * 100, 1) if total_assets > 0 else 0,
            "stocks_amount": round(total_stocks, 2),
            "bonds_amount": round(total_bonds, 2),
            "real_estate_amount": round(total_real_estate, 2),
            "cash_amount": round(total_cash, 2),
            "alternative_amount": round(total_alternative, 2)
        }
    
    def _analyze_cash_flow(self, monthly_surplus: float, monthly_income: float) -> Dict:
        """Analyze cash flow situation"""
        if monthly_income == 0:
            return {"status": "UNKNOWN", "message": "No income data available"}
        
        surplus_rate = monthly_surplus / monthly_income * 100
        
        if monthly_surplus < 0:
            status = "NEGATIVE"
            message = f"Spending ${abs(monthly_surplus):,.0f}/month more than earning"
        elif surplus_rate < 5:
            status = "TIGHT"
            message = f"Only ${monthly_surplus:,.0f}/month surplus ({surplus_rate:.1f}% of income)"
        elif surplus_rate < 15:
            status = "MODERATE"
            message = f"${monthly_surplus:,.0f}/month surplus ({surplus_rate:.1f}% of income)"
        else:
            status = "STRONG"
            message = f"Excellent ${monthly_surplus:,.0f}/month surplus ({surplus_rate:.1f}% of income)"
        
        return {
            "status": status,
            "monthly_surplus": round(monthly_surplus, 2),
            "surplus_rate": round(surplus_rate, 1),
            "message": message,
            "annual_surplus": round(monthly_surplus * 12, 2)
        }
    
    def _get_retirement_context(self, user_id: int, db: Session) -> Dict:
        """Get essential retirement context for LLM"""
        try:
            from ..services.retirement_calculator import retirement_calculator
            
            # Get comprehensive retirement analysis
            analysis = retirement_calculator.calculate_comprehensive_retirement_analysis(user_id, db)
            
            if not analysis or 'error' in analysis:
                return {"status": "unavailable", "message": "Retirement analysis not available"}
            
            # Extract key retirement facts
            portfolio = analysis.get('portfolio_analysis', {})
            status = analysis.get('status', {})
            ss = analysis.get('social_security', {})
            
            return {
                "completion_percentage": portfolio.get('completion_percentage', 0),
                "surplus_deficit": portfolio.get('surplus_deficit', 0),
                "required_portfolio": portfolio.get('required_portfolio_size', 0),
                "current_retirement_assets": portfolio.get('total_retirement_capable', 0),
                "social_security_monthly": ss.get('monthly_benefit', 0),
                "social_security_annual": ss.get('annual_benefit', 0),
                "retirement_status": status.get('overall', 'UNKNOWN'),
                "can_retire_early": status.get('retirement_readiness', '') == 'Can retire now'
            }
            
        except Exception as e:
            logger.warning(f"Could not get retirement context for user {user_id}: {str(e)}")
            return {"status": "error", "message": str(e)}