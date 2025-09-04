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
                    # Decrease patterns
                    r'(?i).*reduce.*goal.*(\$?[\d,M]+)',
                    r'(?i).*lower.*goal.*(\$?[\d,M]+)',
                    r'(?i).*decrease.*goal.*(\$?[\d,M]+)',
                    
                    # Increase patterns
                    r'(?i).*increase.*goal.*(\$?[\d,M]+)',
                    r'(?i).*raise.*goal.*(\$?[\d,M]+)',
                    r'(?i).*higher.*goal.*(\$?[\d,M]+)',
                    
                    # General adjustment patterns
                    r'(?i).*change.*goal.*to.*(\$?[\d,M]+)',
                    r'(?i).*adjust.*goal.*to.*(\$?[\d,M]+)',
                    r'(?i).*set.*goal.*to.*(\$?[\d,M]+)',
                    r'(?i).*goal.*to.*(\$?[\d,M]+)',
                    r'(?i).*my goal is.*(\$?[\d,M]+)',
                    r'(?i).*if.*goal.*(\$?[\d,M]+)',
                    
                    # Timeline impact patterns
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
                    r'(?i).*monthly.*contribution.*goal',
                    # Timeframe variants (e.g., "in 5 years")
                    r'(?i).*save.*monthly.*in\s*(\d{1,3})\s*years',
                    r'(?i).*reach.*\$?[\d,\.]+.*in\s*(\d{1,3})\s*years'
                ],
                'required_params': ['current_assets', 'target_goal', 'years'],
                'optional_params': ['growth_rate'],
                'extract_numbers': True,
                'extract_years': True
            },
            
            'growth_rate_impact': {
                'patterns': [
                    r'(?i).*(\d+(?:\.\d+)?)%.*growth',
                    r'(?i).*growth.*(\d+(?:\.\d+)?)%',
                    r'(?i).*(\d+(?:\.\d+)?)%.*return',
                    r'(?i).*consider.*(\d+(?:\.\d+)?)%',
                    r'(?i).*assume.*(\d+(?:\.\d+)?)%',
                    r'(?i).*investment.*growth.*(\d+(?:\.\d+)?)%',
                    r'(?i).*(\d+(?:\.\d+)?)%.*investment'
                ],
                'extract_growth_rate': True,
                'redirect_to': 'compound_growth_scenarios'  # Show investment growth scenarios
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
                    r'(?i).*growth.*scenarios',
                    # Net worth projection phrasing
                    r'(?i).*net\s*worth.*in\s*(\d{1,3})\s*years',
                    r'(?i)in\s*(\d{1,3})\s*years.*net\s*worth',
                    # Time-bound goal phrasing – route to scenarios (goal_for_timeframe)
                    r'(?i).*retir.*in\s*(\d{1,3})\s*years.*goal',
                    r'(?i).*in\s*(\d{1,3})\s*years.*what.*goal'
                ],
                'required_params': ['principal', 'years'],
                'optional_params': ['rates', 'monthly_contributions'],
                'extract_years': True
            }
        }

        # Add withdrawal sustainability mapping (safe withdrawal)
        self.CALCULATION_PATTERNS['withdrawal_sustainability'] = {
            'patterns': [
                r'(?i).*safe.*withdraw',
                r'(?i).*withdraw\s*(\d+(?:\.\d+)?)%.*',
                r'(?i).*withdrawal.*sustain',
            ],
            'required_params': ['assets', 'annual_withdrawal', 'years_needed'],
            'optional_params': ['growth_rate'],
            'extract_withdraw_percent': True
        }
    
    def detect_calculation_needed(self, user_message: str, conversation_history: List[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        Detect if user query requires calculation and return calculation info
        """
        
        # First check for explicit mathematical keywords
        math_indicators = [
            'calculate', 'years', 'timeline', 'how long', 'when can', 'growth rate',
            'percentage', '%', 'months', 'savings needed', 'required', 'goal',
            'shave off', 'reduce', 'increase', 'raise', 'lower', 'tax rate', 'contribution'
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
                    if config.get('extract_years'):
                        years = self._extract_years(user_message, match)
                        if years:
                            detection_result['extracted_years'] = years
                    
                    return detection_result
        
        # Fallback: check conversation context for calculation hints
        fallback = self._check_conversation_context(user_message, conversation_history)
        # Heuristics: handle "reduce/increase to $X" or "reduce/increase by $X" without 'goal'
        if not fallback:
            reduce_inc = re.search(r"(?i).*(reduce|increase|raise|lower)\s+to\s+(\$?[\d,\.]+(?:[Mm]illion|[Mm])?)", user_message)
            if reduce_inc:
                numbers = self._extract_numbers_from_message(user_message)
                return {
                    'calculation_type': 'retirement_goal_adjustment',
                    'confidence': 0.7,
                    'pattern_matched': 'reduce/increase to',
                    'required_params': self.CALCULATION_PATTERNS['retirement_goal_adjustment']['required_params'],
                    'optional_params': self.CALCULATION_PATTERNS['retirement_goal_adjustment'].get('optional_params', []),
                    'extract_numbers': True,
                    'extracted_numbers': numbers,
                }
        if not fallback:
            reduce_by = re.search(r"(?i).*(reduce|lower|decrease|increase|raise)\s+.*?by\s+(\$?[\d,\.]+(?:[Kk]|[Mm]illion|[Mm])?)", user_message)
            if reduce_by:
                numbers = self._extract_numbers_from_message(user_message)
                return {
                    'calculation_type': 'retirement_goal_adjustment',
                    'confidence': 0.65,
                    'pattern_matched': 'reduce/increase by',
                    'required_params': self.CALCULATION_PATTERNS['retirement_goal_adjustment']['required_params'],
                    'optional_params': self.CALCULATION_PATTERNS['retirement_goal_adjustment'].get('optional_params', []),
                    'extract_numbers': True,
                    'extracted_numbers': numbers,
                }
        return fallback
    
    def extract_calculation_params(self, user_message: str, user_context: Dict, 
                                 calculation_info: Dict) -> Dict[str, Any]:
        """
        Extract calculation parameters from user message and context
        """
        
        calc_type = calculation_info['calculation_type']
        params = {}
        
        # Standard parameter mapping from user context
        # Note: user_context is the 'facts' object from identity_math.compute_claims
        
        # Get values from _context if available
        context_data = user_context.get('_context', {})
        
        param_mapping = {
            'current_assets': self._get_current_assets(user_context),
            'target_goal': context_data.get('retirement_goal', user_context.get('retirement_goal_amount', 3500000)),
            'monthly_additions': user_context.get('monthly_surplus', 0),
            'income': user_context.get('monthly_income', 0) * 12,  # Convert to annual
            'salary': user_context.get('monthly_income', 0) * 12,   # Convert to annual
            'current_401k': user_context.get('annual_401k', 0),  # Already annual
            'current_fund': user_context.get('liquid_assets', 0),
            'monthly_expenses': user_context.get('monthly_expenses', 0),
            'age': context_data.get('age', 55),  # Default to 55 if not found
            'state': context_data.get('state', 'NC'),
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

        if 'extracted_years' in calculation_info:
            params['years'] = calculation_info['extracted_years']

        # Withdrawal sustainability special handling
        if calc_type == 'withdrawal_sustainability':
            # Assets from context
            params['assets'] = params.get('assets', self._get_current_assets(user_context))
            # Years needed default 30 if not extracted
            params['years_needed'] = params.get('years_needed', 30)
            # Annual withdrawal from dollar number or percent
            withdraw_annual = None
            # Dollar values in message
            if 'extracted_numbers' in calculation_info and calculation_info['extracted_numbers']:
                # Take the largest positive as annual withdrawal
                withdraw_annual = max(calculation_info['extracted_numbers'])
            if not withdraw_annual:
                # Try to extract percentage and apply to assets
                pct = self._extract_percentage(user_message)
                if pct and params['assets']:
                    withdraw_annual = float(params['assets']) * (pct / 100.0)
            if not withdraw_annual and params.get('assets'):
                # Default to 4% rule
                withdraw_annual = float(params['assets']) * 0.04
            params['annual_withdrawal'] = withdraw_annual or 0
        
        # Special handling for specific calculation types
        if calc_type == 'retirement_goal_adjustment':
            params.update(self._handle_goal_adjustment_params(user_message, user_context, calculation_info))
        
        elif calc_type == 'compound_growth_scenarios':
            # If user specified a growth rate, use it plus scenarios around it
            if 'growth_rate' in params:
                user_rate = params.pop('growth_rate')  # Remove from params
                params['rates'] = [user_rate - 0.02, user_rate, user_rate + 0.02]
            else:
                params['rates'] = [0.05, 0.07, 0.09]  # Default scenario rates
            # Determine principal from user context (net worth preferred)
            params['principal'] = self._get_current_assets(user_context)
            # Ensure we have years parameter
            if 'years' not in params:
                params['years'] = 10  # Default 10 year projection
            # Use monthly surplus as monthly contributions if available
            if 'monthly_contributions' not in params:
                params['monthly_contributions'] = user_context.get('monthly_surplus', 0)

        return params
    
    def _get_current_assets(self, user_context: Dict) -> float:
        """Get total assets that count toward retirement"""
        
        # Primary: Use net_worth if available (most accurate)
        if 'net_worth' in user_context and user_context['net_worth'] > 0:
            return user_context['net_worth']
        
        # Secondary: Use total_assets if available
        if 'total_assets' in user_context and user_context['total_assets'] > 0:
            return user_context['total_assets']
        
        # Fallback: Calculate net worth from assets - liabilities
        total_assets = user_context.get('total_assets', 0)
        total_liabilities = user_context.get('total_liabilities', 0)
        if total_assets > 0:
            return max(0, total_assets - total_liabilities)
        
        # Last resort: Sum up individual asset categories
        assets = 0
        asset_fields = [
            'retirement_total', 'investment_total', 'liquid_assets'
        ]
        
        for field in asset_fields:
            assets += user_context.get(field, 0)
        
        # Log warning if we still have zero
        if assets == 0:
            logger.warning(f"Could not extract current assets from context: {list(user_context.keys())}")
        
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
        
        # Pattern 2: Plain numbers with million/M or thousand/K suffix
        million_pattern = r'(\d+(?:[.,]\d+)*)\s*([Mm]illion|[Mm])\b'
        for match in re.finditer(million_pattern, message):
            number_str = match.group(1).replace(',', '')
            try:
                value = float(number_str) * 1000000
                numbers.append(value)
            except ValueError:
                continue

        thousand_pattern = r'(\d+(?:[.,]\d+)*)\s*([Kk])\b'
        for match in re.finditer(thousand_pattern, message):
            number_str = match.group(1).replace(',', '')
            try:
                value = float(number_str) * 1000
                numbers.append(value)
            except ValueError:
                continue
        
        # Pattern 3: Numbers with commas (proper and improper formatting)
        # This handles both 2,500,000 and 2,500000 formats
        comma_number_pattern = r'\b(\d+,\d+(?:,\d+)*)\b'
        for match in re.finditer(comma_number_pattern, message):
            try:
                # Handle cases like 2,500000 by treating as 2,500,000
                number_str = match.group(1)
                # If we have something like 2,500000 (comma but then 6 digits), fix it
                if ',' in number_str:
                    parts = number_str.split(',')
                    if len(parts) == 2 and len(parts[1]) == 6:  # Like 2,500000
                        # Treat as 2500000
                        value = float(parts[0] + parts[1])
                    else:
                        # Normal comma-separated number
                        value = float(number_str.replace(',', ''))
                    
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

    def _extract_percentage(self, message: str) -> float:
        """Extract the first percentage value from the message if present."""
        import re
        m = re.search(r'(\d+(?:\.\d+)?)\s*%', message)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                return None
        return None

    def _extract_years(self, message: str, match_obj) -> int:
        """Extract horizon in years from message."""
        # Try capturing group first
        if match_obj and match_obj.groups():
            for g in match_obj.groups():
                if g and g.isdigit():
                    try:
                        val = int(g)
                        if 1 <= val <= 100:
                            return val
                    except ValueError:
                        pass
        # Fallback generic search
        m = re.search(r"(?i)in\s*(\d{1,3})\s*years", message)
        if m:
            try:
                val = int(m.group(1))
                if 1 <= val <= 100:
                    return val
            except ValueError:
                pass
        return None
    
    def _map_extracted_numbers(self, numbers: List[float], calc_type: str) -> Dict[str, float]:
        """Map extracted numbers to appropriate parameters"""

        if not numbers:
            return {}

        if calc_type == 'retirement_goal_adjustment':
            if len(numbers) >= 1:
                # Take the largest number as the new goal (handles duplicates from different patterns)
                return {'new_goal': max(numbers)}

        if calc_type == 'required_monthly_savings':
            # Use the largest amount as target goal
            return {'target_goal': max(numbers)}

        return {}
    
    def _handle_goal_adjustment_params(self, message: str, user_context: Dict, 
                                     calculation_info: Dict) -> Dict[str, Any]:
        """Special handling for goal adjustment calculations"""

        params = {}

        # Get original goal from context - avoid hardcoding
        default_goal = user_context.get('_context', {}).get('retirement_goal', 3500000)
        params['original_goal'] = user_context.get('retirement_goal_amount', default_goal)

        # Try to extract new goal from message
        if 'extracted_numbers' in calculation_info:
            numbers = calculation_info['extracted_numbers']
            pattern = calculation_info.get('pattern_matched', '')
            # Only set absolute target when matched pattern indicates 'to'
            if numbers and ('to' in pattern):
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

        # Handle relative adjustments like "reduce by $200k" or "increase by 500000"
        if 'new_goal' not in params:
            rel = re.search(r"(?i)(reduce|lower|decrease|increase|raise)\s+.*?by\s+(\$?[\d,\.]+(?:[Kk]|[Mm]illion|[Mm])?)", message)
            if rel:
                numbers = self._extract_numbers_from_message(message)
                if numbers:
                    delta = numbers[0]
                    original = params.get('original_goal', default_goal)
                    verb = rel.group(1).lower()
                    if verb in ['reduce', 'lower', 'decrease']:
                        params['new_goal'] = max(0, original - delta)
                    else:
                        params['new_goal'] = original + delta

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
