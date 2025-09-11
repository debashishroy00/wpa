#!/usr/bin/env python3
"""
Direct test of retirement calculation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

try:
    import retirement_calculator
    print("Import successful")
    
    # Create instance of retirement calculator
    calc = retirement_calculator.RetirementCalculator()
    
    # Test with test user's actual data
    test_context = {
        'age': 35,
        'monthly_expenses': 5300,
        'monthly_surplus': 1700,  # 7000 - 5300
        'assets_breakdown': {
            'cash_bank_accounts': 55000,
            'investment_accounts': 350000,
            'retirement_accounts': 720000,
            'real_estate': 0
        }
    }
    
    print(f"Testing with: {test_context}")
    result = calc.calculate_years_to_financial_independence(test_context)
    print(f"Result: {result}")
    
except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()