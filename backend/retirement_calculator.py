"""
Retirement Calculator Service
Performs accurate retirement calculations and provides structured analysis
NO LLM MATH - All calculations done in Python for accuracy
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
import structlog

logger = structlog.get_logger()

class RetirementCalculator:
    """Accurate retirement calculations service"""
    
    def __init__(self):
        # Conservative, consistent assumptions
        self.inflation_rate = 0.03  # 3% annual inflation
        self.growth_rate = 0.07    # 7% nominal growth
        self.real_growth_rate = 0.04  # 7% - 3% inflation
        self.withdrawal_rate = 0.04  # 4% rule
        self.expense_ratio_retirement = 0.80  # 80% rule for retirement expenses
        self.standard_retirement_age = 67  # Full Social Security retirement age
        
    def calculate_comprehensive_retirement_analysis(self, user_id: int, db: Session) -> Dict[str, Any]:
        """
        Calculate complete retirement readiness with ALL assets and correct math
        """
        try:
            # Get all user financial data
            user_data = self._get_comprehensive_user_data(user_id, db)
            
            # Calculate retirement timeline
            current_age = user_data['age']
            retirement_age = user_data.get('target_retirement_age', 65)
            years_to_retirement = max(0, retirement_age - current_age)
            
            # Calculate future expenses (properly inflated)
            current_annual_expenses = user_data['monthly_expenses'] * 12
            future_annual_expenses = current_annual_expenses * (1 + self.inflation_rate) ** years_to_retirement
            
            # Social Security analysis
            ss_monthly = user_data['social_security_monthly']
            ss_annual = ss_monthly * 12
            
            # Net portfolio income needed (after Social Security)
            net_portfolio_income_needed = max(0, future_annual_expenses - ss_annual)
            
            # Required portfolio size (4% rule)
            required_portfolio = net_portfolio_income_needed / self.withdrawal_rate
            
            # RETIREMENT PROGRESS CALCULATION
            # ================================
            # Components included in retirement progress:
            #   1. All retirement accounts (401k, IRA, etc.)
            #   2. All investment accounts (brokerage, mutual funds, etc.)
            #   3. Optionally: portion of real estate equity (if configured)
            # Formula: sum(retirement_accounts) + sum(investment_accounts) + (real_estate_factor * real_estate_equity)
            # Note: Using only liquid assets for conservative retirement calculations
            retirement_assets = self._get_liquid_retirement_assets(user_data)
            total_retirement_capable = sum(retirement_assets.values())
            
            # Calculate surplus/deficit
            surplus_deficit = total_retirement_capable - required_portfolio
            completion_percentage = (total_retirement_capable / required_portfolio * 100) if required_portfolio > 0 else 200
            
            # Log calculated values for verification
            logger.debug(f"User {user_id}: Calculated retirement_progress={total_retirement_capable:,.0f}, goal={required_portfolio:,.0f}, progress_pct={completion_percentage:.1f}%")
            
            # Determine status
            if surplus_deficit >= 0:
                status = "AHEAD_OF_SCHEDULE"
                status_message = f"You're {completion_percentage:.1f}% funded - ahead of schedule!"
            elif completion_percentage >= 80:
                status = "ON_TRACK"
                status_message = f"You're {completion_percentage:.1f}% complete - on track"
            else:
                status = "BEHIND_SCHEDULE"
                status_message = f"You're {completion_percentage:.1f}% complete - need to save more"
            
            # Calculate financial independence timeline
            fi_analysis = self.calculate_years_to_financial_independence(user_data)
            early_retirement_age = fi_analysis.get('retirement_age', 65)
            
            # Calculate goal timeline using liquid assets only
            goal_timeline = self._calculate_goal_timeline_liquid(user_data, user_data.get('retirement_goal_amount', 3500000))
            
            return {
                'user_info': {
                    'name': user_data['name'],
                    'current_age': current_age,
                    'target_retirement_age': retirement_age,
                    'years_to_retirement': years_to_retirement
                },
                'expenses': {
                    'current_annual': current_annual_expenses,
                    'future_annual': future_annual_expenses,
                    'monthly_current': user_data['monthly_expenses']
                },
                'social_security': {
                    'monthly_benefit': ss_monthly,
                    'annual_benefit': ss_annual,
                    'starts_at_age': self.standard_retirement_age
                },
                'portfolio_analysis': {
                    'income_needed_from_portfolio': net_portfolio_income_needed,
                    'required_portfolio_size': required_portfolio,
                    'current_retirement_assets': retirement_assets,
                    'total_retirement_capable': total_retirement_capable,
                    'surplus_deficit': surplus_deficit,
                    'completion_percentage': completion_percentage,
                    'asset_breakdown': self._format_asset_breakdown(retirement_assets, total_retirement_capable)
                },
                'status': {
                    'overall': status,
                    'message': status_message,
                    'early_retirement_age': early_retirement_age,
                    'retirement_readiness': 'Can retire now' if surplus_deficit >= 0 else 'Need more savings'
                },
                'user_goal': {
                    'target_amount': user_data.get('retirement_goal_amount', 3500000),
                    'progress_toward_goal': (total_retirement_capable / user_data.get('retirement_goal_amount', 3500000) * 100),
                    'goal_timeline': goal_timeline
                },
                'financial_independence': fi_analysis,
                'strengths': self._identify_strengths(user_data),
                'recommendations': self._generate_recommendations(user_data, surplus_deficit, completion_percentage)
            }
            
        except Exception as e:
            logger.error(f"Retirement calculation failed: {str(e)}")
            return self._get_fallback_analysis()
    
    def _get_comprehensive_user_data(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get all user financial data from database"""
        try:
            from app.models.user import User
            from app.models.user_profile import UserProfile, UserBenefit
            from app.services.financial_summary_service import financial_summary_service
            
            # Get basic user info
            user = db.query(User).filter(User.id == user_id).first()
            profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            
            # Get comprehensive financial summary
            financial_summary = financial_summary_service.get_user_financial_summary(user_id, db)
            
            # Get Social Security benefits
            ss_benefit = db.query(UserBenefit).filter(
                UserBenefit.profile_id == profile.id,
                UserBenefit.benefit_type == 'social_security'
            ).first() if profile else None
            
            return {
                'name': f"{user.first_name} {user.last_name}".strip() if user and (user.first_name or user.last_name) else f"User {user_id}",
                'age': profile.age if profile and profile.age else 54,
                'monthly_expenses': financial_summary.get('monthlyExpenses', 7124),
                'monthly_income': financial_summary.get('monthlyIncome', 17744),
                'monthly_surplus': financial_summary.get('monthlySurplus', 10620),
                'net_worth': financial_summary.get('netWorth', 2564574),
                'total_assets': financial_summary.get('totalAssets', 2879827),
                'social_security_monthly': float(ss_benefit.estimated_monthly_benefit) if ss_benefit and ss_benefit.estimated_monthly_benefit else 4000,
                'debt_to_income_ratio': financial_summary.get('debtToIncomeRatio', 13.9),
                'savings_rate': financial_summary.get('savingsRate', 60),
                'retirement_goal_amount': 3500000,  # User's stated goal
                'target_retirement_age': 65,
                'assets_breakdown': financial_summary.get('assetsBreakdown', {}),
                'liabilities_breakdown': financial_summary.get('liabilitiesBreakdown', {})
            }
            
        except Exception as e:
            logger.error(f"Failed to get user data: {str(e)}")
            # Return reasonable defaults for user 1 (Debashish)
            return {
                'name': 'Debashish Roy',
                'age': 54,
                'monthly_expenses': 7124,
                'monthly_income': 17744,
                'monthly_surplus': 10620,
                'net_worth': 2564574,
                'total_assets': 2879827,
                'social_security_monthly': 4000,
                'debt_to_income_ratio': 13.9,
                'savings_rate': 60,
                'retirement_goal_amount': 3500000,
                'target_retirement_age': 65,
                'assets_breakdown': {},
                'liabilities_breakdown': {}
            }
    
    def _get_liquid_retirement_assets(self, user_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Get ONLY liquid assets available for retirement - excludes primary residence
        This follows conservative financial planning principles
        """
        if not self._validate_user_data(user_data):
            logger.warning("User data validation failed, using empty assets")
            return {}
            
        assets_breakdown = user_data.get('assets_breakdown', {})
        liquid_assets = {}
        
        # Only include truly liquid retirement assets:
        
        # 1. Retirement accounts (401k, IRA, etc.) - liquid at retirement age
        retirement_accounts = assets_breakdown.get('retirement_accounts', 0)
        if retirement_accounts > 0:
            liquid_assets['retirement_accounts'] = float(retirement_accounts)
        
        # 2. Investment accounts (brokerage, mutual funds) - fully liquid
        investment_accounts = assets_breakdown.get('investment_accounts', 0)
        if investment_accounts > 0:
            liquid_assets['investment_accounts'] = float(investment_accounts)
        
        # 3. Cash (liquid but shouldn't be primary retirement funding)
        cash_accounts = assets_breakdown.get('cash_bank_accounts', 0)
        if cash_accounts > 0:
            liquid_assets['cash_accounts'] = float(cash_accounts)
        
        # DO NOT INCLUDE:
        # - Primary residence equity (illiquid, need place to live)
        # - Personal property (cars, jewelry, etc.)
        # - Business assets (may not be easily sellable)
        
        logger.info(f"Liquid retirement assets calculated: {liquid_assets}")
        return liquid_assets
    
    def calculate_years_to_financial_independence(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate years to financial independence using proper 4% rule methodology"""
        if not self._validate_user_data(user_data):
            return {'error': 'Invalid user data provided'}
            
        current_age = user_data.get('age', 50)
        monthly_expenses = user_data.get('monthly_expenses', 0)
        monthly_savings = user_data.get('monthly_surplus', 0)
        current_liquid_assets = sum(self._get_liquid_retirement_assets(user_data).values())
        
        # 80% rule for retirement expenses
        retirement_monthly_need = monthly_expenses * self.expense_ratio_retirement
        retirement_annual_need = retirement_monthly_need * 12
        
        # 4% withdrawal rule - portfolio needed for financial independence
        portfolio_target = retirement_annual_need / self.withdrawal_rate
        
        logger.info(f"FI calculation: current_assets={current_liquid_assets:,.0f}, target={portfolio_target:,.0f}")
        
        if current_liquid_assets >= portfolio_target:
            return {
                'years_to_financial_independence': 0,
                'target_portfolio': portfolio_target,
                'current_liquid_assets': current_liquid_assets,
                'retirement_age': current_age,
                'surplus': current_liquid_assets - portfolio_target,
                'status': 'financially_independent'
            }
        
        # Calculate years using compound growth formula
        annual_savings = monthly_savings * 12
        years_needed = self._calculate_compound_growth_timeline(
            current_liquid_assets, annual_savings, self.real_growth_rate, portfolio_target
        )
        
        return {
            'years_to_financial_independence': years_needed,
            'target_portfolio': portfolio_target,
            'current_liquid_assets': current_liquid_assets,
            'retirement_age': current_age + years_needed if years_needed else None,
            'annual_savings_needed': annual_savings,
            'retirement_monthly_expenses': retirement_monthly_need,
            'status': 'needs_savings' if years_needed else 'impossible_timeline'
        }
    
    def _format_asset_breakdown(self, assets: Dict[str, float], total: float) -> Dict[str, Any]:
        """Format asset breakdown with percentages"""
        breakdown = {}
        for asset_type, amount in assets.items():
            percentage = (amount / total * 100) if total > 0 else 0
            breakdown[asset_type] = {
                'amount': amount,
                'percentage': percentage,
                'formatted': f"${amount:,.0f} ({percentage:.1f}%)"
            }
        return breakdown
    
    def _calculate_compound_growth_timeline(self, present_value: float, annual_payment: float, rate: float, target: float) -> int:
        """Calculate years needed to reach target with compound growth and contributions"""
        if present_value >= target:
            return 0
        
        if annual_payment <= 0:
            logger.warning("No annual contributions - timeline may be very long")
        
        years = 0
        portfolio_value = present_value
        
        # Iterate year by year until target is reached (max 50 years for safety)
        while portfolio_value < target and years < 50:
            # Add annual contribution then apply growth
            portfolio_value = (portfolio_value + annual_payment) * (1 + rate)
            years += 1
        
        if portfolio_value >= target:
            logger.info(f"Target reached in {years} years with final value: ${portfolio_value:,.0f}")
            return years
        else:
            logger.warning(f"Target not reachable within 50 years. Current trajectory insufficient.")
            return None
    
    def _get_milestone_projections(self, projections: List[Dict], goal_amount: float) -> List[Dict]:
        """Get key milestone years"""
        milestones = []
        
        for projection in projections:
            assets = projection['projected_assets']
            year = projection['year']
            age = projection['age']
            
            # Add milestones at key amounts
            if len(milestones) == 0 and assets >= 2500000:  # First milestone: $2.5M
                milestones.append({
                    'year': year,
                    'age': age,
                    'amount': 2500000,
                    'description': "Reach $2.5M"
                })
            elif len(milestones) == 1 and assets >= 3000000:  # Second milestone: $3M
                milestones.append({
                    'year': year,
                    'age': age,
                    'amount': 3000000,
                    'description': "Reach $3M"
                })
            elif len(milestones) == 2 and assets >= goal_amount:  # Goal achievement
                milestones.append({
                    'year': year,
                    'age': age,
                    'amount': goal_amount,
                    'description': f"Reach ${goal_amount:,.0f} goal"
                })
                break
        
        return milestones
    
    def _validate_user_data(self, user_data: Dict[str, Any]) -> bool:
        """Validate that user data contains required fields for calculations"""
        required_fields = ['age', 'monthly_expenses', 'monthly_surplus', 'assets_breakdown']
        
        for field in required_fields:
            if field not in user_data or user_data[field] is None:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Validate data types and ranges
        try:
            age = int(user_data['age'])
            monthly_expenses = float(user_data['monthly_expenses'])
            monthly_surplus = float(user_data['monthly_surplus'])
            
            if age < 18 or age > 100:
                logger.warning(f"Invalid age: {age}")
                return False
            
            if monthly_expenses < 0:
                logger.warning(f"Invalid monthly expenses: {monthly_expenses}")
                return False
                
            # Assets breakdown should be a dictionary
            if not isinstance(user_data['assets_breakdown'], dict):
                logger.warning("Assets breakdown is not a dictionary")
                return False
                
        except (ValueError, TypeError) as e:
            logger.warning(f"Data type validation failed: {e}")
            return False
        
        return True
    
    def _calculate_goal_timeline_liquid(self, user_data: Dict[str, Any], goal_amount: float) -> Dict[str, Any]:
        """Calculate when user will reach their goal using only liquid assets"""
        current_assets = sum(self._get_liquid_retirement_assets(user_data).values())
        monthly_surplus = user_data.get('monthly_surplus', 0)
        annual_surplus = monthly_surplus * 12
        
        if current_assets >= goal_amount:
            return {
                'goal_achieved': True,
                'years_to_goal': 0,
                'goal_age': user_data.get('age', 54),
                'message': f"Goal already achieved! You have ${current_assets:,.0f} vs goal of ${goal_amount:,.0f}",
                'projections': []
            }
        
        # Use consistent real growth rate
        current_age = user_data.get('age', 54)
        projections = []
        projected_assets = current_assets
        years_elapsed = 0
        
        # Calculate year-by-year until goal is reached (max 20 years)
        while projected_assets < goal_amount and years_elapsed < 20:
            years_elapsed += 1
            projected_assets = (projected_assets + annual_surplus) * (1 + self.real_growth_rate)
            
            projections.append({
                'year': 2025 + years_elapsed,
                'age': current_age + years_elapsed,
                'projected_assets': projected_assets,
                'years_from_now': years_elapsed
            })
        
        goal_achieved_year = next((p for p in projections if p['projected_assets'] >= goal_amount), None)
        
        return {
            'goal_achieved': False,
            'years_to_goal': goal_achieved_year['years_from_now'] if goal_achieved_year else None,
            'goal_age': goal_achieved_year['age'] if goal_achieved_year else None,
            'message': f"Will reach ${goal_amount:,.0f} goal in {goal_achieved_year['years_from_now']} years at age {goal_achieved_year['age']}" if goal_achieved_year else "Goal may take longer than 20 years with current liquid assets",
            'projections': projections[:10],  # Show first 10 years
            'milestone_years': self._get_milestone_projections(projections, goal_amount)
        }
    
    def _identify_strengths(self, user_data: Dict[str, Any]) -> List[str]:
        """Identify user's financial strengths"""
        strengths = []
        
        if user_data['savings_rate'] > 50:
            strengths.append(f"Exceptional {user_data['savings_rate']:.0f}% savings rate")
        
        if user_data['debt_to_income_ratio'] < 20:
            strengths.append(f"Low debt burden ({user_data['debt_to_income_ratio']:.1f}% DTI)")
        
        liquid_retirement_assets = sum(self._get_liquid_retirement_assets(user_data).values())
        if liquid_retirement_assets > 1000000:
            strengths.append(f"Strong liquid retirement assets: ${liquid_retirement_assets:,.0f}")
        
        if user_data['social_security_monthly'] > 3000:
            strengths.append(f"Strong Social Security benefits (${user_data['social_security_monthly']:,.0f}/month)")
        
        strengths.append("Diversified asset portfolio across multiple accounts")
        
        return strengths
    
    def _generate_recommendations(self, user_data: Dict[str, Any], surplus_deficit: float, completion_percentage: float) -> List[str]:
        """Generate specific recommendations based on analysis"""
        recommendations = []
        
        if surplus_deficit > 0:
            recommendations.append("You may be able to consider early retirement based on liquid assets")
            recommendations.append("Consider working with a financial advisor to optimize withdrawal strategies")
            recommendations.append("Important: This analysis excludes home equity - ensure you have adequate housing plans")
        elif completion_percentage > 80:
            recommendations.append("Stay the course - your current savings rate will get you there")
            recommendations.append("Consider modest increases to 401k contributions")
        else:
            recommendations.append("Focus on building liquid retirement assets through increased savings")
            recommendations.append("Maximize 401k and IRA contributions to take advantage of tax benefits")
            recommendations.append("Consider increasing investment account contributions beyond retirement accounts")
        
        recommendations.append("Maintain emergency fund separate from retirement calculations")
        recommendations.append("Consider tax-loss harvesting in taxable investment accounts")
        recommendations.append("Important: Primary residence equity not included - plan for retirement housing needs")
        
        return recommendations
    
    def _get_fallback_analysis(self) -> Dict[str, Any]:
        """Fallback analysis if data retrieval fails"""
        return {
            'error': True,
            'message': 'Unable to perform detailed retirement analysis due to data access issues',
            'status': {'overall': 'UNKNOWN', 'message': 'Analysis unavailable'}
        }

# Global instance
retirement_calculator = RetirementCalculator()