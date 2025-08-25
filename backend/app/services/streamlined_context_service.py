"""
Streamlined Context Service
Provides focused, prioritized financial context for LLMs
Solves the context fragmentation and data loss issues
"""
from typing import Dict, List, Optional, Tuple
import logging
from sqlalchemy.orm import Session
from datetime import datetime
from .enhanced_context_service import EnhancedContextService
from .session_context_service import SessionContextService

logger = logging.getLogger(__name__)


class StreamlinedContextService:
    """
    Provides focused, prioritized financial context for LLMs
    Ensures critical financial data always reaches the LLM
    """
    
    def __init__(self):
        self.enhanced_service = EnhancedContextService()
        self.session_service = SessionContextService()
    
    def get_priority_context(self, user_id: int, session_id: str, db: Session, 
                           intent: str = "general", max_chars: int = 1200) -> str:
        """
        Get prioritized financial context that fits within character limits
        Ensures critical data always makes it to the LLM
        
        Args:
            user_id: User ID
            session_id: Session ID for context continuity
            db: Database session
            intent: Financial intent (retirement, debt, investment, etc.)
            max_chars: Maximum characters for context
            
        Returns:
            Focused context string optimized for LLM consumption
        """
        try:
            # Get session context for established facts
            session = self.session_service.get_or_create_session(user_id, session_id, db)
            
            # Get smart context with calculations
            smart_context = self.enhanced_service.build_smart_context(user_id)
            
            if 'error' in smart_context:
                return f"Financial data temporarily unavailable: {smart_context['error']}"
            
            # Build prioritized context based on intent
            context_parts = []
            
            # PRIORITY 1: Core Identity & Status (always include)
            core_facts = self._build_core_facts(session.core_facts, smart_context)
            context_parts.append(("CORE", core_facts))
            
            # PRIORITY 2: Intent-specific critical data
            intent_context = self._build_intent_context(intent, smart_context, session.core_facts)
            if intent_context:
                context_parts.append(("INTENT", intent_context))
            
            # PRIORITY 3: Supporting financial data
            supporting_context = self._build_supporting_context(smart_context)
            context_parts.append(("SUPPORT", supporting_context))
            
            # Assemble context within character limit
            final_context = self._assemble_context(context_parts, max_chars)
            
            logger.info(f"Built streamlined context for user {user_id}: {len(final_context)} chars, intent={intent}")
            return final_context
            
        except Exception as e:
            logger.error(f"Error building streamlined context for user {user_id}: {str(e)}")
            return f"Context error: {str(e)}"
    
    def _build_core_facts(self, session_facts: Dict, smart_context: Dict) -> str:
        """Build comprehensive core facts for professional analysis"""
        name = session_facts.get('name', f"User {smart_context.get('user_id', 'Unknown')}")
        age = session_facts.get('age', 'Unknown')
        net_worth = smart_context.get('net_worth', 0)
        total_assets = smart_context.get('total_assets', 0)
        total_liabilities = smart_context.get('total_liabilities', 0)
        monthly_income = smart_context.get('monthly_income', 0)
        monthly_expenses = smart_context.get('monthly_expenses', 0)
        monthly_surplus = smart_context.get('monthly_surplus', 0)
        debt_to_income = smart_context.get('debt_to_income_ratio', 0)
        
        # Calculate key ratios for professional analysis
        savings_rate = (monthly_surplus / monthly_income * 100) if monthly_income > 0 else 0
        debt_to_asset_ratio = (total_liabilities / total_assets * 100) if total_assets > 0 else 0
        
        # Get retirement status from context
        retirement_ctx = smart_context.get('retirement_context', {})
        completion_pct = retirement_ctx.get('completion_percentage', 0)
        
        core = f"""CLIENT PROFILE: {name} (age {age})
FINANCIAL POSITION:
• Net Worth: ${net_worth:,.0f} (Assets: ${total_assets:,.0f}, Liabilities: ${total_liabilities:,.0f})
• Monthly Cash Flow: ${monthly_income:,.0f} income - ${monthly_expenses:,.0f} expenses = ${monthly_surplus:,.0f} surplus
• Key Ratios: {savings_rate:.1f}% savings rate, {debt_to_income:.1f}% DTI, {debt_to_asset_ratio:.1f}% debt-to-asset

RETIREMENT ANALYSIS:
• Funding Status: {completion_pct:.1f}% of retirement goal"""

        # Add detailed retirement context
        if retirement_ctx.get('social_security_annual', 0) > 0:
            ss_annual = retirement_ctx['social_security_annual']
            ss_monthly = ss_annual / 12
            core += f"\n• Social Security: ${ss_monthly:,.0f}/month (${ss_annual:,.0f}/year)"
        
        if retirement_ctx.get('surplus_deficit', 0) != 0:
            surplus = retirement_ctx['surplus_deficit']
            status = "AHEAD" if surplus > 0 else "BEHIND"
            core += f"\n• Status: {status} by ${abs(surplus):,.0f}"
            
            if surplus > 0:
                core += f" (Early retirement feasible)"
        
        # Add portfolio context if available
        portfolio = smart_context.get('portfolio_breakdown', {})
        if portfolio.get('total_assets', 0) > 0:
            stocks_pct = portfolio.get('stocks_percentage', 0)
            bonds_pct = portfolio.get('bonds_percentage', 0)
            cash_pct = portfolio.get('cash_percentage', 0)
            re_pct = portfolio.get('real_estate_percentage', 0)
            alt_pct = portfolio.get('alternative_percentage', 0)
            
            core += f"\n\nPORTFOLIO ALLOCATION: {stocks_pct:.1f}% stocks, {bonds_pct:.1f}% bonds, {re_pct:.1f}% real estate, {cash_pct:.1f}% cash, {alt_pct:.1f}% alternatives"
        
        return core
    
    def _build_intent_context(self, intent: str, smart_context: Dict, session_facts: Dict) -> Optional[str]:
        """Build context specific to the detected intent"""
        
        intent_builders = {
            'retirement': self._build_retirement_intent_context,
            'debt': self._build_debt_intent_context,
            'investment': self._build_investment_intent_context,
            'goals': self._build_goals_intent_context,
            'budget': self._build_budget_intent_context,
            'net_worth': self._build_networth_intent_context
        }
        
        builder = intent_builders.get(intent.lower())
        if builder:
            return builder(smart_context, session_facts)
        
        return None
    
    def _build_retirement_intent_context(self, smart_context: Dict, session_facts: Dict) -> str:
        """Build comprehensive retirement-specific context"""
        retirement_ctx = smart_context.get('retirement_context', {})
        
        if not retirement_ctx or retirement_ctx.get('status') == 'unavailable':
            return "RETIREMENT: Analysis pending"
        
        required = retirement_ctx.get('required_portfolio', 0)
        current = retirement_ctx.get('current_retirement_assets', 0)
        ss_monthly = retirement_ctx.get('social_security_monthly', 0)
        ss_annual = retirement_ctx.get('social_security_annual', 0)
        completion_pct = retirement_ctx.get('completion_percentage', 0)
        surplus_deficit = retirement_ctx.get('surplus_deficit', 0)
        
        # Calculate withdrawal rates and scenarios
        monthly_income = smart_context.get('monthly_income', 0)
        annual_income = monthly_income * 12
        replacement_80pct = annual_income * 0.8
        replacement_70pct = annual_income * 0.7
        
        context = f"""DETAILED RETIREMENT ANALYSIS:
• Current Position: {completion_pct:.1f}% funded (${current:,.0f} of ${required:,.0f} required)
• Surplus/Deficit: ${surplus_deficit:+,.0f}
• Social Security: ${ss_monthly:,.0f}/month starting at 67 (${ss_annual:,.0f}/year)

WITHDRAWAL SCENARIOS:
• 80% Income Replacement: ${replacement_80pct:,.0f}/year needed
• 70% Income Replacement: ${replacement_70pct:,.0f}/year needed
• Net Portfolio Need (after SS): ${max(0, replacement_80pct - ss_annual):,.0f}/year
• Safe Withdrawal Rate: {(current * 0.04):,.0f}/year at 4% rule"""

        if surplus_deficit > 0:
            context += f"\n• EARLY RETIREMENT: Feasible with ${surplus_deficit:,.0f} surplus"
            # Calculate early retirement age
            age = session_facts.get('age', 54)
            if age and monthly_income > 0:
                years_of_expenses = surplus_deficit / (monthly_income * 12 * 0.8)
                early_retirement_age = age + max(0, 10 - years_of_expenses)  # Conservative estimate
                context += f" (potential age {early_retirement_age:.0f})"
        
        return context
    
    def _build_debt_intent_context(self, smart_context: Dict, session_facts: Dict) -> str:
        """Build comprehensive debt analysis context"""
        dti = smart_context.get('debt_to_income_ratio', 0)
        monthly_debt = smart_context.get('monthly_debt_payments', 0)
        monthly_income = smart_context.get('monthly_income', 0)
        monthly_surplus = smart_context.get('monthly_surplus', 0)
        debt_strategy = smart_context.get('debt_strategy', [])
        
        context = f"""COMPREHENSIVE DEBT ANALYSIS:
• DTI Ratio: {dti:.1f}% (Excellent <20%, Good <36%, High >36%)
• Monthly Debt Service: ${monthly_debt:,.0f} of ${monthly_income:,.0f} income
• Available for Extra Payments: ${monthly_surplus:,.0f}/month surplus"""

        if debt_strategy:
            context += f"\n\nDEBT PRIORITIZATION (Avalanche Method):"
            for i, debt in enumerate(debt_strategy[:3]):  # Top 3 debts
                annual_cost = debt.get('annual_interest_cost', 0)
                daily_cost = debt.get('daily_interest_cost', 0)
                context += f"\n• #{i+1}: {debt['name']} - ${debt['balance']:,.0f} @ {debt['rate']:.2f}%"
                context += f" (${annual_cost:,.0f}/year cost, ${daily_cost:.2f}/day)"
                
                # Calculate payoff scenarios
                if monthly_surplus > 0:
                    extra_payment = min(monthly_surplus * 0.5, 1000)  # Up to 50% of surplus
                    if extra_payment > 50:
                        context += f"\n  → Extra ${extra_payment:,.0f}/month could save significant interest"
        
        # Opportunity cost analysis
        if monthly_surplus > 1000:
            context += f"\n\nOPPORTUNITY COST: With ${monthly_surplus:,.0f} surplus, analyze debt payoff vs investment returns"
        
        return context
    
    def _build_investment_intent_context(self, smart_context: Dict, session_facts: Dict) -> str:
        """Build comprehensive investment analysis context"""
        portfolio = smart_context.get('portfolio_breakdown', {})
        
        if not portfolio or portfolio.get('total_assets', 0) == 0:
            return "INVESTMENTS: No portfolio data available"
        
        total_assets = portfolio.get('total_assets', 0)
        stocks_pct = portfolio.get('stocks_percentage', 0)
        stocks_amt = portfolio.get('stocks_amount', 0)
        bonds_pct = portfolio.get('bonds_percentage', 0)
        bonds_amt = portfolio.get('bonds_amount', 0)
        cash_pct = portfolio.get('cash_percentage', 0)
        cash_amt = portfolio.get('cash_amount', 0)
        re_pct = portfolio.get('real_estate_percentage', 0)
        re_amt = portfolio.get('real_estate_amount', 0)
        alt_pct = portfolio.get('alternative_percentage', 0)
        alt_amt = portfolio.get('alternative_amount', 0)
        
        age = session_facts.get('age', 54)
        
        context = f"""PORTFOLIO OPTIMIZATION ANALYSIS:
Total Investable Assets: ${total_assets:,.0f}

CURRENT ALLOCATION vs AGE-APPROPRIATE TARGETS:
• Stocks: {stocks_pct:.1f}% (${stocks_amt:,.0f}) - Target for age {age}: {100-age:.0f}%
• Bonds: {bonds_pct:.1f}% (${bonds_amt:,.0f}) - Target: {age:.0f}%
• Real Estate: {re_pct:.1f}% (${re_amt:,.0f})
• Cash: {cash_pct:.1f}% (${cash_amt:,.0f}) - Optimal: 5-10%
• Alternatives: {alt_pct:.1f}% (${alt_amt:,.0f})"""

        # Analysis flags
        issues = []
        if cash_pct > 15:
            issues.append(f"CASH DRAG: {cash_pct:.1f}% cash allocation reducing long-term returns")
        if stocks_pct > (100 - age + 10):
            issues.append(f"HIGH EQUITY RISK: {stocks_pct:.1f}% stocks may be aggressive for age {age}")
        elif stocks_pct < (100 - age - 10):
            issues.append(f"CONSERVATIVE ALLOCATION: {stocks_pct:.1f}% stocks may limit growth potential")
        
        if re_pct > 30:
            issues.append(f"CONCENTRATION RISK: {re_pct:.1f}% real estate concentration")
        
        if issues:
            context += f"\n\nOPTIMIZATION OPPORTUNITIES:\n• " + "\n• ".join(issues)
        
        # Tax efficiency analysis
        retirement_ctx = smart_context.get('retirement_context', {})
        if retirement_ctx.get('completion_percentage', 0) > 100:
            context += f"\n\nTAX OPTIMIZATION: With retirement overfunded, focus on tax-efficient asset location and Roth conversions"
        
        return context
    
    def _build_goals_intent_context(self, smart_context: Dict, session_facts: Dict) -> str:
        """Build goals-specific context"""
        goals = smart_context.get('goals', [])
        
        if not goals:
            return "GOALS: No active goals"
        
        # Show top 2 goals
        context = "FINANCIAL GOALS:"
        for goal in goals[:2]:
            name = goal['name']
            current = goal['current_amount']
            target = goal['target_amount']
            progress = goal['progress_percent']
            context += f"\n- {name}: ${current:,.0f}/${target:,.0f} ({progress:.1f}%)"
        
        return context
    
    def _build_budget_intent_context(self, smart_context: Dict, session_facts: Dict) -> str:
        """Build budget-specific context"""
        income = smart_context.get('monthly_income', 0)
        expenses = smart_context.get('monthly_expenses', 0)
        surplus = smart_context.get('monthly_surplus', 0)
        
        savings_rate = (surplus / income * 100) if income > 0 else 0
        
        return f"""MONTHLY BUDGET:
INCOME: ${income:,.0f}
EXPENSES: ${expenses:,.0f}
SURPLUS: ${surplus:,.0f}
SAVINGS RATE: {savings_rate:.1f}%"""
    
    def _build_networth_intent_context(self, smart_context: Dict, session_facts: Dict) -> str:
        """Build net worth-specific context"""
        assets = smart_context.get('total_assets', 0)
        liabilities = smart_context.get('total_liabilities', 0)
        net_worth = smart_context.get('net_worth', 0)
        
        return f"""NET WORTH BREAKDOWN:
TOTAL ASSETS: ${assets:,.0f}
TOTAL LIABILITIES: ${liabilities:,.0f}
NET WORTH: ${net_worth:,.0f}"""
    
    def _build_supporting_context(self, smart_context: Dict) -> str:
        """Build supporting context that's nice to have but not critical"""
        supporting = []
        
        # Emergency fund status
        emergency = smart_context.get('emergency_analysis', {})
        if emergency and emergency.get('status') != 'UNKNOWN':
            supporting.append(f"EMERGENCY FUND: {emergency['status']}")
        
        # Top opportunity
        opportunities = smart_context.get('opportunities', [])
        if opportunities:
            top_opp = opportunities[0]
            supporting.append(f"TOP OPPORTUNITY: {top_opp['action']}")
        
        return " | ".join(supporting) if supporting else ""
    
    def _assemble_context(self, context_parts: List[Tuple[str, str]], max_chars: int) -> str:
        """Assemble context parts within character limit, prioritizing by importance"""
        
        # Always include core facts
        result_parts = []
        total_chars = 0
        
        for priority, content in context_parts:
            if not content:
                continue
                
            # Add separator if not first part
            separator = "\n\n" if result_parts else ""
            part_with_separator = separator + content
            
            # Check if adding this part would exceed limit
            if total_chars + len(part_with_separator) > max_chars:
                # If this is core facts, we must include it even if it exceeds limit
                if priority == "CORE":
                    result_parts.append(content)
                    total_chars += len(content)
                # For other parts, try to truncate or skip
                elif priority == "INTENT":
                    # Try to fit a truncated version
                    available_chars = max_chars - total_chars - len(separator)
                    if available_chars > 50:  # Minimum useful size
                        truncated = content[:available_chars-3] + "..."
                        result_parts.append(separator + truncated)
                        total_chars += len(separator + truncated)
                break
            else:
                result_parts.append(part_with_separator)
                total_chars += len(part_with_separator)
        
        final_context = "".join(result_parts)
        
        # Add context metadata
        final_context += f"\n\n[Context: {total_chars} chars, optimized for LLM]"
        
        return final_context
    
    def get_essential_facts_only(self, user_id: int, session_id: str, db: Session) -> str:
        """
        Get only the most essential facts (under 300 chars)
        For use when context must be minimal
        """
        try:
            session = self.session_service.get_or_create_session(user_id, session_id, db)
            smart_context = self.enhanced_service.build_smart_context(user_id)
            
            if 'error' in smart_context:
                return f"Data unavailable: {smart_context['error']}"
            
            # Ultra-minimal context
            name = session.core_facts.get('name', f"User {user_id}")
            net_worth = smart_context.get('net_worth', 0)
            monthly_surplus = smart_context.get('monthly_surplus', 0)
            
            retirement_ctx = smart_context.get('retirement_context', {})
            completion_pct = retirement_ctx.get('completion_percentage', 0)
            
            essential = f"{name}: ${net_worth:,.0f} net worth, ${monthly_surplus:,.0f}/mo surplus, {completion_pct:.1f}% retirement funded"
            
            # Add critical retirement status if relevant
            if retirement_ctx.get('can_retire_early'):
                essential += " (can retire early)"
            elif retirement_ctx.get('surplus_deficit', 0) > 0:
                essential += " (ahead of schedule)"
            
            return essential
            
        except Exception as e:
            logger.error(f"Error building essential facts for user {user_id}: {str(e)}")
            return f"Essential facts unavailable: {str(e)}"


# Global instance
streamlined_context_service = StreamlinedContextService()