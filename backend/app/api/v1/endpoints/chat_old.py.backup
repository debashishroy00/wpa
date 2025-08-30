"""
Chat API Endpoints
Handles intelligent financial advisor chat with vector database context
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid
import structlog
import json

from app.db.session import get_db
from app.models.user import User
from app.api.v1.endpoints.auth import get_current_active_user
from app.services.vector_db_service import FinancialVectorDB
from app.api.v1.endpoints.financial_clean import get_comprehensive_summary
from app.services.enhanced_context_service import EnhancedContextService
from app.services.financial_calculator import FinancialCalculator
from app.models.goals_v2 import Goal, GoalProgress, UserPreferences
from app.models.financial import FinancialEntry, EntryCategory, FrequencyType
from app.models.user_profile import UserProfile, FamilyMember, UserBenefit, UserTaxInfo
from sqlalchemy import func, desc, and_
from decimal import Decimal

# Initialize services
vector_db_instance = None
context_service = EnhancedContextService()
calculator = FinancialCalculator()


def get_vector_db():
    """Get vector database instance"""
    global vector_db_instance
    if vector_db_instance is None:
        try:
            vector_db_instance = FinancialVectorDB()
            logger.info("Vector database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize vector database: {str(e)}")
            raise e
    return vector_db_instance

logger = structlog.get_logger()

router = APIRouter()

def build_smart_financial_context(user_id: int, db: Session = None, intent: str = "general", 
                                 session_id: str = None, use_streamlined: bool = True) -> str:
    """
    Build optimized financial context for AI advisor
    Uses streamlined context service to prevent data loss and ensure critical facts reach LLM
    """
    try:
        if use_streamlined and session_id:
            # Use new streamlined context service
            from app.services.streamlined_context_service import streamlined_context_service
            
            logger.info(f"Building streamlined context for user {user_id}, intent: {intent}")
            context = streamlined_context_service.get_priority_context(
                user_id=user_id,
                session_id=session_id,
                db=db,
                intent=intent,
                max_chars=800  # Optimal size for LLM focus
            )
            
            logger.info(f"Streamlined context built: {len(context)} characters")
            return context
        
        # Fallback to legacy comprehensive context (for backward compatibility)
        logger.info(f"Using legacy comprehensive context for user {user_id}")
        return build_legacy_comprehensive_context(user_id, db)
        
    except Exception as e:
        logger.error(f"Error building smart context for user {user_id}: {str(e)}")
        # Emergency fallback - get essential facts only
        try:
            if session_id:
                from app.services.streamlined_context_service import streamlined_context_service
                return streamlined_context_service.get_essential_facts_only(user_id, session_id, db)
        except:
            pass
        
        return f"Financial context temporarily unavailable: {str(e)}"


def build_legacy_comprehensive_context(user_id: int, db: Session = None) -> str:
    """
    Legacy comprehensive context builder (kept for fallback)
    """
    try:
        # Get smart context with calculations
        smart_context = context_service.build_smart_context(user_id)
        
        if 'error' in smart_context:
            logger.error(f"Smart context error for user {user_id}: {smart_context['error']}")
            return "Financial data temporarily unavailable."
        
        # Build essential context parts only
        context_parts = []
        
        # Core financial position
        context_parts.append(f"""FINANCIAL POSITION:
Net Worth: ${smart_context.get('net_worth', 0):,.0f}
Monthly Income: ${smart_context.get('monthly_income', 0):,.0f}
Monthly Surplus: ${smart_context.get('monthly_surplus', 0):,.0f}
Debt-to-Income Ratio: {smart_context.get('debt_to_income_ratio', 0):.1f}%""")

        # Retirement context if available
        retirement_ctx = smart_context.get('retirement_context', {})
        if retirement_ctx and retirement_ctx.get('status') != 'unavailable':
            context_parts.append(f"""RETIREMENT STATUS:
Completion: {retirement_ctx.get('completion_percentage', 0):.1f}%
Social Security: ${retirement_ctx.get('social_security_annual', 0):,.0f}/year
Status: {retirement_ctx.get('retirement_status', 'Unknown')}""")

        # Top debt if exists
        debt_strategy = smart_context.get('debt_strategy', [])
        if debt_strategy:
            top_debt = debt_strategy[0]
            context_parts.append(f"""TOP DEBT PRIORITY:
{top_debt['name']}: ${top_debt['balance']:,.0f} @ {top_debt['rate']:.1f}%""")

        # Top opportunity
        opportunities = smart_context.get('opportunities', [])
        if opportunities:
            top_opp = opportunities[0]
            context_parts.append(f"""TOP OPPORTUNITY:
{top_opp['action']} - {top_opp['impact']}""")

        return "\n\n".join(context_parts)
        
    except Exception as e:
        logger.error(f"Error building legacy context for user {user_id}: {str(e)}")
        return "Financial context temporarily unavailable."

def build_enhanced_system_prompt(smart_context_str: str) -> str:
    """
    Build enhanced system prompt with smart context for precise financial advice
    """
    return f"""You are an expert financial advisor with strong mathematical capabilities.

CLIENT FINANCIAL DATA:
{smart_context_str}

Calculate exactly what the client needs to know. Show your math and explain your reasoning step by step. Give specific, actionable advice with dollar amounts and timelines.

Remember: You have all the data above - use it to provide precise, mathematical guidance."""

def format_liability_details(liabilities: list) -> str:
    """
    Format liability details with enhanced information for AI context
    """
    if not liabilities:
        return "No liabilities recorded"
    
    formatted_lines = []
    for liability in liabilities:
        name = liability.get('name', 'Unknown')
        balance = liability.get('balance', 0)
        line = f"- {name}: ${balance:,.0f}"
        
        # Add interest rate if available
        if 'interest_rate' in liability and liability['interest_rate'] is not None:
            rate = liability['interest_rate']
            line += f" at {rate:.2f}% interest"
            
            # Add payment info
            if 'minimum_payment' in liability and liability['minimum_payment']:
                payment = liability['minimum_payment']
                line += f" (${payment:,.0f}/month payment)"
            
            # Add loan term info
            if 'remaining_months' in liability and liability['remaining_months']:
                remaining = liability['remaining_months']
                years = remaining // 12
                months = remaining % 12
                if years > 0:
                    line += f", {remaining} months remaining"
                    
                    # Calculate payoff insights
                    if rate > 0 and liability.get('minimum_payment', 0) > 0:
                        if rate > 15:
                            line += " (HIGH RATE - prioritize payoff)"
                        elif rate < 3:
                            line += " (LOW RATE - consider investing instead)"
            
            # Add fixed/variable rate info
            if 'is_fixed_rate' in liability:
                rate_type = "fixed" if liability['is_fixed_rate'] else "variable"
                line += f" ({rate_type} rate)"
        
        formatted_lines.append(line)
    
    return "\n".join(formatted_lines)

def get_user_financial_summary(user_id: int, db: Session) -> dict:
    """
    Get user financial summary for chat context (without FastAPI dependencies)
    """
    try:
        print("\n" + "="*80)
        print("STEP 1: DATABASE RETRIEVAL - get_user_financial_summary")
        print("="*80)
        
        # Get ALL financial entries for live calculations
        entries = db.query(FinancialEntry).filter(
            FinancialEntry.user_id == user_id,
            FinancialEntry.is_active == True
        ).all()
        
        print(f"Total entries found: {len(entries)}")
        
        # Check liability entries specifically
        liability_entries = [e for e in entries if e.category == EntryCategory.liabilities]
        print(f"Liability entries: {len(liability_entries)}")
        
        for entry in liability_entries:
            print(f"\nLiability: {entry.description}")
            print(f"  DB Fields:")
            print(f"    - amount: ${entry.amount}")
            print(f"    - interest_rate: {entry.interest_rate}%")
            print(f"    - daily_interest_cost: ${entry.daily_interest_cost}")
            print(f"    - minimum_payment: ${entry.minimum_payment}")
            print(f"    - last_synced_to_vector: {entry.last_synced_to_vector}")
        
        if not entries:
            logger.warning(f"No financial entries found for user {user_id}")
            return {}
        
        # Calculate live financial data
        assets_by_category = {}
        liabilities = []
        monthly_income = Decimal('0')
        monthly_expenses = Decimal('0')
        
        for entry in entries:
            if entry.category == EntryCategory.assets:
                subcategory = entry.subcategory or ('real_estate' if float(entry.amount) > 100000 else 'other_assets')
                if subcategory not in assets_by_category:
                    assets_by_category[subcategory] = []
                assets_by_category[subcategory].append({
                    "name": entry.description,
                    "value": float(entry.amount),
                    "subcategory": subcategory
                })
            elif entry.category == EntryCategory.liabilities:
                liability_data = {
                    "name": entry.description,
                    "balance": float(entry.amount),
                    "subcategory": entry.subcategory or 'other_debt',
                    "type": entry.subcategory or 'debt'
                }
                
                # Add enhanced liability details if available
                if entry.interest_rate is not None:
                    liability_data["interest_rate"] = float(entry.interest_rate)
                if entry.minimum_payment is not None:
                    liability_data["minimum_payment"] = float(entry.minimum_payment)
                if entry.loan_term_months is not None:
                    liability_data["loan_term_months"] = entry.loan_term_months
                if entry.remaining_months is not None:
                    liability_data["remaining_months"] = entry.remaining_months
                if entry.is_fixed_rate is not None:
                    liability_data["is_fixed_rate"] = entry.is_fixed_rate
                if entry.original_amount is not None:
                    liability_data["original_amount"] = float(entry.original_amount)
                
                liabilities.append(liability_data)
            elif entry.category == EntryCategory.income:
                if entry.frequency == FrequencyType.monthly:
                    monthly_income += entry.amount
                elif entry.frequency == FrequencyType.annually:
                    monthly_income += entry.amount / 12
                elif entry.frequency == FrequencyType.weekly:
                    monthly_income += entry.amount * 52 / 12
            elif entry.category == EntryCategory.expenses:
                if entry.frequency == FrequencyType.monthly:
                    monthly_expenses += entry.amount
                elif entry.frequency == FrequencyType.annually:
                    monthly_expenses += entry.amount / 12
                elif entry.frequency == FrequencyType.weekly:
                    monthly_expenses += entry.amount * 52 / 12
        
        # Calculate totals
        total_assets = sum(asset['value'] for category in assets_by_category.values() for asset in category)
        total_liabilities = sum(liability['balance'] for liability in liabilities)
        net_worth = total_assets - total_liabilities
        monthly_surplus = float(monthly_income - monthly_expenses)
        savings_rate = (monthly_surplus / float(monthly_income)) * 100 if monthly_income > 0 else 0
        
        # Calculate monthly debt payments (scalable DTI calculation)
        monthly_debt_payments = Decimal('0')
        
        # Method 1: Use minimum_payment from liability entries
        liability_entries = [e for e in entries if e.category == EntryCategory.liabilities]
        
        # Group by balance to avoid duplicates, keep the one with highest minimum payment
        unique_liabilities = {}
        for liability in liability_entries:
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
                # Treat 'one_time' as monthly for minimum payments
                if liability.frequency in [FrequencyType.monthly, FrequencyType.one_time]:
                    monthly_debt_payments += liability.minimum_payment
                elif liability.frequency == FrequencyType.annually:
                    monthly_debt_payments += liability.minimum_payment / 12
                elif liability.frequency == FrequencyType.weekly:
                    monthly_debt_payments += liability.minimum_payment * 52 / 12
                elif liability.frequency == FrequencyType.quarterly:
                    monthly_debt_payments += liability.minimum_payment / 3
                elif liability.frequency == FrequencyType.daily:
                    monthly_debt_payments += liability.minimum_payment * 30
        
        # Method 2: If no minimum payments found, look for debt payment expenses
        if monthly_debt_payments == 0:
            debt_payment_keywords = ['mortgage', 'home loan', 'credit card', 'loan payment', 'car payment', 'student loan', 'debt payment', 'installment']
            
            for entry in entries:
                if entry.category == EntryCategory.expenses:
                    expense_desc_lower = entry.description.lower()
                    if any(keyword in expense_desc_lower for keyword in debt_payment_keywords):
                        if entry.frequency == FrequencyType.monthly:
                            monthly_debt_payments += entry.amount
                        elif entry.frequency == FrequencyType.annually:
                            monthly_debt_payments += entry.amount / 12
                        elif entry.frequency == FrequencyType.weekly:
                            monthly_debt_payments += entry.amount * 52 / 12
                        elif entry.frequency == FrequencyType.quarterly:
                            monthly_debt_payments += entry.amount / 3
                        elif entry.frequency == FrequencyType.daily:
                            monthly_debt_payments += entry.amount * 30
        
        # Calculate DTI correctly using monthly debt payments
        debt_to_income_ratio = round((float(monthly_debt_payments) / float(monthly_income)) * 100, 1) if monthly_income > 0 else 0
        
        print(f"\nSTEP 2: DTI CALCULATION")
        print(f"  Monthly Income: ${monthly_income:,.2f}")
        print(f"  Monthly Debt Payments: ${monthly_debt_payments:,.2f}")
        print(f"  DTI Ratio: {debt_to_income_ratio}%")
        
        logger.info(f"Chat Context DTI Calculation - Monthly Debt: ${monthly_debt_payments}, Monthly Income: ${monthly_income}, DTI: {debt_to_income_ratio}%")
        
        # Organize assets
        real_estate = assets_by_category.get('real_estate', [])
        investments = (
            assets_by_category.get('retirement_accounts', []) +
            assets_by_category.get('investment_accounts', []) +
            assets_by_category.get('stocks_bonds', [])
        )
        cash = (
            assets_by_category.get('cash_bank_accounts', []) +
            assets_by_category.get('other_assets', [])
        )
        
        real_estate_value = sum(asset['value'] for asset in real_estate)
        investments_value = sum(asset['value'] for asset in investments)
        cash_value = sum(asset['value'] for asset in cash)
        
        print(f"\nSTEP 3: RETURNED JSON STRUCTURE")
        print(f"  - debt_to_income_ratio: {debt_to_income_ratio}%")
        print(f"  - liabilities count: {len(liabilities)}")
        
        # Check if enhanced fields make it to JSON
        for liability in liabilities:
            print(f"  JSON Liability: {liability.get('name', 'UNNAMED')}")
            print(f"    - balance: ${liability.get('balance', 0):,.2f}")
            print(f"    - interest_rate in JSON: {liability.get('interest_rate', 'NOT PRESENT')}")
            print(f"    - daily_interest_cost in JSON: {liability.get('daily_interest_cost', 'NOT PRESENT')}")
        
        print("="*80 + "\n")
        
        return {
            'netWorth': net_worth,
            'totalAssets': total_assets,
            'totalLiabilities': total_liabilities,
            'monthlyIncome': float(monthly_income),
            'monthlyExpenses': float(monthly_expenses),
            'monthlySurplus': monthly_surplus,
            'savingsRate': round(savings_rate, 1),
            'debtToIncomeRatio': debt_to_income_ratio,
            'monthlyDebtPayments': float(monthly_debt_payments),
            'emergencyFundCoverage': round(cash_value / float(monthly_expenses), 1) if monthly_expenses > 0 else 0,
            'assets': {
                'realEstate': real_estate,
                'investments': investments,
                'cash': cash
            },
            'liabilities': liabilities  # Include enhanced liability details
        }
        
    except Exception as e:
        logger.error(f"Error calculating financial summary for user {user_id}: {str(e)}")
        return {}

def get_essential_context(user_id: int, db: Session) -> str:
    """
    Get only the absolutely essential user data - under 300 chars max
    Includes: Client name, age, state, net worth, monthly surplus, risk tolerance
    """
    try:
        # Get user basic info
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return "User data not found"
        
        # Get profile data
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        
        # Get essential financial data (using same calculation as frontend)
        summary = get_user_financial_summary(user_id, db)
        
        # Build ultra-concise context (target: 200-300 chars)
        name = f"{user.first_name} {user.last_name}".strip() if user.first_name or user.last_name else "Client"
        age = profile.age if profile else "unknown"
        state = profile.state if profile else "unknown" 
        risk_tolerance = profile.risk_tolerance if profile else "unknown"
        
        net_worth = summary.get('netWorth', 0) if summary else 0
        monthly_surplus = summary.get('monthlySurplus', 0) if summary else 0
        
        # Format in most concise way possible
        context = f"{name}, {age}, {state}. Net worth: ${net_worth:,.0f}. Monthly surplus: ${monthly_surplus:,.0f}. Risk: {risk_tolerance}."
        
        return context[:300]  # Hard limit at 300 chars
        
    except Exception as e:
        logger.error(f"Error building essential context: {str(e)}")
        return "Essential context unavailable"

def build_retirement_critical_context(user_id: int, db: Session) -> str:
    """
    Build critical context specifically for retirement questions
    Ensures Social Security is ALWAYS included
    """
    try:
        from app.models.user_profile import UserProfile, UserBenefit
        
        # Get user profile
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            return ""
            
        # Get Social Security benefits
        ss_benefit = db.query(UserBenefit).filter(
            UserBenefit.profile_id == profile.id,
            UserBenefit.benefit_type == 'social_security'
        ).first()
        
        if not ss_benefit:
            return ""
            
        # Get financial summary for income data
        summary = get_user_financial_summary(user_id, db)
        
        # Calculate key retirement metrics
        user_age = profile.age or 54
        ss_monthly = float(ss_benefit.estimated_monthly_benefit or 4000)
        ss_annual = ss_monthly * 12
        ss_start_age = ss_benefit.full_retirement_age or 67
        years_to_retirement = max(0, ss_start_age - user_age)
        
        # Get current income to estimate retirement needs
        monthly_income = summary.get('monthlyIncome', 0) if summary else 0
        annual_income = monthly_income * 12
        
        # Standard retirement planning: 80% income replacement
        retirement_needs_annual = annual_income * 0.8
        
        # Calculate NET portfolio requirement (after SS)
        net_portfolio_needs = max(0, retirement_needs_annual - ss_annual)
        required_portfolio = net_portfolio_needs / 0.04  # 4% rule
        
        # Get current retirement savings
        total_assets = summary.get('totalAssets', 0) if summary else 0
        
        context = f"""
🎯 CRITICAL RETIREMENT CONTEXT FOR AI:

CLIENT INFO:
- Age: {user_age} years old
- Annual Income: ${annual_income:,.0f}
- Years to Retirement: {years_to_retirement} years

GUARANTEED RETIREMENT INCOME:
✅ Social Security: ${ss_monthly:,.0f}/month (${ss_annual:,.0f}/year) starting at age {ss_start_age}

RETIREMENT CALCULATION (MUST USE THIS):
1. Retirement Income Need (80% rule): ${retirement_needs_annual:,.0f}/year
2. SUBTRACT Social Security: -${ss_annual:,.0f}/year
3. Net Portfolio Must Generate: ${net_portfolio_needs:,.0f}/year
4. Portfolio Required (4% rule): ${required_portfolio:,.0f}

CURRENT STATUS:
- Total Assets: ${total_assets:,.0f}
- Progress: {(total_assets/required_portfolio*100):.1f}% complete

⚠️ CRITICAL: Always subtract SS from retirement needs BEFORE calculating required portfolio!
"""
        return context
        
    except Exception as e:
        logger.warning(f"Failed to build retirement context: {str(e)}")
        return ""


# Removed complex retirement context function - trusting vector DB instead!

@router.get("/health")
async def chat_health():
    """
    Chat endpoint health check
    """
    # Check which LLM providers are available
    import os
    available_providers = []
    if os.getenv('OPENAI_API_KEY'):
        available_providers.append('openai')
    if os.getenv('GEMINI_API_KEY'):
        available_providers.append('gemini')  
    if os.getenv('ANTHROPIC_API_KEY'):
        available_providers.append('claude')
    
    return {
        "status": "healthy",
        "service": "Step 6 Chat API",
        "endpoints": ["/message", "/suggestions/{user_id}"],
        "llm_status": "real_llm_apis_active",
        "available_providers": available_providers,
        "context_source": "live_comprehensive_summary",
        "dti_fix_applied": True,
        "fallback": "mock_responses_if_api_fails",
        "note": "Step 5 uses separate /api/v1/llm/* endpoints"
    }

@router.post("/test-llm")
async def test_llm_integration(
    provider: str = "gemini",
    model_tier: str = "dev"
):
    """
    Test LLM integration without authentication (for debugging)
    """
    try:
        # Test the LLM response generation
        test_message = "What is 2+2?"
        test_context = "This is a simple math test."
        
        response = await generate_llm_response(
            message=test_message,
            context=test_context,
            provider=provider,
            model_tier=model_tier,
            user_id=1
        )
        
        return {
            "status": "success",
            "provider": provider,
            "model_tier": model_tier,
            "test_message": test_message,
            "response": response,
            "response_type": "mock" if "mock" in response.lower() else "real_llm"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "provider": provider,
            "model_tier": model_tier,
            "error": str(e),
            "error_type": type(e).__name__
        }

@router.get("/debug-dti/{user_id}")
async def debug_dti_calculation(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Debug endpoint to check current DTI calculation
    """
    try:
        # Get live financial summary
        financials = get_user_financial_summary(user_id, db)
        
        return {
            "user_id": user_id,
            "current_dti": financials.get('debtToIncomeRatio', 'NOT_FOUND'),
            "monthly_debt_payments": financials.get('monthlyDebtPayments', 'NOT_FOUND'), 
            "monthly_income": financials.get('monthlyIncome', 'NOT_FOUND'),
            "total_liabilities": financials.get('totalLiabilities', 'NOT_FOUND'),
            "calculation_method": "live_financial_summary_direct",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "user_id": user_id,
            "error": str(e),
            "error_type": type(e).__name__
        }


class ChatMessageRequest(BaseModel):
    user_id: int
    message: str
    session_id: str
    provider: str = 'gemini'
    model_tier: str = 'dev'
    include_context: bool = True

class ChatMessageResponse(BaseModel):
    message: Dict[str, Any]
    tokens_used: Dict[str, int]
    cost_breakdown: Dict[str, float]
    suggested_questions: List[str]
    context_used: Optional[str] = None
    intent_detected: Optional[str] = None

@router.post("/message", response_model=ChatMessageResponse)
async def send_chat_message(
    request: ChatMessageRequest,
    db: Session = Depends(get_db)
    # TEMPORARILY REMOVED AUTH: current_user: User = Depends(get_current_active_user)
):
    """
    Send a message to the AI financial advisor
    """
    
    logger.info(f"🔴 CHAT API CALLED - User: {request.user_id}, Message: '{request.message}', Include Context: {request.include_context}")
    
    # TEMPORARY TEST - Return immediately to confirm endpoint is hit
    return ChatMessageResponse(
        message={
            "id": f"test_{uuid.uuid4()}",
            "content": f"🎯 INTENT SYSTEM WORKING! Your message: '{request.message}' - Intent would be detected here",
            "role": "assistant",
            "timestamp": datetime.now().isoformat(),
            "provider": "test",
            "model": "test",
            "session_id": "test"
        },
        tokens_used={"input": 0, "output": 0, "total": 0},
        cost_breakdown={"total": 0.0},
        suggested_questions=[],
        context_used="Test context",
        intent_detected="TEST"
    )
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        # Generate contextual suggestions based on user data
        suggestions = await generate_contextual_suggestions(user_id)
        
        return {
            "initial": [
                "What's my current financial health score?",
                "Show me my complete financial picture",
                "What should I focus on next financially?",
                "How am I doing compared to others my age?",
                "What are my biggest financial risks?",
                "How can I optimize my savings rate?"
            ],
            "contextual": suggestions
        }
        
    except Exception as e:
        logger.error(f"Failed to get suggestions for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get suggestions: {str(e)}"
        )

async def generate_llm_response(
    message: str,
    context: str,
    provider: str,
    model_tier: str,
    user_id: int,
    system_prompt: str = None
) -> str:
    """
    Generate LLM response with financial context
    """
    
    # Use provided system prompt or default financial advisor prompt
    if system_prompt is None:
        system_prompt = """You are an expert AI financial advisor with access to the user's complete financial profile. 
        
        Key guidelines:
        - Be specific and use actual numbers from their financial data
        - Provide actionable, personalized advice
        - Reference their goals, preferences, and current situation
        - Use a professional but conversational tone
        - Always include disclaimers for investment advice
        - Focus on education and guidance, not specific investment recommendations
        
        Keep responses concise but comprehensive (2-3 paragraphs max unless asking for detailed analysis).
        """
    
    # Build user prompt with context
    user_prompt = f"""
    FINANCIAL CONTEXT:
    {context}
    
    USER QUESTION: {message}
    
    Please provide personalized financial guidance based on the context above.
    """
    
    # Always use real LLMs now (API keys are in .env)
    try:
        # Attempt to call real LLM API
        return await call_real_llm_api(system_prompt, user_prompt, provider, model_tier, user_id, message)
    except Exception as llm_error:
        logger.warning(f"Real LLM call failed, falling back to mock: {str(llm_error)}")
        # Fall through to mock responses
    
    # Mock LLM responses (used when ENABLE_REAL_LLMS=false or real LLM fails)
    
    if "net worth" in message.lower():
        return f"[MOCK RESPONSE] Based on your financial profile, your current net worth is $2,565,545. This puts you in an excellent position with total assets of $2,879,827 and relatively low liabilities of $314,282. Your 59.9% savings rate is exceptional and shows strong financial discipline. However, I notice your real estate concentration at 50.3% is quite high - you might want to consider diversifying to reduce risk. Your monthly surplus of $10,620 provides great flexibility for additional investments or goal acceleration."
    
    elif "real estate" in message.lower():
        return f"[MOCK RESPONSE] Your real estate allocation is currently 50.3% of your portfolio ($1,449,706 total), which exceeds the typical recommendation of 30% for your moderate risk profile. While real estate has served you well, this concentration creates risk. Consider gradually rebalancing by directing your excellent $10,620 monthly surplus toward other asset classes. Your aggressive investment style suggests you could handle more equity exposure. This diversification would maintain your growth potential while reducing concentration risk."
    
    elif "retirement" in message.lower() or "goal" in message.lower():
        return f"[MOCK RESPONSE] You're making solid progress toward your $3.5M retirement goal with $1,999,181 already saved (57.1% complete). At your current pace, you need $12,062 monthly to reach your 2035 target. The good news? Your $10,620 monthly surplus puts you very close to this requirement. Consider maximizing tax-advantaged accounts first, then investing the remainder in low-cost index funds aligned with your aggressive investment style. Your 24% federal tax bracket makes traditional 401(k) contributions especially valuable."
    
    elif "tax" in message.lower():
        return f"[MOCK RESPONSE] In the 24% federal tax bracket with NC's 4% state rate, tax optimization is crucial. Since you have tax-loss harvesting enabled, you're on the right track. With your high income and surplus, prioritize: 1) Max out 401(k) contributions ($23,000 limit), 2) Consider backdoor Roth IRA if eligible, 3) Municipal bonds for your tax bracket, 4) Continue tax-loss harvesting in taxable accounts. Your married filing jointly status provides additional strategies we could explore. Always consult your tax professional for personalized advice."
    
    else:
        return f"[MOCK RESPONSE] Based on your strong financial position with $2.56M net worth and exceptional 59.9% savings rate, you have many opportunities. Your main focus areas should be: 1) Reducing real estate concentration from 50.3% to improve diversification, 2) Maximizing tax-advantaged savings with your $10,620 monthly surplus, 3) Staying on track for your retirement goal (you're 57% there!). Your aggressive investment style and excellent cash flow provide flexibility to optimize your strategy. What specific area would you like to explore further?"

async def call_real_llm_api(system_prompt: str, user_prompt: str, provider: str, model_tier: str, user_id: int = None, query: str = None) -> str:
    """
    Call real LLM API using API keys from .env
    """
    import os
    import json
    import httpx
    
    # ==========================================
    # STORE LLM PAYLOAD FOR DEBUG VIEW (STEP 7)
    # ==========================================
    if user_id:
        from app.api.v1.endpoints.debug import store_llm_payload
        store_llm_payload(user_id, {
            "query": query or "Unknown query",
            "provider": provider,
            "model_tier": model_tier,
            "system_prompt": system_prompt,
            "user_message": user_prompt,
            "context_used": user_prompt  # Full context is in user_prompt
        })
    
    # ==========================================
    # COMPLETE LLM PAYLOAD LOGGING (STEP 6)
    # ==========================================
    print("\n" + "="*100)
    print("STEP 6: COMPLETE LLM PAYLOAD BEING SENT TO API")
    print("="*100)
    print(f"Provider: {provider}")
    print(f"Model Tier: {model_tier}")
    print()
    print("SYSTEM PROMPT:")
    print("-" * 50)
    print(system_prompt)
    print()
    print("USER PROMPT:")
    print("-" * 50)
    print(user_prompt)
    print()
    print("COMBINED PROMPT LENGTH:")
    print(f"- System prompt: {len(system_prompt)} characters")
    print(f"- User prompt: {len(user_prompt)} characters")
    print(f"- Total: {len(system_prompt) + len(user_prompt)} characters")
    print("="*100)
    
    if provider.lower() == "openai":
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        model = "gpt-3.5-turbo" if model_tier == "dev" else "gpt-4"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.7
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise ValueError(f"OpenAI API error: {response.status_code} {response.text}")
            
            data = response.json()
            llm_response = data["choices"][0]["message"]["content"]
            
            # Log the LLM response
            print("\n" + "="*100)
            print("STEP 7: LLM RESPONSE RECEIVED FROM OPENAI")
            print("="*100)
            print(f"Response length: {len(llm_response)} characters")
            print("RESPONSE CONTENT:")
            print("-" * 50)
            print(llm_response)
            print("="*100)
            
            return llm_response
    
    elif provider.lower() == "gemini":
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        
        model = "gemini-1.5-flash" if model_tier == "dev" else "gemini-1.5-pro"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [
                        {
                            "parts": [
                                {"text": f"{system_prompt}\n\n{user_prompt}"}
                            ]
                        }
                    ],
                    "generationConfig": {
                        "maxOutputTokens": 1000,
                        "temperature": 0.7
                    }
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise ValueError(f"Gemini API error: {response.status_code} {response.text}")
            
            data = response.json()
            llm_response = data["candidates"][0]["content"]["parts"][0]["text"]
            
            # Log the LLM response
            print("\n" + "="*100)
            print("STEP 7: LLM RESPONSE RECEIVED FROM GEMINI")
            print("="*100)
            print(f"Response length: {len(llm_response)} characters")
            print("RESPONSE CONTENT:")
            print("-" * 50)
            print(llm_response)
            print("="*100)
            
            return llm_response
    
    elif provider.lower() == "claude":
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        
        model = "claude-3-haiku-20240307" if model_tier == "dev" else "claude-3-sonnet-20240229"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "max_tokens": 1000,
                    "system": system_prompt,
                    "messages": [
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.7
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise ValueError(f"Claude API error: {response.status_code} {response.text}")
            
            data = response.json()
            llm_response = data["content"][0]["text"]
            
            # Log the LLM response
            print("\n" + "="*100)
            print("STEP 7: LLM RESPONSE RECEIVED FROM CLAUDE")
            print("="*100)
            print(f"Response length: {len(llm_response)} characters")
            print("RESPONSE CONTENT:")
            print("-" * 50)
            print(llm_response)
            print("="*100)
            
            return llm_response
    
    else:
        raise ValueError(f"Unsupported provider: {provider}")

def estimate_tokens(text: str) -> int:
    """
    Rough token estimation (1 token ≈ 4 characters)
    """
    return max(1, len(text) // 4)

def calculate_cost(input_tokens: int, output_tokens: int, provider: str, model_tier: str) -> Dict[str, float]:
    """
    Calculate LLM costs based on provider and tier
    """
    
    cost_configs = {
        'openai': {
            'dev': {'input': 0.001, 'output': 0.002},  # GPT-3.5
            'prod': {'input': 0.03, 'output': 0.06}    # GPT-4
        },
        'gemini': {
            'dev': {'input': 0.001, 'output': 0.001},   # Gemini Flash
            'prod': {'input': 0.007, 'output': 0.007}   # Gemini Pro
        },
        'claude': {
            'dev': {'input': 0.003, 'output': 0.015},   # Claude Haiku
            'prod': {'input': 0.015, 'output': 0.075}   # Claude Opus
        }
    }
    
    config = cost_configs.get(provider, cost_configs['gemini']).get(model_tier, cost_configs['gemini']['dev'])
    
    input_cost = (input_tokens / 1000) * config['input']
    output_cost = (output_tokens / 1000) * config['output']
    total_cost = input_cost + output_cost
    
    return {
        'input_cost': input_cost,
        'output_cost': output_cost,
        'total': total_cost
    }

def get_model_name(provider: str, model_tier: str) -> str:
    """
    Get model name based on provider and tier
    """
    models = {
        'openai': {'dev': 'gpt-3.5-turbo', 'prod': 'gpt-4'},
        'gemini': {'dev': 'gemini-1.5-flash', 'prod': 'gemini-1.5-pro'},
        'claude': {'dev': 'claude-3-haiku', 'prod': 'claude-3-opus'}
    }
    
    return models.get(provider, models['gemini']).get(model_tier, 'gemini-1.5-flash')

def generate_suggested_questions(user_id: int, current_message: str) -> List[str]:
    """
    Generate contextual follow-up questions
    """
    
    # Base questions that are always relevant
    base_questions = [
        "How can I optimize my tax strategy?",
        "What's my path to financial independence?",
        "Should I rebalance my portfolio?",
        "How can I accelerate my goals?"
    ]
    
    # Context-specific questions based on current message
    if "real estate" in current_message.lower():
        return [
            "How should I diversify out of real estate?",
            "What's the optimal real estate allocation?",
            "Should I sell some rental properties?",
            "How do I reduce concentration risk?"
        ]
    elif "retirement" in current_message.lower():
        return [
            "How much should I save monthly for retirement?",
            "When can I retire comfortably?",
            "What's my retirement income plan?",
            "Should I adjust my retirement timeline?"
        ]
    elif "tax" in current_message.lower():
        return [
            "Should I do more tax-loss harvesting?",
            "What about Roth IRA conversions?",
            "Are municipal bonds right for me?",
            "How can I reduce my tax burden?"
        ]
    else:
        return base_questions

async def generate_contextual_suggestions(user_id: int) -> Dict[str, List[str]]:
    """
    Generate personalized suggestions based on user's financial situation
    """
    
    # These would be dynamically generated based on actual user data
    return {
        "high_priority": [
            "How can I reduce my 50.3% real estate concentration risk?",
            "Should I max out my retirement contributions with my $10,620 monthly surplus?",
            "What's the best tax strategy for my 24% federal tax bracket?"
        ],
        "goals_based": [
            "How close am I to my $3.5M retirement goal?",
            "Should I adjust my college savings strategy?",
            "What's my timeline to financial independence?"
        ],
        "optimization": [
            "Should I rebalance my portfolio given my aggressive investment style?",
            "How can I optimize my $314K in liabilities?",
            "What's the best use of my monthly surplus?"
        ]
    }