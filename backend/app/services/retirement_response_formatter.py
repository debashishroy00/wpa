"""
Retirement Response Formatter
Simple, clean retirement planning response enhancement
Follows CLAUDE.md guidelines - no hardcoded values, graceful fallbacks
"""

import re
from typing import Dict, Any, Optional
import structlog

logger = structlog.get_logger()


class RetirementResponseFormatter:
    """Clean, simple retirement response formatter"""
    
    def __init__(self):
        self.retirement_keywords = ['retirement', 'retire', '401k', 'ira', 'pension', 'financial independence']
    
    def is_retirement_query(self, message: str) -> bool:
        """Check if message is retirement-related"""
        message_lower = message.lower()
        is_retirement = any(keyword in message_lower for keyword in self.retirement_keywords)
        logger.info(f"Retirement query check: '{message[:50]}...' -> {is_retirement}")
        return is_retirement
    
    def enhance_response(self, ai_response: str, user_financial_data: Dict[str, Any]) -> str:
        """
        Enhance AI response with structured retirement metrics
        NEVER hardcodes values - uses actual user data or skips enhancement
        """
        try:
            logger.info(f"Starting retirement response enhancement")
            # CRITICAL: Only enhance if user has actual financial data
            if not user_financial_data or not self._has_meaningful_data(user_financial_data):
                logger.info("Skipping retirement enhancement - no meaningful financial data")
                return ai_response
            
            # Extract key metrics safely
            metrics = self._extract_key_metrics(user_financial_data)
            
            # Only enhance if we have enough data for meaningful insights
            if not metrics or len(metrics) < 3:
                logger.info("Skipping retirement enhancement - insufficient metrics")
                return ai_response
            
            # Add metrics summary to response
            enhanced_response = self._add_metrics_summary(ai_response, metrics)
            
            logger.info(f"Enhanced retirement response with {len(metrics)} metrics")
            return enhanced_response
            
        except Exception as e:
            logger.error(f"Retirement response enhancement failed: {str(e)}")
            return ai_response  # Always return original on error
    
    def _has_meaningful_data(self, data: Dict[str, Any]) -> bool:
        """Check if user has meaningful financial data"""
        # Must have either assets or income to provide retirement insights
        has_assets = data.get('totalAssets', 0) > 0
        has_income = data.get('monthlyIncome', 0) > 0
        has_expenses = data.get('monthlyExpenses', 0) > 0
        
        return has_assets or (has_income and has_expenses)
    
    def _extract_key_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key retirement metrics safely"""
        metrics = {}
        
        # Net worth
        net_worth = data.get('netWorth', 0)
        if net_worth > 0:
            metrics['net_worth'] = net_worth
        
        # Monthly surplus/deficit
        surplus = data.get('monthlySurplus', 0)
        if surplus != 0:  # Include negative values (deficits)
            metrics['monthly_surplus'] = surplus
        
        # Savings rate
        savings_rate = data.get('savingsRate', 0)
        if savings_rate > 0:
            metrics['savings_rate'] = savings_rate
        
        # Retirement assets (from assets breakdown)
        retirement_assets = self._calculate_retirement_assets(data)
        if retirement_assets > 0:
            metrics['retirement_assets'] = retirement_assets
        
        # Debt-to-income ratio
        dti = data.get('debtToIncomeRatio', 0)
        if dti > 0:
            metrics['debt_to_income'] = dti
        
        # Monthly expenses (for retirement planning)
        expenses = data.get('monthlyExpenses', 0)
        if expenses > 0:
            metrics['monthly_expenses'] = expenses
            # Calculate basic retirement need (25x annual expenses)
            metrics['basic_retirement_need'] = expenses * 12 * 25
        
        return metrics
    
    def _calculate_retirement_assets(self, data: Dict[str, Any]) -> float:
        """Calculate retirement assets from breakdown"""
        assets_breakdown = data.get('assetsBreakdown', {})
        retirement_total = 0
        
        for category, items in assets_breakdown.items():
            category_lower = category.lower()
            # Check if category is retirement-related
            if any(keyword in category_lower for keyword in ['retirement', '401k', 'ira', 'pension']):
                for item in items:
                    retirement_total += item.get('value', 0)
            else:
                # Check individual items
                for item in items:
                    item_name = item.get('name', '').lower()
                    if any(keyword in item_name for keyword in ['401k', 'ira', 'retirement', 'pension']):
                        retirement_total += item.get('value', 0)
        
        return retirement_total
    
    def _add_metrics_summary(self, response: str, metrics: Dict[str, Any]) -> str:
        """Add metrics summary to response"""
        # Build concise metrics summary
        summary_parts = []
        
        # Net worth
        if 'net_worth' in metrics:
            net_worth = metrics['net_worth']
            summary_parts.append(f"Net Worth: ${net_worth:,.0f}")
        
        # Retirement assets vs basic need
        if 'retirement_assets' in metrics and 'basic_retirement_need' in metrics:
            current = metrics['retirement_assets']
            needed = metrics['basic_retirement_need']
            percentage = (current / needed * 100) if needed > 0 else 0
            summary_parts.append(f"Retirement Progress: ${current:,.0f} of ${needed:,.0f} needed ({percentage:.0f}%)")
        elif 'retirement_assets' in metrics:
            current = metrics['retirement_assets']
            summary_parts.append(f"Current Retirement Assets: ${current:,.0f}")
        
        # Savings metrics
        if 'monthly_surplus' in metrics:
            surplus = metrics['monthly_surplus']
            if surplus > 0:
                annual_savings = surplus * 12
                summary_parts.append(f"Annual Savings Capacity: ${annual_savings:,.0f}")
            else:
                summary_parts.append(f"Monthly Deficit: ${abs(surplus):,.0f}")
        
        if 'savings_rate' in metrics:
            rate = metrics['savings_rate']
            summary_parts.append(f"Savings Rate: {rate:.0f}%")
        
        # Only add summary if we have meaningful metrics
        if len(summary_parts) >= 2:
            metrics_text = " | ".join(summary_parts)
            return f"{response}\n\n**Key Metrics:** {metrics_text}"
        
        return response


# Global instance
retirement_formatter = RetirementResponseFormatter()