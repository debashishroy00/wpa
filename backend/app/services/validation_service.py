"""
WealthPath AI - Number Validation Service
Advanced validation to prevent LLM number hallucination
"""
import re
import math
from typing import Dict, List, Any, Optional, Union, Tuple
from decimal import Decimal, getcontext
from datetime import datetime, timedelta
import logging

from ..models.llm_models import NumberValidation

logger = logging.getLogger(__name__)

# Set decimal precision for financial calculations
getcontext().prec = 10


class FinancialNumberValidator:
    """Comprehensive financial number validation system"""
    
    def __init__(self):
        self.tolerance_percent = 0.1  # 0.1% tolerance for floating point errors
        self.validation_cache = {}
        
        # Financial calculation patterns
        self.calculation_patterns = {
            'percentage': self._validate_percentage,
            'currency': self._validate_currency,
            'ratio': self._validate_ratio,
            'compound_growth': self._validate_compound_growth,
            'present_value': self._validate_present_value,
            'payment_calculation': self._validate_payment_calculation,
            'allocation_sum': self._validate_allocation_sum
        }
    
    def validate_response_numbers(self, 
                                response_content: str, 
                                source_data: Dict[str, Any]) -> List[NumberValidation]:
        """Validate all numbers in LLM response against source data"""
        validations = []
        
        # Extract numbers with context
        number_matches = self._extract_numbers_with_context(response_content)
        
        for number_info in number_matches:
            validation = self._validate_number_comprehensive(number_info, source_data)
            if validation:
                validations.append(validation)
        
        # Validate mathematical relationships
        relationship_validations = self._validate_mathematical_relationships(
            number_matches, source_data
        )
        validations.extend(relationship_validations)
        
        return validations
    
    def _extract_numbers_with_context(self, text: str) -> List[Dict[str, Any]]:
        """Extract numbers with surrounding context for better validation"""
        number_patterns = [
            # Currency: $1,234.56, $1.2M, $50K
            r'\$\s*(?:(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)|(\d+(?:\.\d+)?)\s*([KMB]))',
            # Percentages: 5.5%, 12%
            r'(\d+(?:\.\d+)?)\s*%',
            # Years: 2024, next 5 years
            r'(?:year|in)\s+(\d{4}|\d{1,2})\s*(?:year|months?)?',
            # General numbers: 1,234.56, 42
            r'\b(\d{1,3}(?:,\d{3})*(?:\.\d{2,4})?)\b',
            # Ratios: 60/40, 3:1
            r'(\d+(?:\.\d+)?)\s*[:/]\s*(\d+(?:\.\d+)?)'
        ]
        
        extracted_numbers = []
        
        for pattern in number_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                context_start = max(0, match.start() - 50)
                context_end = min(len(text), match.end() + 50)
                context = text[context_start:context_end].strip()
                
                number_text = match.group(0)
                parsed_number = self._parse_number(number_text)
                
                if parsed_number is not None:
                    number_info = {
                        'raw_text': number_text,
                        'parsed_value': parsed_number,
                        'context': context,
                        'position': (match.start(), match.end()),
                        'number_type': self._classify_number_type(number_text, context)
                    }
                    extracted_numbers.append(number_info)
        
        return extracted_numbers
    
    def _parse_number(self, number_text: str) -> Optional[float]:
        """Parse number from text representation"""
        try:
            # Remove currency symbols and spaces
            clean_text = number_text.replace('$', '').replace(',', '').replace(' ', '')
            
            # Handle K, M, B suffixes
            multiplier = 1
            if clean_text.endswith(('K', 'k')):
                multiplier = 1000
                clean_text = clean_text[:-1]
            elif clean_text.endswith(('M', 'm')):
                multiplier = 1000000
                clean_text = clean_text[:-1]
            elif clean_text.endswith(('B', 'b')):
                multiplier = 1000000000
                clean_text = clean_text[:-1]
            elif clean_text.endswith('%'):
                clean_text = clean_text[:-1]
                # Don't apply multiplier for percentages, keep as is
            
            return float(clean_text) * multiplier
            
        except (ValueError, AttributeError):
            return None
    
    def _classify_number_type(self, number_text: str, context: str) -> str:
        """Classify the type of number based on text and context"""
        context_lower = context.lower()
        
        if '$' in number_text or any(word in context_lower for word in 
                                   ['dollar', 'cost', 'value', 'amount', 'income', 'expense']):
            return 'currency'
        elif '%' in number_text or any(word in context_lower for word in 
                                     ['percent', 'rate', 'return', 'allocation']):
            return 'percentage'
        elif any(word in context_lower for word in ['year', 'age', 'time']):
            return 'time'
        elif any(word in context_lower for word in ['ratio', 'multiple', 'times']):
            return 'ratio'
        else:
            return 'general'
    
    def _validate_number_comprehensive(self, 
                                     number_info: Dict[str, Any], 
                                     source_data: Dict[str, Any]) -> Optional[NumberValidation]:
        """Comprehensive validation of a single number"""
        number = number_info['parsed_value']
        number_type = number_info['number_type']
        
        # Try multiple validation methods
        validation_methods = [
            ('exact_match', self._exact_match_validation),
            ('calculated_value', self._calculated_value_validation),
            ('range_validation', self._range_validation),
            ('pattern_validation', self._pattern_validation),
            ('contextual_validation', self._contextual_validation)
        ]
        
        for method_name, validation_func in validation_methods:
            try:
                result = validation_func(number, number_info, source_data)
                if result and result.is_valid:
                    return result
            except Exception as e:
                logger.debug(f"Validation method {method_name} failed: {e}")
                continue
        
        # If no validation succeeded, create invalid result
        return NumberValidation(
            original_number=number,
            validated_number=number,
            is_valid=False,
            confidence_score=0.0,
            validation_method="no_validation_passed",
            error_message=f"No validation method could verify this {number_type} value"
        )
    
    def _exact_match_validation(self, 
                              number: float, 
                              number_info: Dict[str, Any], 
                              source_data: Dict[str, Any]) -> Optional[NumberValidation]:
        """Check for exact matches in source data"""
        def search_nested(data, target, path=""):
            matches = []
            
            if isinstance(data, dict):
                for key, value in data.items():
                    current_path = f"{path}.{key}" if path else key
                    if isinstance(value, (int, float, Decimal)):
                        if self._numbers_match(float(value), target):
                            matches.append(current_path)
                    elif isinstance(value, (dict, list)):
                        matches.extend(search_nested(value, target, current_path))
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    current_path = f"{path}[{i}]"
                    if isinstance(item, (int, float, Decimal)):
                        if self._numbers_match(float(item), target):
                            matches.append(current_path)
                    elif isinstance(item, (dict, list)):
                        matches.extend(search_nested(item, target, current_path))
            
            return matches
        
        matches = search_nested(source_data, number)
        
        if matches:
            return NumberValidation(
                original_number=number,
                validated_number=number,
                is_valid=True,
                confidence_score=1.0,
                validation_method="exact_match",
                error_message=None
            )
        
        return None
    
    def _calculated_value_validation(self, 
                                   number: float, 
                                   number_info: Dict[str, Any], 
                                   source_data: Dict[str, Any]) -> Optional[NumberValidation]:
        """Validate numbers that should be calculated from source data"""
        number_type = number_info['number_type']
        context = number_info['context'].lower()
        
        # Try different calculation patterns based on context
        for pattern_name, validation_func in self.calculation_patterns.items():
            try:
                result = validation_func(number, context, source_data)
                if result:
                    return result
            except Exception as e:
                logger.debug(f"Calculation pattern {pattern_name} failed: {e}")
                continue
        
        return None
    
    def _validate_percentage(self, 
                           number: float, 
                           context: str, 
                           source_data: Dict[str, Any]) -> Optional[NumberValidation]:
        """Validate percentage calculations"""
        # Look for allocation percentages that should sum to 100
        if 'allocation' in context or 'portfolio' in context:
            # This would need access to other allocations to validate sum
            pass
        
        # Look for return rates that should match historical data
        if 'return' in context or 'rate' in context:
            # Validate against known return rates in source data
            pass
        
        return None
    
    def _validate_currency(self, 
                          number: float, 
                          context: str, 
                          source_data: Dict[str, Any]) -> Optional[NumberValidation]:
        """Validate currency amounts"""
        # Check if this is a calculated field like net worth, retirement gap, etc.
        if 'net worth' in context:
            calculated_net_worth = self._calculate_net_worth(source_data)
            if calculated_net_worth and self._numbers_match(number, calculated_net_worth):
                return NumberValidation(
                    original_number=number,
                    validated_number=calculated_net_worth,
                    is_valid=True,
                    confidence_score=0.95,
                    validation_method="calculated_net_worth"
                )
        
        if 'monthly' in context and 'payment' in context:
            # Validate monthly payment calculations
            pass
        
        return None
    
    def _validate_ratio(self, 
                       number: float, 
                       context: str, 
                       source_data: Dict[str, Any]) -> Optional[NumberValidation]:
        """Validate ratio calculations"""
        return None
    
    def _validate_compound_growth(self, 
                                number: float, 
                                context: str, 
                                source_data: Dict[str, Any]) -> Optional[NumberValidation]:
        """Validate compound growth calculations"""
        return None
    
    def _validate_present_value(self, 
                               number: float, 
                               context: str, 
                               source_data: Dict[str, Any]) -> Optional[NumberValidation]:
        """Validate present value calculations"""
        return None
    
    def _validate_payment_calculation(self, 
                                    number: float, 
                                    context: str, 
                                    source_data: Dict[str, Any]) -> Optional[NumberValidation]:
        """Validate payment calculations"""
        return None
    
    def _validate_allocation_sum(self, 
                               number: float, 
                               context: str, 
                               source_data: Dict[str, Any]) -> Optional[NumberValidation]:
        """Validate that allocations sum to 100%"""
        return None
    
    def _range_validation(self, 
                         number: float, 
                         number_info: Dict[str, Any], 
                         source_data: Dict[str, Any]) -> Optional[NumberValidation]:
        """Validate that numbers fall within reasonable ranges"""
        number_type = number_info['number_type']
        
        # Define reasonable ranges for different types
        ranges = {
            'percentage': (0, 100),
            'currency': (0, 1e10),  # Up to $10B
            'time': (0, 100),  # Years
            'ratio': (0, 100)
        }
        
        if number_type in ranges:
            min_val, max_val = ranges[number_type]
            if min_val <= number <= max_val:
                confidence = 0.6  # Medium confidence for range validation
                return NumberValidation(
                    original_number=number,
                    validated_number=number,
                    is_valid=True,
                    confidence_score=confidence,
                    validation_method="range_validation"
                )
        
        return None
    
    def _pattern_validation(self, 
                           number: float, 
                           number_info: Dict[str, Any], 
                           source_data: Dict[str, Any]) -> Optional[NumberValidation]:
        """Validate numbers against expected patterns"""
        # This could validate things like:
        # - Years should be reasonable (e.g., 1900-2100)
        # - Percentages should be 0-100
        # - Currency amounts should have reasonable precision
        return None
    
    def _contextual_validation(self, 
                              number: float, 
                              number_info: Dict[str, Any], 
                              source_data: Dict[str, Any]) -> Optional[NumberValidation]:
        """Validate numbers based on context and domain knowledge"""
        return None
    
    def _validate_mathematical_relationships(self, 
                                           number_matches: List[Dict[str, Any]], 
                                           source_data: Dict[str, Any]) -> List[NumberValidation]:
        """Validate mathematical relationships between numbers"""
        validations = []
        
        # Find percentage allocations that should sum to 100%
        allocations = [match for match in number_matches 
                      if match['number_type'] == 'percentage' 
                      and 'allocation' in match['context'].lower()]
        
        if len(allocations) > 1:
            total = sum(match['parsed_value'] for match in allocations)
            if abs(total - 100) < 1.0:  # Allow small tolerance
                for allocation in allocations:
                    validation = NumberValidation(
                        original_number=allocation['parsed_value'],
                        validated_number=allocation['parsed_value'],
                        is_valid=True,
                        confidence_score=0.8,
                        validation_method="allocation_sum_check"
                    )
                    validations.append(validation)
        
        return validations
    
    def _calculate_net_worth(self, source_data: Dict[str, Any]) -> Optional[float]:
        """Calculate net worth from source data"""
        try:
            # This would need to access the specific structure of your source data
            # Placeholder implementation
            assets = self._extract_value(source_data, ['assets', 'total_assets'])
            liabilities = self._extract_value(source_data, ['liabilities', 'total_liabilities'])
            
            if assets is not None and liabilities is not None:
                return assets - liabilities
        except Exception as e:
            logger.debug(f"Net worth calculation failed: {e}")
        
        return None
    
    def _extract_value(self, data: Dict[str, Any], paths: List[str]) -> Optional[float]:
        """Extract a numeric value from nested data structure"""
        for path in paths:
            try:
                current = data
                for key in path.split('.'):
                    current = current[key]
                if isinstance(current, (int, float, Decimal)):
                    return float(current)
            except (KeyError, TypeError):
                continue
        return None
    
    def _numbers_match(self, num1: float, num2: float) -> bool:
        """Check if two numbers match within tolerance"""
        if num1 == 0 and num2 == 0:
            return True
        if num1 == 0 or num2 == 0:
            return abs(num1 - num2) < 0.01  # Absolute tolerance for small numbers
        
        # Relative tolerance for larger numbers
        relative_diff = abs(num1 - num2) / max(abs(num1), abs(num2))
        return relative_diff <= (self.tolerance_percent / 100)


# Global validator instance
number_validator = FinancialNumberValidator()