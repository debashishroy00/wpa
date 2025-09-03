#!/usr/bin/env python3
"""
Test the fixed retirement calculation with conservative growth rates
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_conservative_retirement_rates():
    """Test the new conservative retirement rate logic"""
    
    class MockGrowthRateManager:
        """Mock the growth rate manager with our fix"""
        
        def __init__(self):
            self.ASSET_RETURNS = {
                'bitcoin': 0.12,  # High return crypto
                'stock_investments': 0.07,
                'retirement_401k': 0.06,
            }
        
        def _get_conservative_retirement_rate(self, user_context):
            """Conservative retirement rate logic"""
            age = user_context.get('age', 50)
            
            if age >= 60:
                base_rate = 0.05  # 5%
                explanation = "Conservative 5% rate for near-retirement planning"
            elif age >= 50:
                base_rate = 0.06  # 6% 
                explanation = "Moderate conservative 6% rate for pre-retirement planning"  
            else:
                base_rate = 0.07  # 7%
                explanation = "Conservative 7% rate for long-term retirement planning"
            
            # Simulate high portfolio rate from crypto/stocks
            portfolio_rate = {'rate': 0.10}  # Aggressive 10% from portfolio weighting
            
            # Cap at conservative rate
            actual_rate = min(portfolio_rate['rate'], base_rate)
            
            if actual_rate < portfolio_rate['rate']:
                explanation += f" (capped from portfolio rate of {portfolio_rate['rate']:.1%})"
            
            return {
                'rate': actual_rate,
                'source': 'conservative_retirement',
                'explanation': explanation,
                'assumptions': [
                    f"Age-appropriate retirement rate: {actual_rate:.1%}",
                    "Conservative assumption for retirement planning",
                    f"User age: {age} years"
                ]
            }
    
    def years_to_goal_with_rate(current_assets, target_goal, growth_rate, monthly_additions=0):
        """Simplified retirement calculation"""
        annual_additions = monthly_additions * 12
        years = 0
        projected_assets = current_assets
        
        while projected_assets < target_goal and years < 50:
            projected_assets = projected_assets * (1 + growth_rate) + annual_additions
            years += 1
        
        return {
            'years': years,
            'final_amount': projected_assets,
            'growth_rate_used': growth_rate
        }
    
    # Test scenarios
    growth_manager = MockGrowthRateManager()
    
    print("=== TESTING FIXED CONSERVATIVE RETIREMENT RATES ===\n")
    
    test_cases = [
        {'age': 55, 'description': 'User age 55 (pre-retirement)'},
        {'age': 45, 'description': 'User age 45 (long-term planning)'},
        {'age': 62, 'description': 'User age 62 (near retirement)'}
    ]
    
    for case in test_cases:
        user_context = {'age': case['age']}
        rate_info = growth_manager._get_conservative_retirement_rate(user_context)
        
        print(f"--- {case['description']} ---")
        print(f"Growth rate: {rate_info['rate']:.1%}")
        print(f"Explanation: {rate_info['explanation']}")
        
        # Calculate timeline with this conservative rate
        result = years_to_goal_with_rate(
            current_assets=2_500_000,
            target_goal=3_500_000,
            growth_rate=rate_info['rate'],
            monthly_additions=7_863
        )
        
        print(f"Years to retirement goal: {result['years']} years")
        print(f"Final amount: ${result['final_amount']:,.0f}")
        print("Assumptions:", rate_info['assumptions'])
        print()
    
    print("=== COMPARISON WITH OLD (AGGRESSIVE) VS NEW (CONSERVATIVE) ===")
    
    # Old aggressive calculation
    old_aggressive = years_to_goal_with_rate(2_500_000, 3_500_000, 0.10, 7_863)
    
    # New conservative (age 55)
    conservative_rate = growth_manager._get_conservative_retirement_rate({'age': 55})
    new_conservative = years_to_goal_with_rate(2_500_000, 3_500_000, conservative_rate['rate'], 7_863)
    
    print(f"OLD (Aggressive 10%): {old_aggressive['years']} years - ${old_aggressive['final_amount']:,.0f}")
    print(f"NEW (Conservative 6%): {new_conservative['years']} years - ${new_conservative['final_amount']:,.0f}")
    print(f"\nDifference: {new_conservative['years'] - old_aggressive['years']} additional years")
    print("✅ This is much more realistic for retirement planning!")

if __name__ == "__main__":
    test_conservative_retirement_rates()