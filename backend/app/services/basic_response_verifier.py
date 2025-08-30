"""
Basic Response Verifier - Task 1.5
Simple verifier that detects numbers in chat responses and compares them to calculated financial data
"""
import re
from typing import Dict, List, Tuple, Any
from app.models.architecture_contracts import ToolsOutput, UserFinancialData
import structlog

logger = structlog.get_logger()


class BasicResponseVerifier:
    """
    Simple response verifier that detects financial numbers in text 
    and compares them to our calculated data
    """
    
    def __init__(self):
        """Initialize with regex patterns for financial numbers"""
        # Percentage pattern: matches "54.4%" or "8.5%" etc
        self.percentage_pattern = re.compile(r'(\d+\.?\d*)%')
        
        # Money pattern: matches "$200,000" or "$9,653" or "$50" etc
        self.money_pattern = re.compile(r'\$([0-9,]+)')
        
        # Number with months pattern: matches "24.7 months" or "5 months"
        self.months_pattern = re.compile(r'(\d+\.?\d*)\s*months?')
        
        # General number pattern for backup
        self.number_pattern = re.compile(r'\b(\d+\.?\d*)\b')

    def verify_response_numbers(self, response_text: str, tools_output: ToolsOutput) -> Dict[str, Any]:
        """
        Find numbers in response and check if they match our calculations
        Returns verification results for logging
        """
        try:
            verification_results = {
                'found_numbers': {},
                'matches': [],
                'mismatches': [],
                'summary': 'No verification performed'
            }
            
            if not response_text or not tools_output:
                verification_results['summary'] = 'Missing response text or tools output'
                return verification_results
            
            # Extract different types of numbers from response
            percentages = self._extract_percentages(response_text)
            money_amounts = self._extract_money_amounts(response_text)
            month_numbers = self._extract_month_numbers(response_text)
            
            verification_results['found_numbers'] = {
                'percentages': percentages,
                'money_amounts': money_amounts,
                'month_numbers': month_numbers
            }
            
            # Compare found numbers to our calculated values
            matches, mismatches = self._compare_to_calculations(
                percentages, money_amounts, month_numbers, tools_output
            )
            
            verification_results['matches'] = matches
            verification_results['mismatches'] = mismatches
            verification_results['summary'] = self._generate_summary(matches, mismatches)
            
            return verification_results
            
        except Exception as e:
            logger.error(f"Response verification failed: {str(e)}")
            return {
                'found_numbers': {},
                'matches': [],
                'mismatches': [],
                'summary': f'Verification error: {str(e)}'
            }

    def _extract_percentages(self, text: str) -> List[float]:
        """Extract percentage values from text"""
        matches = self.percentage_pattern.findall(text)
        percentages = []
        for match in matches:
            try:
                percentages.append(float(match))
            except ValueError:
                continue
        return percentages

    def _extract_money_amounts(self, text: str) -> List[float]:
        """Extract money amounts from text"""
        matches = self.money_pattern.findall(text)
        amounts = []
        for match in matches:
            try:
                # Remove commas and convert to float
                clean_amount = match.replace(',', '')
                amounts.append(float(clean_amount))
            except ValueError:
                continue
        return amounts

    def _extract_month_numbers(self, text: str) -> List[float]:
        """Extract numbers associated with months from text"""
        matches = self.months_pattern.findall(text)
        month_values = []
        for match in matches:
            try:
                month_values.append(float(match))
            except ValueError:
                continue
        return month_values

    def _compare_to_calculations(self, percentages: List[float], money_amounts: List[float], 
                               month_numbers: List[float], tools_output: ToolsOutput) -> Tuple[List[str], List[str]]:
        """Compare found numbers to our calculated values"""
        matches = []
        mismatches = []
        
        # Check percentages against our calculations
        calculated_percentages = [
            tools_output.savings_rate,
            tools_output.debt_to_income_ratio
        ]
        
        for found_pct in percentages:
            matched = False
            for calc_name, calc_value in [
                ('savings_rate', tools_output.savings_rate),
                ('debt_to_income_ratio', tools_output.debt_to_income_ratio)
            ]:
                if self._numbers_match(found_pct, calc_value):
                    matches.append(f"Percentage {found_pct}% matches calculated {calc_name}: {calc_value:.1f}%")
                    matched = True
                    break
            
            if not matched:
                mismatches.append(f"Percentage {found_pct}% does not match any calculated values")
        
        # Check month numbers against liquidity calculation
        for found_months in month_numbers:
            if self._numbers_match(found_months, tools_output.liquidity_months):
                matches.append(f"Months {found_months} matches calculated liquidity: {tools_output.liquidity_months:.1f} months")
            else:
                mismatches.append(f"Months {found_months} does not match calculated liquidity: {tools_output.liquidity_months:.1f} months")
        
        # Check money amounts against net worth and user data (if available)
        for found_amount in money_amounts:
            matched = False
            # Check against net worth
            if self._numbers_match(found_amount, tools_output.net_worth, tolerance=0.05):  # 5% tolerance for large amounts
                matches.append(f"Amount ${found_amount:,.0f} matches calculated net worth: ${tools_output.net_worth:,.0f}")
                matched = True
            
            # Check against user financial data if available
            if hasattr(tools_output, 'raw_data_used') and tools_output.raw_data_used:
                user_data = tools_output.raw_data_used
                for field_name, field_value in [
                    ('monthly_income', user_data.monthly_income),
                    ('monthly_expenses', user_data.monthly_expenses),
                    ('cash_reserves', user_data.cash_reserves),
                    ('total_assets', user_data.total_assets),
                    ('total_debts', user_data.total_debts)
                ]:
                    if self._numbers_match(found_amount, field_value, tolerance=0.05):
                        matches.append(f"Amount ${found_amount:,.0f} matches {field_name}: ${field_value:,.0f}")
                        matched = True
                        break
            
            if not matched and found_amount > 100:  # Only flag larger amounts as mismatches
                mismatches.append(f"Amount ${found_amount:,.0f} does not match any calculated values")
        
        return matches, mismatches

    def _numbers_match(self, found: float, calculated: float, tolerance: float = 0.01) -> bool:
        """Check if two numbers match within tolerance"""
        if calculated == 0:
            return abs(found) < 0.01
        
        # Use relative tolerance for comparison
        relative_diff = abs(found - calculated) / abs(calculated)
        return relative_diff <= tolerance

    def _generate_summary(self, matches: List[str], mismatches: List[str]) -> str:
        """Generate a summary of verification results"""
        total_checks = len(matches) + len(mismatches)
        
        if total_checks == 0:
            return "No financial numbers detected in response"
        
        match_count = len(matches)
        mismatch_count = len(mismatches)
        
        if mismatch_count == 0:
            return f"All {match_count} detected numbers match calculations ✅"
        elif match_count == 0:
            return f"None of {mismatch_count} detected numbers match calculations ❌"
        else:
            return f"{match_count} matches, {mismatch_count} mismatches out of {total_checks} detected numbers"