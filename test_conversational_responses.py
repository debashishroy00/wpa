#!/usr/bin/env python3
"""
Test the conversational calculator responses
"""

def test_old_vs_new_responses():
    """Compare old technical vs new conversational responses"""
    
    print("=== CALCULATOR RESPONSE IMPROVEMENT TEST ===\n")
    
    # Mock data to simulate calculator results
    result = {
        'years': 4.0,
        'final_amount': 3651713,
        'total_contributions': 377424,
        'growth_component': 708744,
        'current_assets': 2565545,
        'target_goal': 3500000,
        'monthly_additions': 7863
    }
    
    assumptions = {
        'growth_rate_info': {
            'rate': 0.06,
            'explanation': 'moderate conservative 6% rate for pre-retirement planning'
        }
    }
    
    print("OLD TECHNICAL FORMAT:")
    print("=" * 50)
    print("""🎯 **Retirement Timeline Analysis**
**Primary Result:** 4.0 years to reach your goal
**Financial Breakdown:**
• Final projected amount: $3,651,713
• Total contributions needed: $377,424
• Growth from investments: $708,744
📊 **Assumptions Used:**
Moderate conservative 6% rate for pre-retirement planning
🟢 **Confidence:** High
💡 *Want different assumptions? Ask: "What if I assume 8% growth instead?"*""")
    
    print("\n\nNEW CONVERSATIONAL FORMAT:")
    print("=" * 50)
    
    # Simulate the new conversational format
    years = result['years']
    target_goal = result['target_goal']
    current_assets = result['current_assets']
    monthly_additions = result['monthly_additions']
    total_contributions = result['total_contributions']
    growth_component = result['growth_component']
    final_amount = result['final_amount']
    rate_explanation = assumptions['growth_rate_info']['explanation']
    
    new_response = f"""Based on your current financial position, you're on track to reach your ${target_goal:,.0f} retirement goal in approximately **{years:.0f} years**.

Here's how this works: Starting with your current assets of ${current_assets:,.0f} and consistently adding your monthly surplus of ${monthly_additions:,.0f}, you'll save about ${total_contributions:,.0f} over this period. Combined with projected investment growth of ${growth_component:,.0f} (using {rate_explanation}), your portfolio should reach ${final_amount:,.0f}.

This timeline assumes you maintain your current savings rate and investment approach. If you want to accelerate this, consider increasing your monthly contributions or exploring investment options that align with your risk tolerance.

The good news is that you're in a strong position - your current savings rate and asset base put you well on track for your retirement goals."""
    
    print(new_response)
    
    print("\n\n=== GOAL ADJUSTMENT COMPARISON ===\n")
    
    # Test goal adjustment response
    adjustment_result = {
        'original_goal': 3500000,
        'new_goal': 3000000,
        'years_saved': 2.0,
        'original_years': 4.0,
        'new_years': 2.0,
        'goal_reduction': 500000,
        'goal_reduction_percent': 14.3
    }
    
    print("OLD TECHNICAL FORMAT:")
    print("-" * 30)
    print("""💰 **Goal Adjustment Impact Analysis**
**Timeline Improvement:**
• Original timeline: 4.0 years to $3,500,000
• New timeline: 2.0 years to $3,000,000
• **Years saved: 2.0 years** ⏰
**Goal Change:**
• Reduction: $500,000 (14.3%)
• This brings your retirement 2.0 years closer!""")
    
    print("\nNEW CONVERSATIONAL FORMAT:")
    print("-" * 30)
    
    original_goal = adjustment_result['original_goal']
    new_goal = adjustment_result['new_goal']
    years_saved = adjustment_result['years_saved']
    original_years = adjustment_result['original_years']
    new_years = adjustment_result['new_years']
    goal_reduction = adjustment_result['goal_reduction']
    goal_reduction_percent = adjustment_result['goal_reduction_percent']
    
    new_adjustment_response = f"""Great question! Reducing your retirement goal from ${original_goal:,.0f} to ${new_goal:,.0f} would **save you {years_saved:.0f} years** - bringing your retirement timeline from {original_years:.0f} years down to just {new_years:.0f} years.

This ${goal_reduction:,.0f} reduction ({goal_reduction_percent:.1f}% less) significantly accelerates your path to financial independence. You'd still have a substantial retirement fund while reaching your goal much sooner.

The calculation uses {rate_explanation} and assumes you maintain your current savings rate. This adjustment demonstrates how even modest goal changes can have dramatic impacts on your timeline."""
    
    print(new_adjustment_response)
    
    print("\n\n=== KEY IMPROVEMENTS ===")
    print("✅ Removed technical jargon and bullet points")
    print("✅ Added natural explanatory language")
    print("✅ Integrated assumptions into narrative flow")
    print("✅ Made responses more conversational and engaging")
    print("✅ Eliminated 'system-speak' formatting")
    print("✅ Created coherent paragraph structure")

if __name__ == "__main__":
    test_old_vs_new_responses()