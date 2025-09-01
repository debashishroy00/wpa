"""
CorePrompts: Three essential prompts for Tax, Risk, and Goals.
Guide LLM to produce grounded, actionable insights.
"""

class CorePrompts:
    """Financial analysis prompt templates"""
    
    TAX_OPTIMIZATION = """
You are analyzing verified financial data for tax optimization.

FACTS (all numbers are real):
{claims}

CONTEXT:
Age: {age}
State: {state}
Filing Status: {filing_status}

RULES (from knowledge base):
{tax_rules}

Analyze for:
1. Asset location optimization
2. Contribution strategies
3. Tax-loss harvesting opportunities
4. Deduction optimization

Use ONLY numbers from FACTS. State assumptions explicitly.
Format: Problem → Impact → Action → Savings
"""

    RISK_ASSESSMENT = """
You are assessing portfolio risk using verified data.

FACTS (all numbers are real):
{claims}

ALLOCATION:
{allocation_data}

Identify:
1. Concentration risks
2. Liquidity gaps
3. Volatility concerns

Base all statements on FACTS provided.
"""

    GOAL_PROGRESS = """
You are tracking financial goal progress.

FACTS (all numbers are real):
{claims}

GOALS:
{user_goals}

Calculate:
1. Current trajectory
2. Gap analysis
3. Required adjustments

Use only verified FACTS for calculations.
"""

    def format_prompt(self, prompt_type: str, **kwargs) -> str:
        """Format prompt with provided data"""
        prompts = {
            "tax": self.TAX_OPTIMIZATION,
            "risk": self.RISK_ASSESSMENT, 
            "goals": self.GOAL_PROGRESS
        }
        
        template = prompts.get(prompt_type, self.TAX_OPTIMIZATION)
        
        # Safe formatting with defaults
        return template.format(
            claims=kwargs.get('claims', {}),
            age=kwargs.get('age', 'unknown'),
            state=kwargs.get('state', 'unknown'),
            filing_status=kwargs.get('filing_status', 'unknown'),
            tax_rules=kwargs.get('tax_rules', 'Standard deduction: $14,600 (single)'),
            allocation_data=kwargs.get('allocation_data', {}),
            user_goals=kwargs.get('user_goals', {})
        )

# Global instance
core_prompts = CorePrompts()