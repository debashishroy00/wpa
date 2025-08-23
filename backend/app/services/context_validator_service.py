"""
Context Validation and Benchmarking Service
Validates financial advice context against industry benchmarks before responding
Ensures accurate, compliant, and appropriate financial guidance
"""

from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime
import structlog
from enum import Enum
from dataclasses import dataclass

logger = structlog.get_logger()

class ValidationSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ValidationResult:
    severity: ValidationSeverity
    category: str
    message: str
    recommendation: Optional[str] = None
    benchmark_reference: Optional[str] = None

class ContextValidatorService:
    """Validates financial context against benchmarks and best practices"""
    
    def __init__(self):
        # Industry benchmarks and thresholds
        self.benchmarks = {
            'emergency_fund': {
                'min_months': 3,
                'recommended_months': 6,
                'conservative_months': 12
            },
            'debt_to_income': {
                'excellent': 0.20,  # Below 20%
                'good': 0.36,       # 20-36%
                'concerning': 0.50, # 36-50%
                'critical': 0.50    # Above 50%
            },
            'savings_rate': {
                'minimum': 0.10,    # 10%
                'good': 0.20,       # 20%
                'excellent': 0.30   # 30%+
            },
            'retirement_allocation': {
                'age_30': {'stocks': 0.90, 'bonds': 0.10},
                'age_40': {'stocks': 0.80, 'bonds': 0.20},
                'age_50': {'stocks': 0.70, 'bonds': 0.30},
                'age_60': {'stocks': 0.60, 'bonds': 0.40},
                'age_65': {'stocks': 0.50, 'bonds': 0.50}
            },
            'withdrawal_rates': {
                'conservative': 0.03,   # 3%
                'standard': 0.04,       # 4% rule
                'aggressive': 0.05      # 5%
            },
            'asset_allocation': {
                'cash_max_percentage': 0.10,  # Max 10% cash in long-term portfolio
                'home_equity_max': 0.40,      # Max 40% net worth in home equity
                'single_stock_max': 0.05      # Max 5% in any single stock
            }
        }
    
    def validate_context(self, context: Dict[str, Any], user_profile: Dict[str, Any]) -> List[ValidationResult]:
        """
        Validate financial context against industry benchmarks
        
        Args:
            context: Financial context data
            user_profile: User profile data (age, risk tolerance, etc.)
            
        Returns:
            List of validation results with recommendations
        """
        validations = []
        
        try:
            # Extract key metrics from context
            age = self._extract_age(context, user_profile)
            net_worth = self._extract_net_worth(context)
            monthly_income = self._extract_monthly_income(context)
            monthly_expenses = self._extract_monthly_expenses(context)
            debt_to_income = self._extract_debt_to_income(context)
            savings_rate = self._extract_savings_rate(context)
            
            # Validate emergency fund
            validations.extend(self._validate_emergency_fund(context, monthly_expenses))
            
            # Validate debt ratios
            validations.extend(self._validate_debt_ratios(debt_to_income))
            
            # Validate savings rate
            validations.extend(self._validate_savings_rate(savings_rate, age))
            
            # Validate asset allocation if available
            validations.extend(self._validate_asset_allocation(context, age))
            
            # Validate retirement readiness
            validations.extend(self._validate_retirement_context(context, age))
            
            # Validate goal feasibility
            validations.extend(self._validate_goal_feasibility(context))
            
            logger.info(f"Context validation complete: {len(validations)} findings")
            return validations
            
        except Exception as e:
            logger.error(f"Context validation failed: {str(e)}")
            return [ValidationResult(
                severity=ValidationSeverity.ERROR,
                category="validation_error",
                message=f"Context validation failed: {str(e)}",
                recommendation="Please review input data and try again"
            )]
    
    def _validate_emergency_fund(self, context: Dict[str, Any], monthly_expenses: float) -> List[ValidationResult]:
        """Validate emergency fund adequacy"""
        validations = []
        
        try:
            # Extract liquid assets (cash, savings, money market)
            liquid_assets = self._extract_liquid_assets(context)
            
            if monthly_expenses > 0:
                months_covered = liquid_assets / monthly_expenses
                
                if months_covered < self.benchmarks['emergency_fund']['min_months']:
                    validations.append(ValidationResult(
                        severity=ValidationSeverity.CRITICAL,
                        category="emergency_fund",
                        message=f"Emergency fund covers only {months_covered:.1f} months of expenses",
                        recommendation=f"Build emergency fund to at least {self.benchmarks['emergency_fund']['recommended_months']} months of expenses (${monthly_expenses * self.benchmarks['emergency_fund']['recommended_months']:,.0f})",
                        benchmark_reference="Industry standard: 3-6 months of expenses"
                    ))
                elif months_covered < self.benchmarks['emergency_fund']['recommended_months']:
                    validations.append(ValidationResult(
                        severity=ValidationSeverity.WARNING,
                        category="emergency_fund",
                        message=f"Emergency fund covers {months_covered:.1f} months of expenses",
                        recommendation=f"Consider building to {self.benchmarks['emergency_fund']['recommended_months']} months for better security",
                        benchmark_reference="Recommended: 6 months of expenses"
                    ))
                else:
                    validations.append(ValidationResult(
                        severity=ValidationSeverity.INFO,
                        category="emergency_fund",
                        message=f"Emergency fund is adequate: {months_covered:.1f} months covered",
                        benchmark_reference="Industry standard: 3-6 months of expenses"
                    ))
        
        except Exception as e:
            logger.warning(f"Emergency fund validation failed: {str(e)}")
        
        return validations
    
    def _validate_debt_ratios(self, debt_to_income: float) -> List[ValidationResult]:
        """Validate debt-to-income ratios"""
        validations = []
        
        try:
            # Convert back to percentage for display
            debt_to_income_pct = debt_to_income * 100
            
            if debt_to_income <= self.benchmarks['debt_to_income']['excellent']:
                validations.append(ValidationResult(
                    severity=ValidationSeverity.INFO,
                    category="debt_ratio",
                    message=f"Excellent debt-to-income ratio: {debt_to_income_pct:.1f}%",
                    benchmark_reference="Excellent: Below 20%"
                ))
            elif debt_to_income <= self.benchmarks['debt_to_income']['good']:
                validations.append(ValidationResult(
                    severity=ValidationSeverity.INFO,
                    category="debt_ratio",
                    message=f"Good debt-to-income ratio: {debt_to_income_pct:.1f}%",
                    benchmark_reference="Good: 20-36%"
                ))
            elif debt_to_income <= self.benchmarks['debt_to_income']['concerning']:
                validations.append(ValidationResult(
                    severity=ValidationSeverity.WARNING,
                    category="debt_ratio",
                    message=f"Concerning debt-to-income ratio: {debt_to_income_pct:.1f}%",
                    recommendation="Consider debt reduction strategies before increasing investments",
                    benchmark_reference="Concerning: 36-50%"
                ))
            else:
                validations.append(ValidationResult(
                    severity=ValidationSeverity.CRITICAL,
                    category="debt_ratio",
                    message=f"Critical debt-to-income ratio: {debt_to_income_pct:.1f}%",
                    recommendation="Focus on aggressive debt reduction before investment growth",
                    benchmark_reference="Critical: Above 50%"
                ))
        
        except Exception as e:
            logger.warning(f"Debt ratio validation failed: {str(e)}")
        
        return validations
    
    def _validate_savings_rate(self, savings_rate: float, age: int) -> List[ValidationResult]:
        """Validate savings rate appropriateness"""
        validations = []
        
        try:
            # Adjust recommendations based on age
            if age < 30:
                target_rate = 0.15  # 15% for young savers
            elif age < 40:
                target_rate = 0.20  # 20% for 30s
            elif age < 50:
                target_rate = 0.25  # 25% for 40s (catch-up time)
            else:
                target_rate = 0.30  # 30%+ for 50s+ (maximum catch-up)
            
            # Convert back to percentage for display
            savings_rate_pct = savings_rate * 100
            
            if savings_rate >= target_rate:
                validations.append(ValidationResult(
                    severity=ValidationSeverity.INFO,
                    category="savings_rate",
                    message=f"Excellent savings rate for age {age}: {savings_rate_pct:.1f}%",
                    benchmark_reference=f"Age-appropriate target: {target_rate:.0%}"
                ))
            elif savings_rate >= self.benchmarks['savings_rate']['good']:
                validations.append(ValidationResult(
                    severity=ValidationSeverity.INFO,
                    category="savings_rate",
                    message=f"Good savings rate: {savings_rate_pct:.1f}%",
                    recommendation=f"Consider increasing to {target_rate:.0%} for age {age}",
                    benchmark_reference=f"Age-appropriate target: {target_rate:.0%}"
                ))
            elif savings_rate >= self.benchmarks['savings_rate']['minimum']:
                validations.append(ValidationResult(
                    severity=ValidationSeverity.WARNING,
                    category="savings_rate",
                    message=f"Minimum savings rate: {savings_rate_pct:.1f}%",
                    recommendation=f"Increase savings rate to {target_rate:.0%} for better financial security",
                    benchmark_reference=f"Minimum: 10%, Recommended for age {age}: {target_rate:.0%}"
                ))
            else:
                validations.append(ValidationResult(
                    severity=ValidationSeverity.CRITICAL,
                    category="savings_rate",
                    message=f"Below minimum savings rate: {savings_rate_pct:.1f}%",
                    recommendation="Focus on expense reduction and income optimization to reach 10% minimum savings rate",
                    benchmark_reference="Minimum: 10%"
                ))
        
        except Exception as e:
            logger.warning(f"Savings rate validation failed: {str(e)}")
        
        return validations
    
    def _validate_asset_allocation(self, context: Dict[str, Any], age: int) -> List[ValidationResult]:
        """Validate asset allocation appropriateness"""
        validations = []
        
        try:
            # Extract asset breakdown
            asset_breakdown = context.get('asset_breakdown', {})
            total_assets = context.get('total_retirement_assets', 0)
            
            if not asset_breakdown or total_assets <= 0:
                return validations
            
            # Calculate current allocation percentages
            allocation = {}
            for asset_type, amount in asset_breakdown.items():
                if isinstance(amount, (int, float)) and amount > 0:
                    allocation[asset_type] = amount / total_assets
            
            # Check cash allocation
            cash_allocation = allocation.get('other_liquid_assets', 0)
            if cash_allocation > self.benchmarks['asset_allocation']['cash_max_percentage']:
                validations.append(ValidationResult(
                    severity=ValidationSeverity.WARNING,
                    category="asset_allocation",
                    message=f"High cash allocation: {cash_allocation:.1%}",
                    recommendation="Consider investing excess cash for long-term growth",
                    benchmark_reference="Recommended cash allocation: <10% for long-term portfolios"
                ))
            
            # Age-based allocation check
            target_allocation = self._get_age_appropriate_allocation(age)
            if target_allocation:
                equity_heavy_assets = allocation.get('investment_accounts', 0) + allocation.get('401k', 0)
                if equity_heavy_assets < target_allocation['stocks'] - 0.10:  # 10% tolerance
                    validations.append(ValidationResult(
                        severity=ValidationSeverity.WARNING,
                        category="asset_allocation",
                        message=f"Conservative allocation for age {age}: {equity_heavy_assets:.1%} in growth assets",
                        recommendation=f"Consider increasing equity allocation to ~{target_allocation['stocks']:.0%} for age {age}",
                        benchmark_reference=f"Age {age} target: ~{target_allocation['stocks']:.0%} stocks, ~{target_allocation['bonds']:.0%} bonds"
                    ))
        
        except Exception as e:
            logger.warning(f"Asset allocation validation failed: {str(e)}")
        
        return validations
    
    def _validate_retirement_context(self, context: Dict[str, Any], age: int) -> List[ValidationResult]:
        """Validate retirement readiness and projections"""
        validations = []
        
        try:
            completion_percentage = context.get('retirement_completion_percentage', 0)
            retirement_status = context.get('retirement_status', '')
            years_to_retirement = 65 - age if age < 65 else 0
            
            # Validate completion percentage against age
            expected_completion = self._calculate_expected_retirement_completion(age)
            
            if completion_percentage >= expected_completion + 20:  # 20% ahead
                validations.append(ValidationResult(
                    severity=ValidationSeverity.INFO,
                    category="retirement_readiness",
                    message=f"Ahead of retirement schedule: {completion_percentage:.1f}% funded",
                    recommendation="Consider early retirement options or lifestyle upgrades",
                    benchmark_reference=f"Expected for age {age}: ~{expected_completion:.0f}%"
                ))
            elif completion_percentage >= expected_completion:
                validations.append(ValidationResult(
                    severity=ValidationSeverity.INFO,
                    category="retirement_readiness",
                    message=f"On track for retirement: {completion_percentage:.1f}% funded",
                    benchmark_reference=f"Expected for age {age}: ~{expected_completion:.0f}%"
                ))
            elif completion_percentage >= expected_completion - 20:  # Within 20%
                validations.append(ValidationResult(
                    severity=ValidationSeverity.WARNING,
                    category="retirement_readiness",
                    message=f"Slightly behind retirement schedule: {completion_percentage:.1f}% funded",
                    recommendation="Consider increasing retirement contributions or extending working years",
                    benchmark_reference=f"Expected for age {age}: ~{expected_completion:.0f}%"
                ))
            else:
                validations.append(ValidationResult(
                    severity=ValidationSeverity.CRITICAL,
                    category="retirement_readiness",
                    message=f"Significantly behind retirement schedule: {completion_percentage:.1f}% funded",
                    recommendation="Implement aggressive catch-up strategy: maximize contributions, reduce expenses, consider working longer",
                    benchmark_reference=f"Expected for age {age}: ~{expected_completion:.0f}%"
                ))
        
        except Exception as e:
            logger.warning(f"Retirement validation failed: {str(e)}")
        
        return validations
    
    def _validate_goal_feasibility(self, context: Dict[str, Any]) -> List[ValidationResult]:
        """Validate if financial goals are realistic and achievable"""
        validations = []
        
        try:
            goal_amount = context.get('retirement_goal_amount', 0)
            years_to_goal = context.get('years_to_goal', 0)
            monthly_surplus = context.get('monthly_surplus', 0)
            
            if goal_amount > 0 and years_to_goal > 0 and monthly_surplus > 0:
                # Calculate required monthly savings (simplified)
                months_to_goal = years_to_goal * 12
                required_monthly = goal_amount / months_to_goal  # Simplified, no interest
                
                feasibility_ratio = monthly_surplus / required_monthly
                
                if feasibility_ratio >= 1.2:
                    validations.append(ValidationResult(
                        severity=ValidationSeverity.INFO,
                        category="goal_feasibility",
                        message=f"Goal is easily achievable with current savings capacity",
                        recommendation="Consider accelerating timeline or increasing goal amount",
                        benchmark_reference=f"Required: ${required_monthly:,.0f}/month, Available: ${monthly_surplus:,.0f}/month"
                    ))
                elif feasibility_ratio >= 0.8:
                    validations.append(ValidationResult(
                        severity=ValidationSeverity.INFO,
                        category="goal_feasibility",
                        message=f"Goal is achievable with current savings capacity",
                        benchmark_reference=f"Required: ${required_monthly:,.0f}/month, Available: ${monthly_surplus:,.0f}/month"
                    ))
                elif feasibility_ratio >= 0.5:
                    validations.append(ValidationResult(
                        severity=ValidationSeverity.WARNING,
                        category="goal_feasibility",
                        message=f"Goal requires significant portion of available savings",
                        recommendation="Consider adjusting timeline or reducing goal amount",
                        benchmark_reference=f"Required: ${required_monthly:,.0f}/month, Available: ${monthly_surplus:,.0f}/month"
                    ))
                else:
                    validations.append(ValidationResult(
                        severity=ValidationSeverity.CRITICAL,
                        category="goal_feasibility",
                        message=f"Goal may not be achievable with current savings capacity",
                        recommendation="Revise goal amount, extend timeline, or increase income/reduce expenses",
                        benchmark_reference=f"Required: ${required_monthly:,.0f}/month, Available: ${monthly_surplus:,.0f}/month"
                    ))
        
        except Exception as e:
            logger.warning(f"Goal feasibility validation failed: {str(e)}")
        
        return validations
    
    def get_validation_summary(self, validations: List[ValidationResult]) -> Dict[str, Any]:
        """Generate a summary of validation results"""
        summary = {
            'total_findings': len(validations),
            'by_severity': {
                'critical': 0,
                'error': 0,
                'warning': 0,
                'info': 0
            },
            'by_category': {},
            'action_required': False,
            'overall_assessment': 'good'
        }
        
        for validation in validations:
            # Count by severity
            summary['by_severity'][validation.severity.value] += 1
            
            # Count by category
            if validation.category not in summary['by_category']:
                summary['by_category'][validation.category] = 0
            summary['by_category'][validation.category] += 1
        
        # Determine if action required
        critical_count = summary['by_severity']['critical']
        error_count = summary['by_severity']['error']
        warning_count = summary['by_severity']['warning']
        
        if critical_count > 0:
            summary['action_required'] = True
            summary['overall_assessment'] = 'critical'
        elif error_count > 0:
            summary['action_required'] = True
            summary['overall_assessment'] = 'needs_attention'
        elif warning_count > 2:
            summary['action_required'] = True
            summary['overall_assessment'] = 'review_recommended'
        
        return summary
    
    # Helper methods
    def _extract_age(self, context: Dict[str, Any], user_profile: Dict[str, Any]) -> int:
        """Extract user age from context or profile"""
        return context.get('age') or user_profile.get('age', 54)  # Default 54 if not found
    
    def _extract_net_worth(self, context: Dict[str, Any]) -> float:
        """Extract net worth from context"""
        return float(context.get('net_worth', 0))
    
    def _extract_monthly_income(self, context: Dict[str, Any]) -> float:
        """Extract monthly income from context"""
        return float(context.get('monthly_income', 0))
    
    def _extract_monthly_expenses(self, context: Dict[str, Any]) -> float:
        """Extract monthly expenses from context"""
        return float(context.get('monthly_expenses', 0))
    
    def _extract_debt_to_income(self, context: Dict[str, Any]) -> float:
        """Extract debt-to-income ratio from context (convert percentage to decimal)"""
        dti_percentage = float(context.get('debt_to_income_ratio', 0))
        # Convert percentage to decimal for comparison with benchmarks
        return dti_percentage / 100.0
    
    def _extract_savings_rate(self, context: Dict[str, Any]) -> float:
        """Extract savings rate from context (convert percentage to decimal)"""
        savings_percentage = float(context.get('savings_rate', 0))
        # Convert percentage to decimal for comparison with benchmarks
        return savings_percentage / 100.0
    
    def _extract_liquid_assets(self, context: Dict[str, Any]) -> float:
        """Extract liquid assets (cash, savings) from context"""
        asset_breakdown = context.get('asset_breakdown', {})
        liquid_assets = asset_breakdown.get('other_liquid_assets', 0)
        return float(liquid_assets)
    
    def _get_age_appropriate_allocation(self, age: int) -> Optional[Dict[str, float]]:
        """Get age-appropriate asset allocation"""
        if age <= 35:
            return self.benchmarks['retirement_allocation']['age_30']
        elif age <= 45:
            return self.benchmarks['retirement_allocation']['age_40']
        elif age <= 55:
            return self.benchmarks['retirement_allocation']['age_50']
        elif age <= 62:
            return self.benchmarks['retirement_allocation']['age_60']
        else:
            return self.benchmarks['retirement_allocation']['age_65']
    
    def _calculate_expected_retirement_completion(self, age: int) -> float:
        """Calculate expected retirement completion percentage for age"""
        if age <= 25:
            return 5.0   # 5% by 25
        elif age <= 30:
            return 15.0  # 15% by 30
        elif age <= 35:
            return 30.0  # 30% by 35
        elif age <= 40:
            return 50.0  # 50% by 40
        elif age <= 45:
            return 70.0  # 70% by 45
        elif age <= 50:
            return 85.0  # 85% by 50
        elif age <= 55:
            return 95.0  # 95% by 55
        elif age <= 60:
            return 100.0 # 100% by 60
        else:
            return 110.0 # Should be complete + buffer by 65

# Global instance
context_validator = ContextValidatorService()