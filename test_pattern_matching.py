#!/usr/bin/env python3
"""
Test pattern matching for calculation router
"""

import re

def test_pattern(pattern, test_string):
    """Test if pattern matches string"""
    match = re.search(pattern, test_string)
    print(f"Pattern: {pattern}")
    print(f"String:  {test_string}")
    print(f"Match:   {bool(match)}")
    if match:
        print(f"Groups:  {match.groups()}")
    print("-" * 50)
    return match

def main():
    # Test the problematic queries
    test_queries = [
        "what if i reduce my goal to 3000000, how many years it will shave off",
        "Am I on track for my retirement goal?",
        "consider 7% growth rate",
        "how many years exactly can i shave off",
        "If I reduce my retirement goal to $3M with 7% growth rate, how many years will that save me?"
    ]
    
    # Patterns from calculation_router.py
    patterns = {
        'retirement_goal_adjustment': [
            r'(?i).*reduce.*goal.*(\$?[\d,]+)',
            r'(?i).*change.*goal.*(\$?[\d,]+)',
            r'(?i).*goal.*(\$?[\d,]+).*years.*save',
            r'(?i).*years.*save.*goal.*(\$?[\d,]+)',
            r'(?i).*shave.*years.*goal.*(\$?[\d,]+)',
            r'(?i).*(\$?[\d,]+).*goal.*timeline'
        ],
        'years_to_retirement_goal': [
            r'(?i).*when can i retire',
            r'(?i).*how long.*retirement',
            r'(?i).*years.*retirement goal',
            r'(?i).*timeline.*retirement',
            r'(?i).*reach.*retirement goal',
            r'(?i).*on track.*retirement',
            r'(?i).*track.*retirement goal',
            r'(?i).*retirement.*on track'
        ],
        'growth_rate_impact': [
            r'(?i).*(\d+)%.*growth.*rate',
            r'(?i).*growth.*rate.*(\d+)',
            r'(?i).*(\d+)%.*return',
            r'(?i).*consider.*(\d+)%',
            r'(?i).*assume.*(\d+)%'
        ]
    }
    
    print("Testing query pattern matching:\n")
    
    for query in test_queries:
        print(f"TESTING QUERY: '{query}'")
        print("=" * 60)
        
        found_match = False
        for calc_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = test_pattern(pattern, query)
                if match:
                    print(f">>> MATCHED: {calc_type}")
                    found_match = True
                    break
            if found_match:
                break
        
        if not found_match:
            print(">>> NO MATCH FOUND")
        
        print("\n" + "=" * 60 + "\n")

if __name__ == "__main__":
    main()