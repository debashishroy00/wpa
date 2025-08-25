"""
Deterministic Context Service
Provides ONLY pre-computed Step-4 values to LLMs - NO NEW MATH
Implements "single source of truth" principle
"""
from typing import Dict, Any, Optional
import logging
from sqlalchemy.orm import Session
from datetime import datetime

logger = logging.getLogger(__name__)


class DeterministicContextService:
    """
    Provides only Step-4 computed values to LLMs
    Eliminates math hallucination by using single source of truth
    """
    
    def get_step4_context(self, user_id: int, session_id: str, db: Session) -> Dict[str, Any]:
        """
        Get ONLY Step-4 pre-computed values - no calculations allowed
        
        Returns:
            Dictionary with Step-4 plan_json data only
        """
        try:
            # Get the latest Step-4 calculation for this user
            step4_data = self._get_latest_step4_calculation(user_id, db)
            
            if not step4_data:
                return {
                    "error": "No Step-4 calculation available",
                    "message": "Run financial analysis first"
                }
            
            # Extract only the computed values - no new calculations
            context = {
                "user_id": user_id,
                "calculation_timestamp": step4_data.get("timestamp"),
                "health": step4_data.get("health", {}),
                "financial_position": step4_data.get("financial_position", {}),
                "retirement": step4_data.get("retirement", {}),
                "debt_analysis": step4_data.get("debt_analysis", {}),
                "portfolio": step4_data.get("portfolio", {}),
                "goals": step4_data.get("goals", {}),
                "recommendations": step4_data.get("recommendations", {}),
                "guardrails": step4_data.get("guardrails", {})
            }
            
            logger.info(f"Retrieved Step-4 context for user {user_id}: {len(str(context))} chars")
            return context
            
        except Exception as e:
            logger.error(f"Error getting Step-4 context for user {user_id}: {str(e)}")
            return {
                "error": f"Step-4 context unavailable: {str(e)}",
                "user_id": user_id
            }
    
    def _get_latest_step4_calculation(self, user_id: int, db: Session) -> Optional[Dict]:
        """Get the most recent Step-4 calculation for user"""
        try:
            # Import here to avoid circular imports
            from app.services.retirement_calculator import retirement_calculator
            
            # Get fresh Step-4 calculation
            step4_result = retirement_calculator.calculate_comprehensive_retirement_analysis(user_id, db)
            
            if not step4_result or 'error' in step4_result:
                return None
            
            return step4_result
            
        except Exception as e:
            logger.error(f"Failed to get Step-4 calculation: {str(e)}")
            return None
    
    def build_no_math_context(self, user_id: int, session_id: str, db: Session, 
                             intent: str = "general") -> str:
        """
        Build context string with ONLY Step-4 values - no calculations
        
        Args:
            user_id: User ID
            session_id: Session ID
            db: Database session
            intent: Financial intent
            
        Returns:
            Context string with only pre-computed Step-4 values
        """
        step4_data = self.get_step4_context(user_id, session_id, db)
        
        if "error" in step4_data:
            return f"STEP-4 DATA UNAVAILABLE: {step4_data['error']}"
        
        # Build context using ONLY Step-4 computed values
        context_parts = []
        
        # User identification (from Step-4 or database)
        try:
            from app.models.user import User
            user = db.query(User).filter(User.id == user_id).first()
            name = f"{user.first_name} {user.last_name}".strip() if user and (user.first_name or user.last_name) else f"User {user_id}"
        except:
            name = f"User {user_id}"
        
        context_parts.append(f"CLIENT: {name}")
        
        # Health status (from Step-4 only)
        health = step4_data.get("health", {})
        if health:
            band = health.get("band", "unknown")
            score = health.get("score")
            context_parts.append(f"HEALTH STATUS: {band.replace('_', ' ').title()}")
            if score is not None:
                context_parts.append(f"HEALTH SCORE: {score}/100")
        
        # Financial position (Step-4 computed values only)
        financial = step4_data.get("financial_position", {})
        if financial:
            context_parts.append("FINANCIAL POSITION (STEP-4 COMPUTED):")
            
            if "net_worth" in financial:
                context_parts.append(f"• Net Worth: ${financial['net_worth']:,.0f}")
            if "monthly_surplus" in financial:
                context_parts.append(f"• Monthly Surplus: ${financial['monthly_surplus']:,.0f}")
            if "debt_to_income_ratio" in financial:
                context_parts.append(f"• DTI Ratio: {financial['debt_to_income_ratio']:.1f}%")
            if "savings_rate" in financial:
                context_parts.append(f"• Savings Rate: {financial['savings_rate']:.1f}%")
        
        # Retirement analysis (Step-4 computed values only)
        retirement = step4_data.get("retirement", {})
        if retirement:
            context_parts.append("RETIREMENT ANALYSIS (STEP-4 COMPUTED):")
            
            if "success_probability" in retirement:
                context_parts.append(f"• Success Probability: {retirement['success_probability']:.1f}%")
            if "funding_gap" in retirement:
                gap = retirement['funding_gap']
                status = "Surplus" if gap < 0 else "Gap"
                context_parts.append(f"• Funding {status}: ${abs(gap):,.0f}")
            if "required_monthly" in retirement:
                context_parts.append(f"• Required Monthly: ${retirement['required_monthly']:,.0f}")
            if "current_monthly" in retirement:
                context_parts.append(f"• Current Monthly: ${retirement['current_monthly']:,.0f}")
        
        # Portfolio allocation (Step-4 computed values only)
        portfolio = step4_data.get("portfolio", {})
        if portfolio and "allocation" in portfolio:
            allocation = portfolio["allocation"]
            context_parts.append("PORTFOLIO ALLOCATION (STEP-4 COMPUTED):")
            for asset_class, percentage in allocation.items():
                context_parts.append(f"• {asset_class.title()}: {percentage:.1f}%")
        
        # Guardrails (Step-4 determined)
        guardrails = step4_data.get("guardrails", {})
        if guardrails:
            context_parts.append("GUARDRAILS (STEP-4 DETERMINED):")
            if guardrails.get("stabilize_first"):
                context_parts.append("• STABILIZE FIRST: Gap < 0 or MC < 70%")
            if guardrails.get("pay_off_now"):
                context_parts.append("• PAY OFF NOW: Credit card < $5k")
        
        # Goals (Step-4 computed progress)
        goals = step4_data.get("goals", {})
        if goals:
            context_parts.append("GOALS PROGRESS (STEP-4 COMPUTED):")
            for goal_name, goal_data in goals.items():
                if "progress_percentage" in goal_data:
                    context_parts.append(f"• {goal_name}: {goal_data['progress_percentage']:.1f}% complete")
        
        # Recommendations (Step-4 generated)
        recommendations = step4_data.get("recommendations", {})
        if recommendations:
            context_parts.append("STEP-4 RECOMMENDATIONS:")
            if isinstance(recommendations, dict):
                for rec_type, rec_data in recommendations.items():
                    if isinstance(rec_data, dict) and "action" in rec_data:
                        context_parts.append(f"• {rec_data['action']}")
                    elif isinstance(rec_data, str):
                        context_parts.append(f"• {rec_data}")
            elif isinstance(recommendations, list):
                for rec in recommendations[:3]:  # Top 3 recommendations
                    if isinstance(rec, dict) and "action" in rec:
                        context_parts.append(f"• {rec['action']}")
                    elif isinstance(rec, str):
                        context_parts.append(f"• {rec}")
                    else:
                        context_parts.append(f"• {str(rec)}")
        
        final_context = "\n".join(context_parts)
        
        # Add critical instruction
        final_context += "\n\nCRITICAL: Use ONLY the Step-4 computed values above. Do NOT calculate new numbers."
        
        return final_context
    
    def validate_no_new_math(self, response_text: str, step4_data: Dict) -> Dict[str, Any]:
        """
        Validate that LLM response contains no new calculations
        
        Args:
            response_text: LLM response to validate
            step4_data: Step-4 computed values for comparison
            
        Returns:
            Validation result with any violations found
        """
        import re
        
        violations = []
        
        # Extract all dollar amounts from response
        dollar_pattern = r'\$[\d,]+(?:\.\d{2})?'
        response_dollars = re.findall(dollar_pattern, response_text)
        
        # Extract all percentages from response
        percent_pattern = r'\b\d+(?:\.\d+)?%'
        response_percentages = re.findall(percent_pattern, response_text)
        
        # Get all valid Step-4 values
        valid_dollars = set()
        valid_percentages = set()
        
        def extract_numbers_from_dict(data, prefix=""):
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, (int, float)):
                        if "percentage" in key or "rate" in key:
                            valid_percentages.add(f"{value:.1f}%")
                        else:
                            valid_dollars.add(f"${value:,.0f}")
                    elif isinstance(value, dict):
                        extract_numbers_from_dict(value, f"{prefix}.{key}")
        
        extract_numbers_from_dict(step4_data)
        
        # Check for unauthorized dollar amounts
        for dollar in response_dollars:
            if dollar not in valid_dollars:
                violations.append(f"Unauthorized dollar amount: {dollar}")
        
        # Check for unauthorized percentages
        for percent in response_percentages:
            if percent not in valid_percentages:
                violations.append(f"Unauthorized percentage: {percent}")
        
        # Check for calculation keywords
        calc_keywords = [
            "calculate", "computed", "assuming", "4% rule", "multiply", 
            "divide", "add", "subtract", "total", "sum"
        ]
        
        for keyword in calc_keywords:
            if keyword.lower() in response_text.lower():
                violations.append(f"Calculation keyword found: {keyword}")
        
        return {
            "is_valid": len(violations) == 0,
            "violations": violations,
            "response_dollars": response_dollars,
            "response_percentages": response_percentages,
            "valid_dollars": list(valid_dollars),
            "valid_percentages": list(valid_percentages)
        }


# Global instance
deterministic_context_service = DeterministicContextService()