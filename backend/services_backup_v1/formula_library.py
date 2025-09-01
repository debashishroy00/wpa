"""
Financial Formula Library
Dynamic injection of relevant financial formulas based on user intent
"""
import re
from typing import Dict, List, Optional
import structlog
from ..utils.safe_conversion import safe_float

logger = structlog.get_logger()

class FormulaLibrary:
    """Inject relevant formulas based on intent and context"""
    
    def __init__(self):
        self.FORMULAS = {
            'retirement': {
                'formulas': [
                    "4% Rule: Portfolio_Needed = Annual_Expenses ÷ 0.04",
                    "FIRE Number: 25 × Annual_Expenses (inverse of 4% rule)",
                    "Years to Retirement Goal: log(Goal ÷ Current) ÷ log(1 + Return_Rate)",
                    "Retirement Income: Portfolio_Size × Withdrawal_Rate",
                    "Required Monthly Savings: (Goal - Current) ÷ [((1+r)^months - 1) ÷ r]"
                ],
                'examples': [
                    "If monthly expenses are $5,000: $5,000 × 12 ÷ 0.04 = $1,500,000 needed",
                    "FIRE at $60k/year expenses: $60,000 × 25 = $1,500,000 portfolio",
                    "From $100k to $1.5M at 7%: log(1500000÷100000) ÷ log(1.07) = 40.7 years"
                ]
            },
            'investment': {
                'formulas': [
                    "Future Value: FV = PV × (1 + r)^years",
                    "With Monthly Deposits: FV = PV(1+r)^n + PMT[((1+r)^n - 1)/r]",
                    "Real Return: (1 + Nominal_Rate) ÷ (1 + Inflation_Rate) - 1",
                    "Required Return: (Goal ÷ Present_Value)^(1/years) - 1",
                    "Monthly Investment Needed: Goal × r ÷ [((1+r)^months - 1)]"
                ],
                'examples': [
                    "$10,000 at 7% for 10 years: $10,000 × (1.07)^10 = $19,672",
                    "$500/month for 20 years at 7%: $500 × [((1.07)^20 - 1) ÷ 0.07] = $244,382",
                    "Real return: 10% nominal, 3% inflation: (1.10 ÷ 1.03) - 1 = 6.8%"
                ]
            },
            'debt': {
                'formulas': [
                    "Payoff Time: -log(1 - (rate × balance ÷ payment)) ÷ log(1 + rate)",
                    "Total Interest: (Payment × Months) - Principal",
                    "Interest Savings: Original_Interest - New_Interest",
                    "Debt Avalanche: Pay minimums + extra to highest rate first",
                    "Debt Snowball: Pay minimums + extra to smallest balance first"
                ],
                'examples': [
                    "$5,000 at 18% APR with $200/month: 32 months to payoff",
                    "Total interest: ($200 × 32) - $5,000 = $1,400",
                    "Double payments cut time: 32 months → 16 months, save $700"
                ]
            },
            'cash_flow': {
                'formulas': [
                    "Savings Rate: (Income - Expenses) ÷ Income × 100",
                    "Emergency Fund Months: Emergency_Fund ÷ Monthly_Expenses",
                    "Net Cash Flow: Total_Income - Total_Expenses",
                    "Debt-to-Income Ratio: Total_Debt_Payments ÷ Gross_Income",
                    "Free Cash Flow: Net_Income - Essential_Expenses - Debt_Payments"
                ],
                'examples': [
                    "$8,000 income, $6,000 expenses: ($8,000 - $6,000) ÷ $8,000 = 25% savings rate",
                    "$30,000 emergency fund, $5,000 monthly expenses: 6 months coverage",
                    "$2,000 debt payments on $8,000 income: 25% debt-to-income ratio"
                ]
            },
            'tax': {
                'formulas': [
                    "Tax Savings: Contribution × Marginal_Tax_Rate",
                    "After-Tax Return: Pre_Tax_Return × (1 - Tax_Rate)",
                    "Tax-Equivalent Yield: Municipal_Rate ÷ (1 - Tax_Rate)",
                    "Traditional vs Roth: Current_Tax_Rate vs Retirement_Tax_Rate",
                    "Effective Tax Rate: Total_Tax ÷ Total_Income"
                ],
                'examples': [
                    "$6,000 401k at 24% bracket: $6,000 × 0.24 = $1,440 tax savings",
                    "7% taxable at 24% bracket: 7% × (1 - 0.24) = 5.32% after-tax",
                    "3% municipal for 24% bracket: 3% ÷ (1 - 0.24) = 3.95% equivalent"
                ]
            },
            'insurance': {
                'formulas': [
                    "Life Insurance Need: 10-12 × Annual_Income",
                    "Income Replacement: 70-80% of current income needed",
                    "Disability Coverage: 60-70% of gross income",
                    "Premium as % of Income: Annual_Premium ÷ Annual_Income",
                    "Coverage Gap: Needed_Coverage - Current_Coverage"
                ],
                'examples': [
                    "$100k income needs $1M-$1.2M life insurance",
                    "$8,000 monthly income needs $5,600-$6,400 disability coverage",
                    "$2,000 premium on $100k income = 2% of income"
                ]
            }
        }
    
    def detect_calculation_topics(self, message: str) -> List[str]:
        """Detect which calculation topics are relevant to the message"""
        message_lower = message.lower()
        topics = []
        
        # Retirement keywords
        if any(word in message_lower for word in ['retire', 'retirement', 'fire', '4%', 'withdraw', 'nest egg']):
            topics.append('retirement')
        
        # Investment keywords
        if any(word in message_lower for word in ['invest', 'return', 'compound', 'growth', 'portfolio', 'future value']):
            topics.append('investment')
        
        # Debt keywords
        if any(word in message_lower for word in ['debt', 'loan', 'payoff', 'interest', 'mortgage', 'credit']):
            topics.append('debt')
        
        # Cash flow keywords
        if any(word in message_lower for word in ['savings rate', 'emergency fund', 'cash flow', 'income', 'expenses']):
            topics.append('cash_flow')
        
        # Tax keywords
        if any(word in message_lower for word in ['tax', '401k', 'ira', 'roth', 'deduction', 'bracket']):
            topics.append('tax')
        
        # Insurance keywords
        if any(word in message_lower for word in ['insurance', 'life insurance', 'disability', 'coverage']):
            topics.append('insurance')
        
        return topics if topics else ['investment']  # Default to investment
    
    def get_relevant_formulas(self, topics: List[str]) -> str:
        """Get formulas for specific topics"""
        if not topics:
            return ""
        
        formula_sections = []
        
        for topic in topics[:3]:  # Limit to 3 topics to avoid overwhelming
            if topic in self.FORMULAS:
                data = self.FORMULAS[topic]
                section = f"\n📊 {topic.upper().replace('_', ' ')} FORMULAS:\n"
                
                # Add formulas
                for formula in data['formulas']:
                    section += f"• {formula}\n"
                
                # Add examples
                section += f"\nEXAMPLES:\n"
                for example in data['examples']:
                    section += f"• {example}\n"
                
                formula_sections.append(section)
        
        if formula_sections:
            return "\n" + "\n".join(formula_sections)
        
        return ""
    
    def extract_numbers_from_message(self, message: str) -> Dict:
        """Extract numerical values and percentages from user message"""
        extracted = {}
        
        # Extract percentages
        percentages = re.findall(r'(\d+(?:\.\d+)?)%', message)
        if percentages:
            extracted['percentages'] = [safe_float(p, 0) for p in percentages if p.strip()]
        
        # Extract dollar amounts
        dollar_amounts = re.findall(r'\$?([\d,]+(?:\.\d{2})?)', message)
        if dollar_amounts:
            extracted['amounts'] = [safe_float(amt.replace(',', ''), 0) for amt in dollar_amounts if amt.strip()]
        
        # Extract years
        years = re.findall(r'(\d+)\s*(?:years?|yrs?)', message.lower())
        if years:
            extracted['years'] = [int(y) for y in years]
        
        # Detect common rules
        rules_detected = []
        if '4% rule' in message.lower() or 'four percent rule' in message.lower():
            rules_detected.append('4_percent_rule')
            extracted['withdrawal_rate'] = 0.04
        
        if '10x' in message.lower() or '10 times' in message.lower():
            rules_detected.append('10x_income_rule')
        
        if rules_detected:
            extracted['rules'] = rules_detected
        
        return extracted
    
    def create_calculation_context(self, message: str, user_data: Dict) -> str:
        """Create enhanced context for calculations"""
        topics = self.detect_calculation_topics(message)
        formulas = self.get_relevant_formulas(topics)
        numbers = self.extract_numbers_from_message(message)
        
        # Safely format user data with proper defaults
        monthly_income = safe_float(user_data.get('monthly_income'), 0.0)
        monthly_expenses = safe_float(user_data.get('monthly_expenses'), 0.0)
        total_assets = safe_float(user_data.get('total_assets'), 0.0)
        investment_total = safe_float(user_data.get('investment_total'), 0.0)
        age = user_data.get('age', 'Unknown')
        
        context = f"""
CALCULATION CONTEXT:
• Topics detected: {', '.join(topics)}
• Numbers in message: {numbers}
• User's key financial data:
  - Monthly Income: ${monthly_income:,.0f}
  - Monthly Expenses: ${monthly_expenses:,.0f}
  - Total Assets: ${total_assets:,.0f}
  - Investment Portfolio: ${investment_total:,.0f}
  - Age: {age}
{formulas}

CALCULATION INSTRUCTIONS:
1. Use the user's actual financial data in calculations
2. Show step-by-step work with clear formulas
3. Format results with proper currency symbols and commas
4. Explain what each calculation means in practical terms
5. Round appropriately (dollars to nearest dollar, percentages to 1 decimal)
"""
        
        return context
    
    def get_formula_for_intent(self, intent: str, specific_calculation: str = None) -> Optional[str]:
        """Get specific formula for a given intent and calculation type"""
        intent_mapping = {
            'retirement': 'retirement',
            'allocation': 'investment',
            'debt': 'debt',
            'returns': 'investment',
            'cash_flow': 'cash_flow',
            'tax': 'tax',
            'real_estate': 'investment',
            'emergency': 'cash_flow',
            'risk': 'investment'
        }
        
        formula_topic = intent_mapping.get(intent, 'investment')
        
        if formula_topic in self.FORMULAS:
            formulas = self.FORMULAS[formula_topic]['formulas']
            if specific_calculation:
                # Try to find most relevant formula
                for formula in formulas:
                    if specific_calculation.lower() in formula.lower():
                        return formula
            return formulas[0]  # Return first formula as default
        
        return None

# Global formula library instance
formula_library = FormulaLibrary()