"""
Financial Intent Detection Service
Detects what users are really asking about and provides targeted search terms
"""

from typing import Dict, List, Tuple
from enum import Enum
import structlog

logger = structlog.get_logger()

class FinancialIntent(Enum):
    RETIREMENT = "retirement"
    DEBT_MANAGEMENT = "debt"
    INVESTMENT = "investment"
    TAX_PLANNING = "tax"
    BUDGET = "budget"
    EMERGENCY_FUND = "emergency"
    INSURANCE = "insurance"
    ESTATE_PLANNING = "estate"
    EDUCATION = "education"
    REAL_ESTATE = "real_estate"
    CASH_FLOW = "cash_flow"
    NET_WORTH = "net_worth"
    SAVINGS = "savings"
    GOAL_PLANNING = "goal_planning"
    GENERAL = "general"

class IntentService:
    """Detect financial intent and provide targeted search strategies"""
    
    def __init__(self):
        self.intent_patterns = {
            FinancialIntent.RETIREMENT: {
                "keywords": [
                    "retire", "retirement", "401k", "ira", "social security", "pension",
                    "roth", "traditional", "withdrawal", "nest egg", "retire early",
                    "financial independence", "fire", "medicare"
                ],
                "search_terms": [
                    "retirement accounts 401k ira",
                    "social security benefits pension",
                    "age retirement timeline",
                    "monthly surplus savings",
                    "investment returns allocation"
                ],
                "required_context": ["retirement_savings", "age", "social_security", "monthly_surplus"]
            },
            
            FinancialIntent.DEBT_MANAGEMENT: {
                "keywords": [
                    "debt", "loan", "mortgage", "credit card", "pay off", "interest",
                    "refinance", "consolidate", "payoff", "balance", "minimum payment",
                    "snowball", "avalanche", "credit score"
                ],
                "search_terms": [
                    "credit card debt interest rates",
                    "mortgage balance payments",
                    "loan terms minimum payments",
                    "debt to income ratio",
                    "monthly surplus available"
                ],
                "required_context": ["all_debts", "interest_rates", "minimum_payments", "monthly_income"]
            },
            
            FinancialIntent.INVESTMENT: {
                "keywords": [
                    "invest", "portfolio", "stocks", "bonds", "allocation", "returns",
                    "diversification", "rebalance", "etf", "mutual fund", "index",
                    "risk tolerance", "asset allocation", "dividend", "growth"
                ],
                "search_terms": [
                    "investment accounts portfolio",
                    "asset allocation stocks bonds",
                    "risk tolerance investment timeline",
                    "current holdings returns",
                    "monthly surplus investing"
                ],
                "required_context": ["investment_accounts", "risk_tolerance", "allocation", "timeline"]
            },
            
            FinancialIntent.TAX_PLANNING: {
                "keywords": [
                    "tax", "deduction", "bracket", "filing", "refund", "write off",
                    "ira contribution", "401k contribution", "itemize", "standard",
                    "capital gains", "tax loss", "hsa", "state tax"
                ],
                "search_terms": [
                    "tax bracket filing status",
                    "deductions itemized standard",
                    "retirement contributions tax",
                    "state tax rate location",
                    "income tax strategy"
                ],
                "required_context": ["tax_bracket", "filing_status", "income", "deductions", "state"]
            },
            
            FinancialIntent.BUDGET: {
                "keywords": [
                    "budget", "spend", "expense", "save", "surplus", "cash flow",
                    "money going", "afford", "spending", "categories", "track",
                    "cut costs", "reduce expenses", "where money goes"
                ],
                "search_terms": [
                    "monthly income expenses",
                    "spending categories breakdown",
                    "monthly surplus savings rate",
                    "budget tracking expenses",
                    "cash flow analysis"
                ],
                "required_context": ["monthly_income", "monthly_expenses", "spending_categories", "surplus"]
            },
            
            FinancialIntent.EMERGENCY_FUND: {
                "keywords": [
                    "emergency", "safety net", "cushion", "reserves", "rainy day",
                    "emergency fund", "liquid savings", "months coverage",
                    "unexpected expenses", "job loss"
                ],
                "search_terms": [
                    "emergency fund cash reserves",
                    "liquid savings accounts",
                    "monthly expenses coverage",
                    "cash bank accounts available",
                    "savings rate emergency"
                ],
                "required_context": ["cash_accounts", "monthly_expenses", "emergency_fund"]
            },
            
            FinancialIntent.EDUCATION: {
                "keywords": [
                    "college", "education", "529", "tuition", "student",
                    "school", "university", "education savings", "student loans",
                    "college fund", "education costs"
                ],
                "search_terms": [
                    "529 education savings plan",
                    "college tuition costs",
                    "student loans education debt",
                    "family members children age",
                    "education goals savings"
                ],
                "required_context": ["529_accounts", "family_members", "education_goals"]
            },
            
            FinancialIntent.REAL_ESTATE: {
                "keywords": [
                    "house", "home", "property", "real estate", "rent", "buy",
                    "mortgage", "down payment", "closing costs", "home value",
                    "refinance", "equity", "rental"
                ],
                "search_terms": [
                    "home property real estate value",
                    "mortgage balance payments",
                    "down payment savings",
                    "real estate investments",
                    "rental income property"
                ],
                "required_context": ["real_estate", "mortgage", "home_value", "rental_income"]
            },
            
            FinancialIntent.NET_WORTH: {
                "keywords": [
                    "net worth", "wealth", "assets", "financial health", "worth",
                    "total assets", "liabilities", "financial status", "financial picture"
                ],
                "search_terms": [
                    "total assets breakdown",
                    "total liabilities debt",
                    "net worth calculation",
                    "asset allocation summary",
                    "financial health metrics"
                ],
                "required_context": ["total_assets", "total_liabilities", "net_worth", "asset_breakdown"]
            },
            
            FinancialIntent.CASH_FLOW: {
                "keywords": [
                    "cash flow", "monthly income", "take home", "surplus", "deficit",
                    "income vs expenses", "left over", "available money"
                ],
                "search_terms": [
                    "monthly income take home",
                    "monthly expenses breakdown",
                    "monthly surplus deficit",
                    "cash flow analysis",
                    "savings rate monthly"
                ],
                "required_context": ["monthly_income", "monthly_expenses", "surplus", "savings_rate"]
            },
            
            FinancialIntent.SAVINGS: {
                "keywords": [
                    "savings", "save", "saving", "savings rate", "savings account",
                    "high yield", "cd", "money market", "savings goal"
                ],
                "search_terms": [
                    "savings accounts balances",
                    "savings rate monthly",
                    "high yield accounts",
                    "monthly surplus available",
                    "savings goals targets"
                ],
                "required_context": ["savings_accounts", "savings_rate", "monthly_surplus", "goals"]
            },
            
            FinancialIntent.GOAL_PLANNING: {
                "keywords": [
                    "goal", "target", "planning", "achieve", "timeline", "milestone",
                    "financial goal", "future", "plan for", "save for"
                ],
                "search_terms": [
                    "financial goals targets",
                    "goal progress tracking",
                    "monthly surplus available",
                    "timeline achievement",
                    "savings rate goals"
                ],
                "required_context": ["goals", "target_amounts", "timelines", "monthly_surplus"]
            }
        }
    
    def detect_intent(self, question: str) -> Tuple[FinancialIntent, List[str], List[str]]:
        """
        Detect financial intent from user question
        Returns: (intent, search_terms, required_context)
        """
        question_lower = question.lower().strip()
        
        logger.info(f"🎯 Detecting intent for: '{question}'")
        
        # Score each intent based on keyword matches
        intent_scores = {}
        
        for intent, config in self.intent_patterns.items():
            score = 0
            matched_keywords = []
            
            for keyword in config["keywords"]:
                if keyword in question_lower:
                    # Give higher score for exact matches
                    if keyword == question_lower:
                        score += 10
                    elif question_lower.startswith(keyword):
                        score += 5
                    else:
                        score += 1
                    matched_keywords.append(keyword)
            
            if score > 0:
                intent_scores[intent] = {
                    "score": score,
                    "keywords": matched_keywords,
                    "config": config
                }
        
        # Get the highest scoring intent
        if intent_scores:
            best_intent = max(intent_scores.keys(), key=lambda x: intent_scores[x]["score"])
            config = intent_scores[best_intent]["config"]
            matched = intent_scores[best_intent]["keywords"]
            
            logger.info(f"🎯 Intent detected: {best_intent.value} (score: {intent_scores[best_intent]['score']}, keywords: {matched})")
            
            return best_intent, config["search_terms"], config["required_context"]
        
        # Default to general
        logger.info("🎯 No specific intent detected, using GENERAL")
        return FinancialIntent.GENERAL, ["financial summary net worth", "monthly income expenses"], ["financial_overview"]
    
    def get_context_priority(self, intent: FinancialIntent) -> Dict[str, int]:
        """
        Get priority weights for different types of context based on intent
        Higher number = higher priority
        """
        priorities = {
            FinancialIntent.RETIREMENT: {
                "retirement_accounts": 10,
                "social_security": 10,
                "age": 9,
                "monthly_surplus": 8,
                "investment_accounts": 7,
                "tax_info": 6,
                "goals": 5
            },
            FinancialIntent.DEBT_MANAGEMENT: {
                "credit_cards": 10,
                "mortgage": 10,
                "loans": 10,
                "interest_rates": 9,
                "monthly_surplus": 8,
                "debt_to_income": 7,
                "monthly_income": 6
            },
            FinancialIntent.INVESTMENT: {
                "investment_accounts": 10,
                "risk_tolerance": 9,
                "asset_allocation": 8,
                "monthly_surplus": 7,
                "age": 6,
                "goals": 5
            },
            FinancialIntent.BUDGET: {
                "monthly_expenses": 10,
                "monthly_income": 10,
                "spending_categories": 9,
                "monthly_surplus": 8,
                "savings_rate": 7
            },
            FinancialIntent.NET_WORTH: {
                "total_assets": 10,
                "total_liabilities": 10,
                "asset_breakdown": 9,
                "net_worth": 8,
                "monthly_surplus": 6
            }
        }
        
        return priorities.get(intent, {
            "financial_summary": 10,
            "monthly_surplus": 8,
            "net_worth": 7
        })
    
    def should_include_calculations(self, intent: FinancialIntent) -> bool:
        """Determine if this intent needs detailed calculations"""
        calculation_intents = {
            FinancialIntent.RETIREMENT,
            FinancialIntent.DEBT_MANAGEMENT,
            FinancialIntent.GOAL_PLANNING,
            FinancialIntent.TAX_PLANNING
        }
        return intent in calculation_intents