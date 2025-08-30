"""
DEPRECATED - retirement_response_template.py
This file is deprecated due to:
1. Indentation issues causing backend crashes
2. Overly complex data extraction logic
3. Hardcoded values and poor scalability
4. Inconsistent empty state handling

REPLACEMENT: retirement_response_formatter.py
Use the new simplified formatter instead.
"""

import re
from typing import Dict, Any, Optional, List
import structlog
from datetime import datetime

logger = structlog.get_logger()


class RetirementPlanningTemplate:
    """
    Conversational response enhancement for retirement planning queries.
    Enhances LLM outputs with accurate metrics in a natural, flowing format.
    """
    
    def __init__(self):
        self.retirement_keywords = [
            'retirement', 'retire', 'retiring', '401k', '401(k)', 'ira', 'roth',
            'pension', 'social security', 'nest egg', 'retirement savings',
            'retirement planning', 'when can i retire', 'retirement age',
            'retirement fund', 'retirement account', 'retirement goal'
        ]
    
    def format_response(self, llm_output: str, calculations: Dict[str, Any], user_context: Dict[str, Any]) -> str:
        """
        Enhance retirement planning response with conversational formatting and accurate metrics
        
        Args:
            llm_output: Raw LLM response text
            calculations: Financial calculations from backend
            user_context: User profile and financial data
            
        Returns:
            Conversationally enhanced response with embedded metrics
        """
        try:
            # If LLM output already contains good information, enhance it conversationally
            if llm_output and len(llm_output) > 100:
                return self._enhance_existing_response(llm_output, calculations, user_context)
            else:
                # Create new conversational response if LLM output is insufficient
                return self._create_conversational_response(calculations, user_context)
                
        except Exception as e:
            logger.error("Error formatting retirement response", error=str(e))
            # Return original response if enhancement fails
            return llm_output
    
    def _enhance_existing_response(self, llm_output: str, calculations: Dict[str, Any], user_context: Dict[str, Any]) -> str:
        """Enhance existing LLM response with accurate metrics"""
        
        # Extract actual values from calculations
        retirement_savings = calculations.get('retirement_assets', 0)
        monthly_income = calculations.get('monthly_income', 0)
        monthly_expenses = calculations.get('monthly_expenses', 0)
        net_worth = calculations.get('net_worth', 0)
        savings_rate = calculations.get('savings_rate', 0)
        
        # Calculate retirement goal if not provided
        retirement_goal = calculations.get('retirement_goal', monthly_expenses * 12 * 25) if monthly_expenses > 0 else 3500000
        
        # Replace common incorrect patterns with accurate data
        replacements = [
            # Fix retirement savings mentions
            (r'\$0 in retirement', f'**${retirement_savings:,.0f}** in retirement assets'),
            (r'Current Savings: \$0', f'Current Savings: **${retirement_savings:,.0f}**'),
            (r'retirement savings of \$0', f'retirement savings of **${retirement_savings:,.0f}**'),
            
            # Fix savings rate
            (r'\d+\.?\d*%?\s*savings rate', f'**{savings_rate:.1f}%** savings rate'),
            
            # Fix net worth
            (r'net worth of \$[\d,]+', f'net worth of **${net_worth:,.0f}**'),
            
            # Fix retirement goal
            (r'goal of \$[\d,]+(?:\.\d+)?[MK]?', f'goal of **${retirement_goal:,.0f}**'),
        ]
        
        enhanced = llm_output
        for pattern, replacement in replacements:
            enhanced = re.sub(pattern, replacement, enhanced, flags=re.IGNORECASE)
        
        # Remove template artifacts and excessive formatting
        enhanced = re.sub(r'##\s*[🎯📊💡📅📈]\s*', '', enhanced)  # Remove emoji headers
        enhanced = re.sub(r'\*\*\d+\.\*\*\s*', '', enhanced)  # Remove numbered bold markers
        enhanced = re.sub(r'^-\s*', '', enhanced, flags=re.MULTILINE)  # Remove bullet points
        enhanced = re.sub(r'\n{3,}', '\n\n', enhanced)  # Fix excessive line breaks
        
        return enhanced
    
    def _create_conversational_response(self, calculations: Dict[str, Any], user_context: Dict[str, Any]) -> str:
        """Create a new conversational response when LLM output is insufficient"""
        
        # Extract key metrics with defaults
        retirement_assets = calculations.get('retirement_assets', 0)
        monthly_income = calculations.get('monthly_income', 0) 
        monthly_expenses = calculations.get('monthly_expenses', 0)
        net_worth = calculations.get('net_worth', 0)
        savings_rate = calculations.get('savings_rate', 0)
        emergency_months = calculations.get('emergency_months', 0)
        debt_to_income = calculations.get('debt_to_income', 0)
        
        # Calculate derived metrics - use 25x rule or reasonable default based on expenses
        retirement_goal = calculations.get('retirement_goal', monthly_expenses * 12 * 25) if monthly_expenses > 0 else monthly_income * 12 * 20 if monthly_income > 0 else 1000000
        progress_percentage = (retirement_assets / retirement_goal * 100) if retirement_goal > 0 else 0
        monthly_savings = monthly_income - monthly_expenses if monthly_income > 0 and monthly_expenses > 0 else 0
        
        # Build conversational response
        response_parts = []
        
        # Opening assessment
        if progress_percentage >= 50:
            response_parts.append(f"Based on your current financial situation, you're actually in excellent shape for retirement. You have **${retirement_assets:,.0f}** in retirement-related investments, which represents about **{progress_percentage:.0f}% of your ${retirement_goal:,.0f} goal**.")
        elif progress_percentage >= 25:
            response_parts.append(f"You're making solid progress toward retirement. With **${retirement_assets:,.0f}** saved, you're about **{progress_percentage:.0f}% of the way to your ${retirement_goal:,.0f} target**.")
        else:
            response_parts.append(f"Let's look at your retirement planning. You currently have **${retirement_assets:,.0f}** saved toward your retirement goal of **${retirement_goal:,.0f}**.")
        
        # Savings rate assessment
        if savings_rate > 0:
            response_parts.append(f"\nWith your current **{savings_rate:.1f}% savings rate**, you're saving approximately **${monthly_savings:,.0f} per month**.")
            
            if savings_rate >= 40:
                response_parts.append("This exceptional savings rate puts you well ahead of most people and suggests you could potentially retire earlier than planned.")
            elif savings_rate >= 20:
                response_parts.append("This is a strong savings rate that should help you reach your retirement goals on schedule.")
            elif savings_rate >= 10:
                response_parts.append("This is a decent savings rate, though increasing it could help you reach your goals faster.")
        
        # Financial health indicators
        if emergency_months > 0 or debt_to_income < 50:
            health_points = []
            if emergency_months >= 6:
                health_points.append(f"your emergency fund covers **{emergency_months:.0f} months of expenses**")
            if debt_to_income < 20:
                health_points.append(f"your debt-to-income ratio is just **{debt_to_income:.1f}%**")
            
            if health_points:
                response_parts.append(f"\nThe key metrics that stand out: {' and '.join(health_points)}. This strong foundation gives you flexibility in your retirement planning.")
        
        # Recommendations based on situation
        if savings_rate >= 30:
            response_parts.append("\nI'd suggest considering whether you want to retire earlier than planned, given your aggressive savings rate, or if you'd prefer to dial back savings slightly and enjoy more of your current income.")
        elif progress_percentage < 25 and savings_rate < 15:
            response_parts.append("\nTo accelerate your retirement savings, consider increasing your monthly contributions if possible, especially if you have access to employer matching in a 401(k) plan.")
        else:
            response_parts.append("\nYou're on a good trajectory. Keep maintaining your current savings discipline while periodically reviewing your investment allocation to ensure it aligns with your timeline.")
        
        return '\n'.join(response_parts)
    
    def is_retirement_query(self, query: str) -> bool:
        """Detect if query is retirement-related"""
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in self.retirement_keywords)