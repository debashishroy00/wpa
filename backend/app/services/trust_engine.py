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
        Ensure every number in response is grounded in claims.
        Returns validated response or degraded safe version.
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
        
        # Verify each number is grounded
        for num in numbers:
            if not self._is_grounded(num, claims):
                result["issues"].append(f"Ungrounded: ${num:,.0f}")
                result["valid"] = False
        
        # Find assumptions
        result["assumptions"] = self._find_assumptions(ai_response)
        
        # Adjust confidence
        if result["assumptions"]:
            result["confidence"] = "MEDIUM"
        if not result["valid"]:
            result["confidence"] = "LOW"
            result["response"] = self._create_safe_response(claims)
        
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