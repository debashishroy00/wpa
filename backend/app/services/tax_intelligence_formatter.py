"""
Tax Intelligence Formatter
Handles ONLY formatting of tax calculations into intelligent insights using LLM
Separates calculation logic from presentation logic
"""
import structlog
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from .tax_calculations import tax_calculations  # Use global instance
from .llm_service import llm_service  # Use global LLM service
from ..models.llm_models import LLMRequest

logger = structlog.get_logger()


class TaxIntelligenceFormatter:
    """Formats tax calculations into intelligent insights using LLM"""
    
    def __init__(self, db: Session):
        self.db = db
        # NO new LLM instance - use global service
        # All calculations done by global tax_calculations instance
    
    async def format_tax_insights(self, user_id: int, question: str, financial_context: Dict) -> str:
        """Format tax insights with real calculations and intelligent presentation"""
        
        try:
            # 1. Get REAL calculations from unified service
            calculations = tax_calculations.analyze_comprehensive_tax_opportunities(
                user_id=user_id,
                financial_context=financial_context,
                db=self.db
            )
            
            if 'error' in calculations:
                return self._format_error_response(calculations['error'])
                
            # Check if we actually have opportunities
            if not calculations.get('calculated_opportunities') or calculations.get('total_potential_savings', 0) <= 0:
                logger.warning(f"No tax opportunities found for user {user_id}")
                return self._format_fallback_response(financial_context)
            
            # 2. Use global LLM to format insights intelligently
            prompt = self._build_insight_prompt(calculations, question)
            
            llm_request = LLMRequest(
                provider='gemini',
                model_tier='dev', 
                system_prompt="You are a CPA and tax strategist. Format tax analysis into clear, actionable insights with specific dollar amounts.",
                user_prompt=prompt,
                temperature=0.2,
                max_tokens=1500
            )
            
            # Use global LLM service (no new instances)
            llm_response = await llm_service.generate(llm_request)
            ai_formatted_response = llm_response.content
            
            # 3. Combine AI formatting with structured real data
            final_response = self._structure_enhanced_response(calculations, ai_formatted_response)
            
            logger.info(f"Tax intelligence formatted successfully", 
                       user_id=user_id, 
                       opportunities_count=len(calculations.get('calculated_opportunities', [])))
            
            return final_response
            
        except Exception as e:
            logger.error(f"Tax intelligence formatting failed", error=str(e), user_id=user_id)
            # Try direct formatting without LLM
            try:
                calculations = tax_calculations.analyze_comprehensive_tax_opportunities(
                    user_id=user_id,
                    financial_context=financial_context,
                    db=self.db
                )
                if calculations.get('calculated_opportunities'):
                    return self._format_direct_response(calculations)
            except Exception as e2:
                logger.error(f"Direct formatting also failed", error=str(e2))
            
            return self._format_fallback_response(financial_context)
    
    def format_quick_opportunities(self, user_id: int, financial_summary: Dict) -> str:
        """Format quick tax opportunities for dashboard"""
        
        try:
            # Get real calculations (no hardcoding)
            opportunities = tax_calculations.get_quick_tax_opportunities(user_id, financial_summary)
            
            if not opportunities:
                return ""
            
            # Format with real numbers
            total_savings = sum(opp['potential_savings'] for opp in opportunities)
            
            response = f"\n\n📊 **TAX OPTIMIZATION OPPORTUNITIES:**\n\n"
            response += f"💰 **Potential Annual Savings: ${total_savings:,.0f}**\n\n"
            response += "**TOP RECOMMENDATIONS:**\n"
            
            for i, opp in enumerate(opportunities[:3], 1):
                difficulty_emoji = {'Easy': '🟢', 'Medium': '🟡', 'Complex': '🔴'}.get(opp['difficulty'], '🟡')
                response += f"{i}. **{opp['strategy']}** {difficulty_emoji}\n"
                response += f"   • Annual Savings: ${opp['potential_savings']:,.0f}\n"
                response += f"   • {opp['description']}\n"
            
            response += "\n**NEXT STEPS:**\n"
            response += "1. Review strategies with your tax professional\n"
            response += "2. Implement Easy (🟢) strategies immediately\n"
            response += "3. Plan Medium (🟡) strategies for year-end\n\n"
            response += "*All calculations based on your actual financial data and 2024 tax rules.*"
            
            return response
            
        except Exception as e:
            logger.error(f"Quick opportunities formatting failed", error=str(e), user_id=user_id)
            return ""
    
    def _build_insight_prompt(self, calculations: Dict, question: str) -> str:
        """Build intelligent prompt for LLM formatting"""
        
        opportunities = calculations.get('calculated_opportunities', [])
        total_savings = calculations.get('total_potential_savings', 0)
        profile = calculations.get('taxpayer_profile', {})
        
        prompt = f"""
        USER QUESTION: "{question}"
        
        TAX ANALYSIS RESULTS:
        Annual Income: ${profile.get('annual_income', 0):,.0f}
        Tax Bracket: {profile.get('tax_bracket', 24)}%
        Total Potential Savings: ${total_savings:,.0f}
        
        SPECIFIC OPPORTUNITIES FOUND:
        """
        
        for opp in opportunities:
            prompt += f"""
        • {opp['strategy']}: ${opp['annual_tax_savings']:,.0f} savings
          Priority: {opp['priority']}, Difficulty: {opp['difficulty']}
          Timeline: {opp['timeline']}
          Description: {opp['description']}
        """
        
        prompt += """
        
        FORMAT REQUIREMENTS:
        1. Answer the user's specific question first
        2. Present opportunities in order of savings amount
        3. Use exact dollar amounts from the calculations
        4. Include implementation timelines
        5. Keep response focused and actionable
        6. Use professional but accessible language
        """
        
        return prompt
    
    def _structure_enhanced_response(self, calculations: Dict, ai_response: str) -> str:
        """Combine AI formatting with structured data"""
        
        # Start with AI-formatted response
        enhanced_response = ai_response
        
        # Add structured opportunity summary
        opportunities = calculations.get('calculated_opportunities', [])
        total_savings = calculations.get('total_potential_savings', 0)
        
        if opportunities and total_savings > 0:
            enhanced_response += f"\n\n📊 **OPPORTUNITY SUMMARY:**\n"
            enhanced_response += f"💰 Total Annual Savings: ${total_savings:,.0f}\n"
            enhanced_response += f"🎯 Strategies Found: {len(opportunities)}\n\n"
            
            # Add top 3 opportunities with real numbers
            for i, opp in enumerate(opportunities[:3], 1):
                difficulty_emoji = {'Easy': '🟢', 'Medium': '🟡', 'Complex': '🔴'}.get(opp['difficulty'], '🟡')
                enhanced_response += f"{i}. **{opp['strategy']}** {difficulty_emoji} - ${opp['annual_tax_savings']:,.0f}\n"
        
        return enhanced_response
    
    def _format_error_response(self, error_message: str) -> str:
        """Format error response"""
        return f"I encountered an issue analyzing your tax situation: {error_message}. Please ensure your financial profile is complete and try again."
    
    def _format_fallback_response(self, financial_context: Dict) -> str:
        """Fallback response when LLM fails"""
        annual_income = financial_context.get('monthly_income', 0) * 12
        
        if annual_income > 0:
            return f"""
            Based on your ${annual_income:,.0f} annual income, here are some general tax strategies to consider:
            
            • Maximize retirement contributions (401k/IRA)
            • Consider tax-loss harvesting if you have investments
            • Review itemization vs standard deduction
            • Plan charitable giving for tax benefits
            
            For specific calculations and personalized advice, please consult with a tax professional.
            """
        else:
            return "Please complete your financial profile to receive personalized tax optimization recommendations."
    
    def is_tax_question(self, message: str) -> bool:
        """Detect if message is tax-related"""
        tax_keywords = [
            'tax', 'deduction', 'irs', 'itemize', 'roth', '401k', 'ira', 
            'bracket', 'savings', 'retirement contribution', 'write-off',
            'refund', 'withholding', 'quarterly', 'estimated', 'charitable',
            'mortgage interest', 'property tax', 'salt', 'bunching',
            'harvest', 'loss', 'capital gains'
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in tax_keywords)


# Global instance for easy import
tax_intelligence_formatter = None  # Will be initialized when needed with db session