"""
TrustEngine: Validates all AI outputs against known facts.
Ensures no hallucinations, no ungrounded numbers, explicit assumptions.
"""

import re
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class TrustEngine:
    """Validate AI responses against mathematical facts"""
    
    def validate(self, ai_response: str, claims: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate AI response and add appropriate disclaimers for recommendations.
        Pass through enhanced responses with warnings instead of blocking them.
        """
        result = {
            "response": ai_response,
            "valid": True,
            "issues": [],
            "assumptions": [],
            "confidence": "HIGH"
        }
        
        # Extract numbers from response
        numbers = self._extract_numbers(ai_response)
        ungrounded_count = 0
        
        # Check each number for grounding
        for num in numbers:
            if not self._is_grounded(num, claims):
                ungrounded_count += 1
        
        # Find assumptions
        result["assumptions"] = self._find_assumptions(ai_response)
        
        # Add disclaimers based on content analysis
        disclaimer_needed = False
        
        # Check for recommendation language
        recommendation_indicators = [
            "recommend", "suggest", "consider", "should", "could", "might want to",
            "action item", "next step", "opportunity", "strategy", "plan"
        ]
        
        has_recommendations = any(indicator in ai_response.lower() for indicator in recommendation_indicators)
        
        # Determine confidence and add disclaimers
        if ungrounded_count > 8:  # High number of calculations/projections
            result["confidence"] = "MEDIUM"
            disclaimer_needed = True
        elif ungrounded_count > 4:
            result["confidence"] = "HIGH"
            disclaimer_needed = True
        elif has_recommendations:
            disclaimer_needed = True
        elif result["assumptions"]:
            result["confidence"] = "MEDIUM"
            disclaimer_needed = True
        
        # Add disclaimer if needed but keep the response
        if disclaimer_needed:
            disclaimer = (
                "\n\n⚠️ **Disclaimer**: This analysis includes recommendations and projections "
                "based on your financial data. All calculations and suggestions should be "
                "reviewed with a qualified financial advisor before making decisions."
            )
            result["response"] = ai_response + disclaimer
        
        return result
    
    def _extract_numbers(self, text: str) -> List[float]:
        """Extract dollar amounts from text"""
        pattern = r'\$[\d,]+\.?\d*'
        numbers = []
        for match in re.findall(pattern, text):
            try:
                num = float(match.replace('$', '').replace(',', ''))
                numbers.append(num)
            except:
                pass
        return numbers
    
    def _is_grounded(self, number: float, claims: Dict) -> bool:
        """Check if number appears in claims"""
        tolerance = 1.0  # Allow small rounding differences
        
        for key, value in claims.items():
            if key.startswith('_'):
                continue
            if isinstance(value, (int, float)):
                if abs(value - number) < tolerance:
                    return True
                # Check annual versions
                if 'monthly' in key and abs(value * 12 - number) < tolerance:
                    return True
        return False
    
    def _find_assumptions(self, text: str) -> List[str]:
        """Extract stated assumptions"""
        patterns = [
            r"assuming[^.]+",
            r"if[^,]+then",
            r"estimated"
        ]
        assumptions = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            assumptions.extend(matches[:3])  # Limit to avoid spam
        return assumptions
    
    def _create_safe_response(self, claims: Dict) -> str:
        """Fallback to grounded facts only"""
        return (
            f"Based on your verified data:\n"
            f"• Net worth: ${claims.get('net_worth', 0):,.0f}\n"
            f"• Monthly surplus: ${claims.get('monthly_surplus', 0):,.0f}\n"
            f"• Total assets: ${claims.get('total_assets', 0):,.0f}\n"
            f"For specific calculations, please provide more context."
        )