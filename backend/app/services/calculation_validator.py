"""
Financial Calculation Validator
Validates mathematical calculations in LLM responses for accuracy
"""
import re
import math
from typing import Dict, List, Tuple, Optional
import structlog
from ..utils.safe_conversion import safe_float

logger = structlog.get_logger()

class CalculationValidator:
    """Validate mathematical calculations in LLM responses"""
    
    def __init__(self):
        self.accuracy_threshold = 0.01  # 1% tolerance for rounding
    
    def extract_calculations(self, response: str) -> List[Tuple]:
        """Extract calculations from response text"""
        # Multiple patterns to catch different calculation formats
        patterns = [
            # Standard: 1,000 × 25 = 25,000
            r'([\d,]+\.?\d*)\s*([×\*\+\-\÷/])\s*([\d,]+\.?\d*)\s*=\s*([\d,]+\.?\d*)',
            # With currency: $1,000 × 25 = $25,000
            r'\$?([\d,]+\.?\d*)\s*([×\*\+\-\÷/])\s*\$?([\d,]+\.?\d*)\s*=\s*\$?([\d,]+\.?\d*)',
            # Parenthetical: (1,000 × 25) = 25,000
            r'\(([\d,]+\.?\d*)\s*([×\*\+\-\÷/])\s*([\d,]+\.?\d*)\)\s*=\s*([\d,]+\.?\d*)',
        ]
        
        all_calculations = []
        for pattern in patterns:
            calculations = re.findall(pattern, response, re.IGNORECASE)
            all_calculations.extend(calculations)
        
        return all_calculations
    
    def extract_percentage_calculations(self, response: str) -> List[Tuple]:
        """Extract percentage-based calculations"""
        # Pattern: $60,000 ÷ 0.04 = $1,500,000
        pattern = r'\$?([\d,]+\.?\d*)\s*÷\s*(0\.\d+)\s*=\s*\$?([\d,]+\.?\d*)'
        return re.findall(pattern, response)
    
    def extract_compound_interest(self, response: str) -> List[Dict]:
        """Extract compound interest calculations"""
        # Pattern: $10,000 × (1.07)^10 = $19,672
        pattern = r'\$?([\d,]+\.?\d*)\s*×\s*\((1\.\d+)\)\^(\d+)\s*=\s*\$?([\d,]+\.?\d*)'
        matches = re.findall(pattern, response)
        
        calculations = []
        for match in matches:
            calculations.append({
                'type': 'compound_interest',
                'principal': safe_float(match[0].replace(',', ''), 0),
                'rate': safe_float(match[1], 0),
                'years': int(match[2]),
                'stated_result': safe_float(match[3].replace(',', ''), 0)
            })
        
        return calculations
    
    def validate_math(self, response: str) -> Dict:
        """Check if math in response is correct"""
        errors = []
        calculation_count = 0
        
        # Validate basic arithmetic
        basic_calculations = self.extract_calculations(response)
        calculation_count += len(basic_calculations)
        
        for calc in basic_calculations:
            try:
                num1 = safe_float(calc[0].replace(',', ''), 0)
                operator = calc[1]
                num2 = safe_float(calc[2].replace(',', ''), 0)
                stated_result = safe_float(calc[3].replace(',', ''), 0)
                
                actual_result = self.perform_operation(num1, operator, num2)
                
                if not self.results_match(actual_result, stated_result):
                    errors.append({
                        'type': 'arithmetic',
                        'calculation': f"{calc[0]} {operator} {calc[2]}",
                        'stated': stated_result,
                        'actual': actual_result,
                        'error_percentage': abs(actual_result - stated_result) / max(actual_result, 1) * 100
                    })
            except Exception as e:
                logger.warning("Failed to validate calculation", calculation=calc, error=str(e))
                continue
        
        # Validate percentage calculations (like 4% rule)
        percentage_calculations = self.extract_percentage_calculations(response)
        calculation_count += len(percentage_calculations)
        
        for calc in percentage_calculations:
            try:
                amount = safe_float(calc[0].replace(',', ''), 0)
                rate = safe_float(calc[1], 0)
                stated_result = safe_float(calc[2].replace(',', ''), 0)
                
                actual_result = amount / rate
                
                if not self.results_match(actual_result, stated_result):
                    errors.append({
                        'type': 'percentage',
                        'calculation': f"${calc[0]} ÷ {calc[1]}",
                        'stated': stated_result,
                        'actual': actual_result,
                        'error_percentage': abs(actual_result - stated_result) / max(actual_result, 1) * 100
                    })
            except Exception as e:
                logger.warning("Failed to validate percentage calculation", calculation=calc, error=str(e))
                continue
        
        # Validate compound interest
        compound_calculations = self.extract_compound_interest(response)
        calculation_count += len(compound_calculations)
        
        for calc in compound_calculations:
            try:
                actual_result = calc['principal'] * (calc['rate'] ** calc['years'])
                
                if not self.results_match(actual_result, calc['stated_result']):
                    errors.append({
                        'type': 'compound_interest',
                        'calculation': f"${calc['principal']:,.0f} × ({calc['rate']})^{calc['years']}",
                        'stated': calc['stated_result'],
                        'actual': actual_result,
                        'error_percentage': abs(actual_result - calc['stated_result']) / max(actual_result, 1) * 100
                    })
            except Exception as e:
                logger.warning("Failed to validate compound interest", calculation=calc, error=str(e))
                continue
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'calculation_count': calculation_count,
            'accuracy_rate': (calculation_count - len(errors)) / max(calculation_count, 1)
        }
    
    def results_match(self, actual: float, stated: float) -> bool:
        """Check if two results match within tolerance"""
        if actual == 0 and stated == 0:
            return True
        
        if actual == 0 or stated == 0:
            return abs(actual - stated) < 1  # Allow $1 difference for zero cases
        
        error_rate = abs(actual - stated) / max(abs(actual), abs(stated))
        return error_rate <= self.accuracy_threshold
    
    def perform_operation(self, num1: float, operator: str, num2: float) -> float:
        """Perform mathematical operation"""
        operations = {
            '×': lambda a, b: a * b,
            '*': lambda a, b: a * b,
            '+': lambda a, b: a + b,
            '-': lambda a, b: a - b,
            '÷': lambda a, b: a / b if b != 0 else float('inf'),
            '/': lambda a, b: a / b if b != 0 else float('inf')
        }
        
        if operator not in operations:
            raise ValueError(f"Unknown operator: {operator}")
        
        return operations[operator](num1, num2)
    
    def suggest_correction(self, error: Dict) -> str:
        """Suggest correction for calculation error"""
        if error['type'] == 'arithmetic':
            return f"Correction: {error['calculation']} = {error['actual']:,.0f}"
        elif error['type'] == 'percentage':
            return f"Correction: {error['calculation']} = ${error['actual']:,.0f}"
        elif error['type'] == 'compound_interest':
            return f"Correction: {error['calculation']} = ${error['actual']:,.0f}"
        else:
            return f"Expected result: {error['actual']:,.0f}"
    
    def get_validation_summary(self, validation: Dict) -> str:
        """Get human-readable validation summary"""
        if validation['valid']:
            return f"✅ All {validation['calculation_count']} calculations verified correct"
        
        error_count = len(validation['errors'])
        accuracy = validation['accuracy_rate'] * 100
        
        summary = f"⚠️ Found {error_count} calculation errors (accuracy: {accuracy:.1f}%)\n"
        
        for error in validation['errors'][:3]:  # Show first 3 errors
            summary += f"• {self.suggest_correction(error)}\n"
        
        if len(validation['errors']) > 3:
            summary += f"... and {len(validation['errors']) - 3} more errors"
        
        return summary

# Global validator instance
calculation_validator = CalculationValidator()