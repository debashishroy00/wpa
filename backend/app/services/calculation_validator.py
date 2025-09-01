"""
Simple calculation validator stub
Provides basic validation for mathematical calculations in responses
"""

class CalculationValidator:
    """Simple validator for mathematical calculations"""
    
    def validate_math(self, response: str) -> dict:
        """Validate mathematical calculations in response"""
        return {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
    
    def suggest_correction(self, error: str) -> str:
        """Suggest correction for calculation error"""
        return f"Please verify: {error}"

# Global instance
calculation_validator = CalculationValidator()