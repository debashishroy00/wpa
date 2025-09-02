"""
Calculation Router
Detects when user queries require mathematical calculations and routes to appropriate calculator
"""

import re
from typing import Dict, List, Optional, Any
import structlog

logger = structlog.get_logger()


class CalculationRouter:
    """Routes user queries to appropriate calculation methods"""
    
    def __init__(self):
        # Calculation trigger patterns
        self.CALCULATION_PATTERNS = {
            'years_to_retirement_goal': {
                'patterns': [
                    r'(?i).*when can i retire',
                    r'(?i).*how long.*retirement',
                    r'(?i).*years.*retirement goal',
                    r'(?i).*timeline.*retirement',
                    r'(?i).*reach.*retirement goal',
                    r'(?i).*on track.*retirement',
                    r'(?i).*track.*retirement goal',
                    r'(?i).*retirement.*on track'
                ],
                'required_params': ['current_assets', 'target_goal'],
                'optional_params': ['monthly_additions', 'growth_rate']
            },
            
            'retirement_goal_adjustment': {
                'patterns': [
                    r'(?i).*reduce.*goal.*(\$?[\d,M]+)',
                    r'(?i).*change.*goal.*(\$?[\d,M]+)',
                    r'(?i).*goal.*(\$?[\d,M]+).*years.*save',
                    r'(?i).*years.*save.*goal.*(\$?[\d,M]+)',
                    r'(?i).*shave.*years.*goal.*(\$?[\d,M]+)',
                    r'(?i).*(\$?[\d,M]+).*goal.*timeline',
                    r'(?i).*how many years.*shave.*off',
                    r'(?i).*years.*can.*shave',
                    r'(?i).*shave.*years'
                ],
                'required_params': ['current_assets', 'original_goal', 'new_goal'],
                'optional_params': ['monthly_additions', 'growth_rate'],
                'extract_numbers': True
            },
            
            'required_monthly_savings': {
                'patterns': [
                    r'(?i).*how much.*save.*month',
                    r'(?i).*monthly.*savings.*needed',
                    r'(?i).*save.*month.*reach',
                    r'(?i).*monthly.*contribution.*goal'
                ],
                'required_params': ['current_assets', 'target_goal', 'years'],
                'optional_params': ['growth_rate']
            },
            
            'growth_rate_impact': {
                'patterns': [
                    r'(?i).*(\d+)%.*growth.*rate',
                    r'(?i).*growth.*rate.*(\d+)',
                    r'(?i).*(\d+)%.*return',
                    r'(?i).*consider.*(\d+)%',
                    r'(?i).*assume.*(\d+)%'
                ],
                'extract_growth_rate': True,
                'redirect_to': 'years_to_retirement_goal'  # Usually what they want
            },
            
            'tax_analysis': {
                'patterns': [
                    r'(?i).*tax.*rate',
                    r'(?i).*marginal.*tax',
                    r'(?i).*tax.*bracket',
                    r'(?i).*effective.*tax'
                ],
                'required_params': ['income'],
                'optional_params': ['state', 'filing_status']
            },
            
            'retirement_contribution_optimization': {
                'patterns': [
                    r'(?i).*401k.*contribution',
                    r'(?i).*max.*401k',
                    r'(?i).*increase.*401k',
                    r'(?i).*401k.*tax.*savings'
                ],
                'required_params': ['salary', 'current_401k'],
                'optional_params': ['age']
            },
            
            'emergency_fund_analysis': {
                'patterns': [
                    r'(?i).*emergency.*fund',
                    r'(?i).*emergency.*savings',
                    r'(?i).*months.*expenses.*saved'
                ],
                'required_params': ['current_fund', 'monthly_expenses'],
                'optional_params': ['target_months']
            },
            
            'compound_growth_scenarios': {
                'patterns': [
                    r'(?i).*compound.*growth',
                    r'(?i).*investment.*growth',
                    r'(?i).*portfolio.*growth',
                    r'(?i).*growth.*scenarios'
                ],
                'required_params': ['principal', 'years'],
                'optional_params': ['rates', 'monthly_contributions']
            }
        }
    
    def detect_calculation_needed(self, user_message: str, conversation_history: List[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        Detect if user query requires calculation and return calculation info
        """
        
        # First check for explicit mathematical keywords
        math_indicators = [
            'calculate', 'years', 'timeline', 'how long', 'when can', 'growth rate',
            'percentage', '%', 'months', 'savings needed', 'required', 'goal',
            'shave off', 'reduce goal', 'tax rate', 'contribution'
        ]
        
        if not any(indicator in user_message.lower() for indicator in math_indicators):
            return None
        
        # Try to match specific calculation patterns
        for calc_type, config in self.CALCULATION_PATTERNS.items():
            for pattern in config['patterns']:
                match = re.search(pattern, user_message)
                if match:
                    logger.info(f"Detected calculation type: {calc_type} from pattern: {pattern}")
                    
                    detection_result = {
                        'calculation_type': calc_type,
                        'confidence': 0.9,
                        'pattern_matched': pattern,
                        'required_params': config['required_params'],
                        'optional_params': config.get('optional_params', [])
                    }
                    
                    # Extract specific values if configured
                    if config.get('extract_numbers'):
                        numbers = self._extract_numbers_from_message(user_message)
                        detection_result['extracted_numbers'] = numbers
                    
                    if config.get('extract_growth_rate'):
                        growth_rate = self._extract_growth_rate(user_message, match)
                        detection_result['extracted_growth_rate'] = growth_rate
                        # Redirect to actual calculation type if specified
                        if 'redirect_to' in config:
                            detection_result['calculation_type'] = config['redirect_to']
                    
                    return detection_result
        
        # Fallback: check conversation context for calculation hints
        return self._check_conversation_context(user_message, conversation_history)
    
    def extract_calculation_params(self, user_message: str, user_context: Dict, 
                                 calculation_info: Dict) -> Dict[str, Any]:
        """
        Extract calculation parameters from user message and context
        """
        
        calc_type = calculation_info['calculation_type']
        params = {}
        
        # Standard parameter mapping from user context
        param_mapping = {
            'current_assets': self._get_current_assets(user_context),
            'target_goal': user_context.get('retirement_goal_amount', 3500000),
            'monthly_additions': user_context.get('monthly_surplus', 0),
            'income': user_context.get('monthly_income', 0) * 12,  # Convert to annual
            'salary': user_context.get('monthly_income', 0) * 12,   # Convert to annual
            'current_401k': user_context.get('retirement_contribution_monthly', 0) * 12,
            'current_fund': user_context.get('liquid_assets', user_context.get('cash_total', 0)),
            'monthly_expenses': user_context.get('monthly_expenses', 0),
            'age': user_context.get('age', user_context.get('_context', {}).get('age')),
            'state': user_context.get('state', 'NC'),
            'filing_status': 'married'  # Default assumption
        }
        
        # Extract required parameters
        for param in calculation_info['required_params']:
            if param in param_mapping:
                params[param] = param_mapping[param]
            else:
                logger.warning(f"Required parameter {param} not found in context")
        
        # Extract optional parameters
        for param in calculation_info.get('optional_params', []):
            if param in param_mapping:
                params[param] = param_mapping[param]
        
        # Handle specific extraction from message
        if 'extracted_numbers' in calculation_info:
            params.update(self._map_extracted_numbers(calculation_info['extracted_numbers'], calc_type))
        
        if 'extracted_growth_rate' in calculation_info:
            params['growth_rate'] = calculation_info['extracted_growth_rate']
        
        # Special handling for specific calculation types
        if calc_type == 'retirement_goal_adjustment':
            params.update(self._handle_goal_adjustment_params(user_message, user_context, calculation_info))
        
        elif calc_type == 'compound_growth_scenarios':
            params['rates'] = [0.05, 0.07, 0.09]  # Default scenario rates
            params['principal'] = params.get('current_assets', 0)
        
        return params
    
    def _get_current_assets(self, user_context: Dict) -> float:
        """Get total assets that count toward retirement"""
        
        # Try multiple ways to get current retirement-relevant assets
        if 'net_worth' in user_context:
            return user_context['net_worth']
        
        if 'total_assets' in user_context:
            return user_context['total_assets']
        
        # Sum up individual asset categories
        assets = 0
        asset_fields = [
            'retirement_total', 'investment_total', 'liquid_assets', 
            'cash_total', 'home_equity', 'bitcoin_value'
        ]
        
        for field in asset_fields:
            assets += user_context.get(field, 0)
        
        return assets
    
    def _extract_numbers_from_message(self, message: str) -> List[float]:
        """Extract monetary amounts from message"""
        
        numbers = []
        
        # Pattern 1: Dollar amounts like $3M, $3,000,000, $1.5M
        dollar_pattern = r'\$(\d+(?:[.,]\d+)*)\s*([Mm]illion|[Mm])?'
        for match in re.finditer(dollar_pattern, message):
            number_str = match.group(1).replace(',', '')
            multiplier_str = match.group(2)
            
            try:
                value = float(number_str)
                if multiplier_str and multiplier_str.lower().startswith('m'):
                    value *= 1000000
                numbers.append(value)
            except ValueError:
                continue
        
        # Pattern 2: Plain numbers with million/M suffix
        million_pattern = r'(\d+(?:[.,]\d+)*)\s*([Mm]illion|[Mm])\b'
        for match in re.finditer(million_pattern, message):
            number_str = match.group(1).replace(',', '')
            try:
                value = float(number_str) * 1000000
                numbers.append(value)
            except ValueError:
                continue
        
        # Pattern 3: Large plain numbers (likely dollar amounts) including with commas
        large_number_pattern = r'\b(\d{1,3}(?:,\d{3})*)\b'  # Numbers with commas like 2,500,000
        for match in re.finditer(large_number_pattern, message):
            try:
                value = float(match.group(1).replace(',', ''))
                if value >= 1000:  # Only consider significant amounts
                    numbers.append(value)
            except ValueError:
                continue
        
        # Pattern 4: Numbers without commas but 6+ digits
        plain_number_pattern = r'\b(\d{6,})\b'  # 6+ digits like 2500000
        for match in re.finditer(plain_number_pattern, message):
            try:
                value = float(match.group(1))
                numbers.append(value)
            except ValueError:
                continue
        
        # Remove duplicates and sort
        return sorted(list(set(numbers)))
    
    def _extract_growth_rate(self, message: str, match_obj) -> float:
        """Extract growth rate percentage from message"""
        
        # Try to find percentage in the match
        if match_obj and match_obj.groups():
            rate_str = match_obj.groups()[0]
            try:
                rate_value = float(rate_str)
                # Convert percentage to decimal (7% -> 0.07)
                return rate_value / 100 if rate_value > 1 else rate_value
            except ValueError:
                pass
        
        # Fallback: search for any percentage in message
        pct_matches = re.findall(r'(\d+(?:\.\d+)?)\s*%', message)
        if pct_matches:
            try:
                return float(pct_matches[0]) / 100
            except ValueError:
                pass
        
        return 0.07  # Default 7%
    
    def _map_extracted_numbers(self, numbers: List[float], calc_type: str) -> Dict[str, float]:
        """Map extracted numbers to appropriate parameters"""
        
        if not numbers:
            return {}
        
        if calc_type == 'retirement_goal_adjustment':
            if len(numbers) >= 1:
                # First number is likely the new goal
                return {'new_goal': numbers[0]}
        
        return {}
    
    def _handle_goal_adjustment_params(self, message: str, user_context: Dict, 
                                     calculation_info: Dict) -> Dict[str, Any]:
        """Special handling for goal adjustment calculations"""
        
        params = {}
        
        # Get original goal from context
        params['original_goal'] = user_context.get('retirement_goal_amount', 3500000)
        
        # Try to extract new goal from message
        if 'extracted_numbers' in calculation_info:
            numbers = calculation_info['extracted_numbers']
            if numbers:
                params['new_goal'] = numbers[0]
        else:
            # Try common goal amounts mentioned in text
            goal_phrases = {
                '3m': 3000000,
                '3 m': 3000000,
                '3 million': 3000000,
                '2.5m': 2500000,
                '2.5 million': 2500000
            }
            
            message_lower = message.lower()
            for phrase, amount in goal_phrases.items():
                if phrase in message_lower:
                    params['new_goal'] = amount
                    break
        
        return params
    
    def _check_conversation_context(self, message: str, conversation_history: List[Dict]) -> Optional[Dict[str, Any]]:
        """Check if previous conversation provides calculation context"""
        
        if not conversation_history:
            return None
        
        # Look for mathematical follow-up questions
        followup_patterns = [
            r'(?i)what if',
            r'(?i)how about',
            r'(?i)consider',
            r'(?i)instead'
        ]
        
        for pattern in followup_patterns:
            if re.search(pattern, message):
                # This might be a follow-up calculation
                return {
                    'calculation_type': 'followup_calculation',
                    'confidence': 0.6,
                    'requires_context': True
                }
        
        return None


# Global instance
calculation_router = CalculationRouter()