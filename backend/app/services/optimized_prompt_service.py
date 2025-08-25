"""
Optimized Prompt Service
Creates focused, effective prompts that ensure LLMs use provided financial data
Solves the prompt overload and context loss issues
"""
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class OptimizedPromptService:
    """
    Creates focused prompts that maximize LLM effectiveness with financial data
    """
    
    def build_focused_system_prompt(self, context: str, intent: str = "general") -> str:
        """
        Build a focused system prompt that ensures LLM uses provided context
        
        Args:
            context: Streamlined financial context (should be under 800 chars)
            intent: Financial intent (retirement, debt, investment, etc.)
            
        Returns:
            Optimized system prompt that maximizes LLM accuracy
        """
        
        # Professional-grade advisor identity
        base_prompt = """You are a senior fiduciary financial advisor with 20+ years of experience managing high-net-worth portfolios. You provide comprehensive, professional-grade analysis that surpasses typical human advisors through data-driven insights.

CLIENT FINANCIAL DATA:
{context}

PROFESSIONAL ANALYSIS REQUIREMENTS:
1. COMPREHENSIVE ASSESSMENT: Analyze ALL aspects of their financial position - not just surface-level observations
2. QUANTITATIVE PRECISION: Use exact numbers, calculate ratios, project scenarios with specific timelines
3. STRATEGIC INSIGHTS: Identify optimization opportunities, tax strategies, and wealth-building tactics
4. RISK ANALYSIS: Assess concentration risk, sequence of returns risk, inflation impact, and contingency planning
5. BENCHMARKING: Compare against age-appropriate benchmarks and top 10% performers
6. ACTIONABLE ROADMAP: Provide specific implementation steps with dollar amounts, account types, and deadlines

RESPONSE DEPTH STANDARDS:
- Lead with quantitative assessment (percentiles, ratios, projections)
- Analyze portfolio efficiency and tax optimization opportunities  
- Address sequence of returns risk and withdrawal strategies
- Identify estate planning and wealth transfer considerations
- Provide specific product recommendations (account types, allocation targets)
- Include stress testing and scenario analysis
- Give implementation timeline with measurable milestones

PROFESSIONAL TONE:
- Confident and authoritative based on data analysis
- Use financial industry terminology appropriately
- Provide insights that demonstrate deep expertise
- Be direct about both strengths and areas needing attention"""

        # Add intent-specific guidance
        intent_guidance = self._get_intent_guidance(intent)
        
        final_prompt = base_prompt.format(context=context)
        if intent_guidance:
            final_prompt += f"\n\nSPECIFIC GUIDANCE FOR {intent.upper()} QUESTIONS:\n{intent_guidance}"
        
        return final_prompt
    
    def _get_intent_guidance(self, intent: str) -> Optional[str]:
        """Get specific guidance for different financial intents"""
        
        guidance_map = {
            "retirement": """RETIREMENT ANALYSIS DEPTH:
- Calculate precise withdrawal rates and sequence of returns risk
- Analyze Social Security optimization strategies (claiming timing, spousal benefits)
- Assess geographic arbitrage opportunities and tax-efficient withdrawal sequencing
- Evaluate Roth conversion ladders and tax diversification strategies
- Project healthcare costs and long-term care insurance needs
- Analyze estate planning implications and wealth transfer strategies
- Consider early retirement feasibility with bridge strategies
- Evaluate pension maximization and lump-sum vs annuity decisions""",
            
            "debt": """DEBT OPTIMIZATION ANALYSIS:
- Calculate opportunity cost of debt payoff vs investment returns
- Analyze tax deductibility and after-tax cost of debt
- Evaluate refinancing opportunities and rate arbitrage
- Consider debt consolidation and balance transfer strategies
- Assess impact on credit utilization and credit score optimization
- Analyze cash flow impact and liquidity preservation
- Evaluate mortgage acceleration vs investment allocation
- Consider strategic use of leverage for tax-advantaged investments""",
            
            "investment": """PORTFOLIO OPTIMIZATION ANALYSIS:
- Analyze asset location efficiency (tax-advantaged vs taxable accounts)
- Evaluate factor exposure (value, growth, momentum, quality, size)
- Assess geographic and sector diversification gaps
- Calculate tax-loss harvesting opportunities and wash sale implications
- Analyze expense ratios and fee drag on long-term returns
- Evaluate rebalancing strategies and tax-efficient implementation
- Consider alternative investments and correlation benefits
- Assess ESG integration and impact investing opportunities
- Analyze options strategies for income generation and downside protection""",
            
            "budget": """- Calculate savings rate: monthly surplus ÷ monthly income × 100
- A 20%+ savings rate is excellent, 10-20% is good, <10% needs improvement
- Identify specific areas where they can optimize spending
- Recommend automatic savings to reach target rates""",
            
            "goals": """- Calculate monthly savings needed: (target - current) ÷ months remaining
- Prioritize goals by importance and timeline
- If they have surplus income, show how to accelerate goal achievement
- Be realistic about what's achievable with their current cash flow""",
            
            "net_worth": """- Break down net worth into assets and liabilities
- Compare to age-based benchmarks if appropriate
- Identify opportunities to increase assets or reduce liabilities
- Show how net worth growth compounds over time"""
        }
        
        return guidance_map.get(intent.lower())
    
    def build_user_message_enhancement(self, original_message: str, context_summary: str) -> str:
        """
        Enhance user message with context hints to improve LLM focus
        
        Args:
            original_message: User's original question
            context_summary: Brief summary of their financial situation
            
        Returns:
            Enhanced message that helps LLM stay focused on user's data
        """
        
        # Add context hint to help LLM focus
        enhanced = f"""Question: {original_message}

Context: {context_summary}

Please answer based on my specific financial situation shown in the data above."""
        
        return enhanced
    
    def validate_prompt_effectiveness(self, system_prompt: str, user_message: str) -> Dict[str, Any]:
        """
        Validate that the prompt is likely to be effective
        
        Returns:
            Dictionary with validation results and suggestions
        """
        
        issues = []
        suggestions = []
        
        # Check prompt length
        total_length = len(system_prompt) + len(user_message)
        if total_length > 2000:
            issues.append("Prompt may be too long for optimal LLM performance")
            suggestions.append("Consider reducing context to under 800 characters")
        
        # Check for specific financial data
        if not any(char in system_prompt for char in ['$', '%']):
            issues.append("No specific financial numbers found in prompt")
            suggestions.append("Ensure context includes actual dollar amounts and percentages")
        
        # Check for user identification
        if "name" not in system_prompt.lower() and "client" not in system_prompt.lower():
            issues.append("User not clearly identified in prompt")
            suggestions.append("Include user's name or clear identification")
        
        # Check for actionable guidance
        required_elements = ["specific", "dollar", "recommend"]
        missing_elements = [elem for elem in required_elements if elem not in system_prompt.lower()]
        if missing_elements:
            issues.append(f"Missing guidance for: {', '.join(missing_elements)}")
            suggestions.append("Add instructions for specific, actionable recommendations")
        
        return {
            "is_effective": len(issues) == 0,
            "total_length": total_length,
            "issues": issues,
            "suggestions": suggestions,
            "score": max(0, 100 - len(issues) * 20)  # Simple scoring system
        }
    
    def create_fallback_prompt(self, user_name: str = "Client") -> str:
        """
        Create a minimal fallback prompt when context is unavailable
        """
        
        return f"""You are a financial advisor helping {user_name}.

I don't have access to your complete financial data right now. To provide the best advice, I'll need some information from you.

Could you share:
- Your current financial goal or concern
- Your approximate age and income level
- Any specific numbers you'd like me to analyze

I'll provide general guidance and help you think through your financial decisions."""
    
    def optimize_for_provider(self, base_prompt: str, provider: str) -> str:
        """
        Optimize prompt for specific LLM provider characteristics
        
        Args:
            base_prompt: Base system prompt
            provider: LLM provider (openai, gemini, claude)
            
        Returns:
            Provider-optimized prompt
        """
        
        if provider.lower() == "claude":
            # Claude responds well to structured instructions
            return f"{base_prompt}\n\nPlease structure your response with clear sections and specific recommendations."
        
        elif provider.lower() == "gemini":
            # Gemini benefits from explicit instruction emphasis
            return f"{base_prompt}\n\nIMPORTANT: Base all calculations and advice on the specific financial data provided above."
        
        elif provider.lower() == "openai":
            # GPT models work well with role-based prompts
            return f"As a professional financial advisor, {base_prompt.lower()}"
        
        else:
            # Default optimization
            return base_prompt


# Global instance
optimized_prompt_service = OptimizedPromptService()