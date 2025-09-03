#!/usr/bin/env python3
"""
Debug the retirement timeline calculation
"""

def years_to_goal_debug(current_assets: float, target_goal: float, growth_rate: float, 
                       monthly_additions: float = 0):
    """Debug version of years_to_goal calculation"""
    
    print(f"=== DEBUGGING RETIREMENT TIMELINE CALCULATION ===")
    print(f"Current assets: ${current_assets:,.0f}")
    print(f"Target goal: ${target_goal:,.0f}")
    print(f"Growth rate: {growth_rate:.1%}")
    print(f"Monthly additions: ${monthly_additions:,.0f} (${monthly_additions * 12:,.0f} annually)")
    print(f"Gap to fill: ${target_goal - current_assets:,.0f}")
    print()
    
    if current_assets >= target_goal:
        return {
            'years': 0,
            'already_achieved': True,
            'surplus': current_assets - target_goal
        }
    
    annual_additions = monthly_additions * 12
    
    if growth_rate == 0:
        # Simple case: no growth
        years = (target_goal - current_assets) / annual_additions if annual_additions > 0 else float('inf')
        print(f"No growth scenario: {years:.1f} years needed")
        return {'years': years}
    
    # Use iterative approach to solve compound growth equation
    years = 0
    projected_assets = current_assets
    
    print("Year-by-year projection:")
    print(f"Year {years}: ${projected_assets:,.0f}")
    
    while projected_assets < target_goal and years < 50:
        # Apply growth first, then add contributions
        growth_amount = projected_assets * growth_rate
        projected_assets = projected_assets * (1 + growth_rate) + annual_additions
        years += 1
        
        print(f"Year {years}: ${projected_assets:,.0f} (growth: ${growth_amount:,.0f}, contribution: ${annual_additions:,.0f})")
        
        if projected_assets >= target_goal:
            print(f"*** TARGET REACHED in {years} years! ***")
            break
    
    if years >= 50:
        years = float('inf')
    
    total_contributions = annual_additions * years if years < 50 else 0
    growth_component = (projected_assets - current_assets - total_contributions) if years < 50 else 0
    
    print()
    print(f"=== FINAL RESULTS ===")
    print(f"Years needed: {years}")
    print(f"Final amount: ${projected_assets:,.0f}")
    print(f"Total contributions: ${total_contributions:,.0f}")
    print(f"Total growth: ${growth_component:,.0f}")
    
    return {
        'years': years,
        'already_achieved': False,
        'final_amount': projected_assets if years < 50 else target_goal,
        'total_contributions': total_contributions,
        'growth_component': growth_component
    }

if __name__ == "__main__":
    # Test with user's actual scenario
    print("=== USER'S SCENARIO ===")
    
    # Scenario 1: Using typical growth rates
    print("\nScenario 1: 7% growth rate")
    years_to_goal_debug(
        current_assets=2_500_000,
        target_goal=3_500_000,
        growth_rate=0.07,
        monthly_additions=7_863
    )
    
    print("\n" + "="*60)
    print("\nScenario 2: 5% growth rate")
    years_to_goal_debug(
        current_assets=2_500_000,
        target_goal=3_500_000,
        growth_rate=0.05,
        monthly_additions=7_863
    )
    
    print("\n" + "="*60)
    print("\nScenario 3: 10% growth rate")
    years_to_goal_debug(
        current_assets=2_500_000,
        target_goal=3_500_000,
        growth_rate=0.10,
        monthly_additions=7_863
    )