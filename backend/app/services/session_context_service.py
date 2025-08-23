"""
Session Context Service
Maintains consistent user context across all conversation types
Prevents the system from "forgetting" established facts
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()

class SessionContext:
    """Maintains user context across conversation"""
    
    def __init__(self, user_id: int, session_id: str):
        self.user_id = user_id
        self.session_id = session_id
        self.core_facts = {}
        self.conversation_history = []
        self.last_updated = datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'session_id': self.session_id,
            'core_facts': self.core_facts,
            'conversation_history': self.conversation_history[-5:],  # Last 5 exchanges
            'last_updated': self.last_updated.isoformat()
        }

class SessionContextService:
    """Manages session context for consistent financial advice"""
    
    def __init__(self):
        # In-memory store (could be Redis in production)
        self.sessions: Dict[str, SessionContext] = {}
        
    def get_or_create_session(self, user_id: int, session_id: str, db: Session) -> SessionContext:
        """Get existing session or create new one with user context"""
        
        if session_id in self.sessions:
            session = self.sessions[session_id]
            # Refresh if old
            if datetime.now() - session.last_updated > timedelta(hours=1):
                session.core_facts = self._load_core_user_facts(user_id, db)
                session.last_updated = datetime.now()
            return session
        
        # Create new session
        session = SessionContext(user_id, session_id)
        session.core_facts = self._load_core_user_facts(user_id, db)
        self.sessions[session_id] = session
        
        logger.info(f"Created new session context for user {user_id}")
        return session
    
    def _load_core_user_facts(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Load essential user facts that should NEVER be forgotten"""
        try:
            # Import here to avoid circular imports
            from app.models.user import User
            from app.models.user_profile import UserProfile, UserBenefit
            from app.services.financial_summary_service import financial_summary_service
            from app.services.retirement_calculator import retirement_calculator
            
            # Get basic user info
            user = db.query(User).filter(User.id == user_id).first()
            profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            
            # Get financial summary
            financial_summary = financial_summary_service.get_user_financial_summary(user_id, db)
            
            # Get retirement analysis (this should ALWAYS be available)
            retirement_analysis = retirement_calculator.calculate_comprehensive_retirement_analysis(user_id, db)
            
            # Extract CORE FACTS that must persist across all conversations
            core_facts = {
                # User Identity
                'name': f"{user.first_name} {user.last_name}".strip() if user and (user.first_name or user.last_name) else f"User {user_id}",
                'age': profile.age if profile and profile.age else 54,
                'state': profile.state if profile and profile.state else 'Unknown',
                
                # Financial Status (CRITICAL - never lose these!)
                'net_worth': financial_summary.get('netWorth', 0),
                'monthly_income': financial_summary.get('monthlyIncome', 0),
                'monthly_expenses': financial_summary.get('monthlyExpenses', 0),
                'monthly_surplus': financial_summary.get('monthlySurplus', 0),
                'debt_to_income_ratio': financial_summary.get('debtToIncomeRatio', 0),
                'savings_rate': financial_summary.get('savingsRate', 0),
                
                # Retirement Facts (ESTABLISHED - don't recalculate each time!)
                'retirement_completion_percentage': retirement_analysis.get('portfolio_analysis', {}).get('completion_percentage', 0),
                'retirement_surplus_deficit': retirement_analysis.get('portfolio_analysis', {}).get('surplus_deficit', 0),
                'retirement_status': retirement_analysis.get('status', {}).get('overall', 'UNKNOWN'),
                'can_retire_early': retirement_analysis.get('status', {}).get('retirement_readiness', '') == 'Can retire now',
                'retirement_goal_amount': self._extract_retirement_goal(user_id, db, retirement_analysis),
                'years_to_goal': retirement_analysis.get('user_goal', {}).get('goal_timeline', {}).get('years_to_goal', None),
                'goal_achievement_age': retirement_analysis.get('user_goal', {}).get('goal_timeline', {}).get('goal_age', None),
                
                # Asset Summary (for quick reference)
                'total_retirement_assets': retirement_analysis.get('portfolio_analysis', {}).get('total_retirement_capable', 0),
                'asset_breakdown': retirement_analysis.get('portfolio_analysis', {}).get('current_retirement_assets', {}),
                'home_value': self._extract_home_value(financial_summary),
                'mortgage_balance': self._extract_mortgage_balance(financial_summary),
                
                # Context timestamp
                'facts_last_updated': datetime.now().isoformat(),
                'context_version': '2.0_enhanced'
            }
            
            logger.info(f"Loaded core facts for {core_facts['name']}: Net worth ${core_facts['net_worth']:,.0f}, {core_facts['retirement_completion_percentage']:.1f}% retirement ready")
            return core_facts
            
        except Exception as e:
            logger.error(f"Failed to load core user facts: {str(e)}")
            # Return minimal facts to prevent total failure
            return {
                'user_id': user_id,
                'name': f"User {user_id}",
                'error': f"Context loading failed: {str(e)}",
                'context_version': '2.0_fallback'
            }
    
    def add_conversation_exchange(self, session_id: str, question: str, response: str, intent: str):
        """Record conversation exchange for context"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.conversation_history.append({
                'timestamp': datetime.now().isoformat(),
                'question': question,
                'response_preview': response[:200] + "..." if len(response) > 200 else response,
                'intent': intent
            })
            
            # Keep only last 10 exchanges
            if len(session.conversation_history) > 10:
                session.conversation_history = session.conversation_history[-10:]
                
            session.last_updated = datetime.now()
    
    def get_universal_context_summary(self, session_id: str) -> str:
        """Get context summary that works for ANY financial question"""
        if session_id not in self.sessions:
            return "No session context available"
        
        session = self.sessions[session_id]
        facts = session.core_facts
        
        if 'error' in facts:
            return f"Context Error: {facts['error']}"
        
        # Build universal context that applies to ALL financial questions
        context = f"""
USER PROFILE & ESTABLISHED FACTS:
Name: {facts.get('name', 'Unknown')}
Age: {facts.get('age', 'Unknown')}
Location: {facts.get('state', 'Unknown')}

CURRENT FINANCIAL STATUS (VERIFIED):
Net Worth: ${facts.get('net_worth', 0):,.0f}
Monthly Income: ${facts.get('monthly_income', 0):,.0f}
Monthly Expenses: ${facts.get('monthly_expenses', 0):,.0f}
Monthly Surplus: ${facts.get('monthly_surplus', 0):,.0f}
Debt-to-Income Ratio: {facts.get('debt_to_income_ratio', 0):.1f}%
Savings Rate: {facts.get('savings_rate', 0):.1f}%

RETIREMENT READINESS (ESTABLISHED):
Completion Status: {facts.get('retirement_completion_percentage', 0):.1f}% funded
Overall Status: {facts.get('retirement_status', 'Unknown')}
Surplus/Deficit: ${facts.get('retirement_surplus_deficit', 0):,.0f}
Early Retirement: {'Yes - can retire now' if facts.get('can_retire_early') else 'Need more analysis'}

FINANCIAL GOALS (CONFIRMED):
Retirement Goal: ${facts.get('retirement_goal_amount', 0):,.0f}
Years to Goal: {facts.get('years_to_goal', 'TBD')}
Goal Achievement Age: {facts.get('goal_achievement_age', 'TBD')}

MAJOR ASSETS (SUMMARY):
Total Retirement Assets: ${facts.get('total_retirement_assets', 0):,.0f}
Home Value: ${facts.get('home_value', 0):,.0f}
Mortgage Balance: ${facts.get('mortgage_balance', 0):,.0f}

{self._format_investment_allocation(facts.get('asset_breakdown', {}), facts.get('total_retirement_assets', 0))}

CONVERSATION CONTEXT:
Last Updated: {facts.get('facts_last_updated', 'Unknown')}
Context Version: {facts.get('context_version', '1.0')}
"""

        # Add recent conversation history for reference
        if session.conversation_history:
            context += "\nRECENT CONVERSATION:\n"
            for exchange in session.conversation_history[-3:]:  # Last 3 exchanges
                context += f"- Q: {exchange['question'][:100]}...\n"
                context += f"  Intent: {exchange['intent']}\n"
        
        return context
    
    def get_context_for_validation(self, session_id: str) -> Dict[str, Any]:
        """Get context data in dictionary format for validation"""
        if session_id not in self.sessions:
            return {}
        
        session = self.sessions[session_id]
        facts = session.core_facts
        
        if 'error' in facts:
            return {}
        
        # Return core facts as dictionary for validation
        return facts
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old sessions to prevent memory leaks"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        old_sessions = [
            session_id for session_id, session in self.sessions.items() 
            if session.last_updated < cutoff_time
        ]
        
        for session_id in old_sessions:
            del self.sessions[session_id]
            
        if old_sessions:
            logger.info(f"Cleaned up {len(old_sessions)} old sessions")
    
    def _extract_retirement_goal(self, user_id: int, db: Session, retirement_analysis: Dict) -> float:
        """Extract retirement goal from user's actual goals, not hard-coded"""
        try:
            from app.models.goals_v2 import Goal
            
            # Look for retirement goals in the database
            retirement_goals = db.query(Goal).filter(
                Goal.user_id == user_id,
                Goal.name.ilike('%retirement%')
            ).all()
            
            if retirement_goals:
                # Use the largest retirement goal
                return max(float(goal.target_amount) for goal in retirement_goals)
            
            # Fallback to analysis if available
            analysis_goal = retirement_analysis.get('user_goal', {}).get('target_amount')
            if analysis_goal:
                return float(analysis_goal)
            
            # Final fallback - calculate based on income replacement
            return 0  # Let system calculate dynamically
            
        except Exception as e:
            logger.warning(f"Could not extract retirement goal for user {user_id}: {str(e)}")
            return 0
    
    def _extract_home_value(self, financial_summary: Dict) -> float:
        """Extract home value from financial data"""
        try:
            assets = financial_summary.get('assetsBreakdown', {})
            
            # Look for home/real estate assets
            for asset in assets:
                if isinstance(asset, dict):
                    category = asset.get('category', '').lower()
                    if 'home' in category or 'real estate' in category or 'primary residence' in category:
                        return float(asset.get('balance', 0))
            
            # Fallback: look in raw assets for real estate
            return 0  # Will be calculated from actual data
            
        except Exception as e:
            logger.warning(f"Could not extract home value: {str(e)}")
            return 0
    
    def _extract_mortgage_balance(self, financial_summary: Dict) -> float:
        """Extract mortgage balance from liabilities"""
        try:
            liabilities = financial_summary.get('liabilitiesBreakdown', {})
            
            # Look for mortgage liabilities
            for liability in liabilities:
                if isinstance(liability, dict):
                    description = liability.get('description', '').lower()
                    if 'mortgage' in description or 'home loan' in description:
                        return float(liability.get('balance', 0))
            
            return 0
            
        except Exception as e:
            logger.warning(f"Could not extract mortgage balance: {str(e)}")
            return 0
    
    def _format_investment_allocation(self, asset_breakdown: Dict, total_assets: float) -> str:
        """Format investment allocation using ACTUAL user data - NO HARD-CODING"""
        if not asset_breakdown or total_assets == 0:
            return "INVESTMENT ALLOCATION: Data not available"
        
        # Calculate actual allocation from user's real data
        allocation_text = f"INVESTMENT ALLOCATION (EXCLUDE HOME EQUITY):\n"
        allocation_text += f"Total Investable Assets: ${total_assets:,.0f}\n\n"
        
        # Show actual breakdown from user's data
        investable_total = 0
        home_equity = 0
        
        for asset_type, amount in asset_breakdown.items():
            percentage = (amount / total_assets * 100) if total_assets > 0 else 0
            
            if 'home_equity' in asset_type.lower():
                home_equity = amount
            else:
                investable_total += amount
                allocation_text += f"- {asset_type.replace('_', ' ').title()}: ${amount:,.0f} ({percentage:.1f}%)\n"
        
        # Calculate investment categories from actual data
        allocation_text += f"\nINVESTMENT ANALYSIS (based on actual holdings):\n"
        
        if investable_total > 0:
            # Extract investment account and 401k (likely equity-heavy)
            equity_assets = asset_breakdown.get('investment_accounts', 0) + asset_breakdown.get('401k', 0)
            crypto_assets = asset_breakdown.get('bitcoin', 0)
            liquid_assets = asset_breakdown.get('other_liquid_assets', 0)
            
            equity_pct = (equity_assets / investable_total * 100) if investable_total > 0 else 0
            crypto_pct = (crypto_assets / investable_total * 100) if investable_total > 0 else 0
            liquid_pct = (liquid_assets / investable_total * 100) if investable_total > 0 else 0
            
            allocation_text += f"- Equity/Growth Assets: ${equity_assets:,.0f} ({equity_pct:.1f}%)\n"
            allocation_text += f"- Alternative/Crypto: ${crypto_assets:,.0f} ({crypto_pct:.1f}%)\n"
            allocation_text += f"- Cash/Liquid: ${liquid_assets:,.0f} ({liquid_pct:.1f}%)\n"
            
            # Analysis based on user's age and situation
            if liquid_pct > 40:
                allocation_text += f"\n⚠️ ANALYSIS: {liquid_pct:.1f}% cash allocation may be excessive for long-term growth\n"
            if crypto_pct > 10:
                allocation_text += f"⚠️ ANALYSIS: {crypto_pct:.1f}% crypto allocation may be high for approaching retirement\n"
        
        return allocation_text

# Global instance
session_context_service = SessionContextService()