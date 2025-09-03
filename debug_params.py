#!/usr/bin/env python3
"""
Debug parameter extraction issue
"""

import json

# Simulate the facts structure as it might be coming from the database
sample_facts = {
    # These might be at top level
    "net_worth": 2565545,
    "monthly_surplus": 7863,
    "retirement_goal_amount": 3500000,
    
    # Or they might be nested
    "_context": {
        "age": 55,
        "retirement_goal": 3500000
    },
    
    # Or in a different structure
    "assets": {
        "total": 2565545,
        "retirement_total": 310216,
        "investment_total": 560784,
        "liquid_assets": 108945,
        "cash_total": 108945,
        "home_equity": 1290000,
        "bitcoin_value": 114600
    },
    
    "cashflow": {
        "monthly_income": 15347,
        "monthly_expenses": 7484,
        "monthly_surplus": 7863
    }
}

def test_extraction():
    """Test parameter extraction logic"""
    
    print("=== DEBUGGING PARAMETER EXTRACTION ===\n")
    
    # Test different structures
    test_contexts = [
        # Structure 1: Flat
        {
            "net_worth": 2565545,
            "monthly_surplus": 7863,
            "retirement_goal_amount": 3500000,
        },
        
        # Structure 2: Nested assets
        {
            "assets": {
                "total": 2565545,
                "retirement_total": 310216,
            },
            "cashflow": {
                "monthly_surplus": 7863
            },
            "goals": {
                "retirement_goal_amount": 3500000
            }
        },
        
        # Structure 3: Empty (what might be happening)
        {},
        
        # Structure 4: Different field names
        {
            "total_net_worth": 2565545,
            "surplus_monthly": 7863,
            "retirement_target": 3500000,
        }
    ]
    
    for i, context in enumerate(test_contexts, 1):
        print(f"Test Structure {i}:")
        print(json.dumps(context, indent=2)[:200])
        
        # Test extraction
        current_assets = context.get('net_worth', 0)
        if current_assets == 0:
            current_assets = context.get('total_assets', 0)
        if current_assets == 0 and 'assets' in context:
            current_assets = context['assets'].get('total', 0)
        
        monthly_surplus = context.get('monthly_surplus', 0)
        if monthly_surplus == 0 and 'cashflow' in context:
            monthly_surplus = context['cashflow'].get('monthly_surplus', 0)
        
        retirement_goal = context.get('retirement_goal_amount', 3500000)
        if retirement_goal == 3500000 and 'goals' in context:
            retirement_goal = context['goals'].get('retirement_goal_amount', 3500000)
        
        print(f"  Extracted:")
        print(f"    current_assets: ${current_assets:,.0f}")
        print(f"    monthly_surplus: ${monthly_surplus:,.0f}")
        print(f"    retirement_goal: ${retirement_goal:,.0f}")
        print()

if __name__ == "__main__":
    test_extraction()