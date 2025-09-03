#!/usr/bin/env python3
"""
Comprehensive audit of calculator issues
"""

import re
import json

def audit_calculation_patterns():
    """Audit all calculation patterns to find gaps"""
    
    print("=== CALCULATOR AUDIT REPORT ===\n")
    
    # Test queries that should work
    test_queries = [
        # Working queries
        ("Am I on track for my retirement goal?", "Should detect: years_to_retirement_goal"),
        ("what if i reduce my goal to 3100000", "Should detect: retirement_goal_adjustment"),
        
        # Failing queries  
        ("what if i increase my goal to 4000000", "Should detect: retirement_goal_adjustment"),
        ("what if my goal is 4000000", "Should detect: retirement_goal_adjustment"),
        ("what if I raise my retirement goal to 4M", "Should detect: retirement_goal_adjustment"),
        ("if I change my goal to 4000000", "Should detect: retirement_goal_adjustment"),
    ]
    
    # Current patterns for retirement_goal_adjustment
    patterns = [
        r'(?i).*reduce.*goal.*(\$?[\d,M]+)',
        r'(?i).*change.*goal.*(\$?[\d,M]+)',
        r'(?i).*goal.*(\$?[\d,M]+).*years.*save',
        r'(?i).*years.*save.*goal.*(\$?[\d,M]+)',
        r'(?i).*shave.*years.*goal.*(\$?[\d,M]+)',
        r'(?i).*(\$?[\d,M]+).*goal.*timeline',
        r'(?i).*how many years.*shave.*off',
        r'(?i).*years.*can.*shave',
        r'(?i).*shave.*years'
    ]
    
    print("PATTERN MATCHING TEST:")
    print("-" * 50)
    
    for query, expected in test_queries:
        matched = False
        matched_pattern = None
        
        for pattern in patterns:
            if re.search(pattern, query):
                matched = True
                matched_pattern = pattern
                break
        
        status = "✓ PASS" if matched else "✗ FAIL"
        print(f"{status} | Query: '{query}'")
        if matched:
            print(f"       Matched pattern: {matched_pattern}")
        else:
            print(f"       {expected} - NO MATCH")
        print()
    
    print("\nISSUES FOUND:")
    print("-" * 50)
    print("1. Pattern set is biased toward 'reduce' and 'shave' keywords")
    print("2. Missing patterns for 'increase', 'raise', 'higher' keywords")
    print("3. Pattern r'(?i).*change.*goal.*(\$?[\d,M]+)' should match but may not be working")
    print("4. Need more general patterns that work for both increases and decreases")
    
    print("\nRECOMMENDED NEW PATTERNS:")
    print("-" * 50)
    
    new_patterns = [
        r'(?i).*increase.*goal.*(\$?[\d,M]+)',
        r'(?i).*raise.*goal.*(\$?[\d,M]+)',
        r'(?i).*goal.*to.*(\$?[\d,M]+)',
        r'(?i).*my goal is.*(\$?[\d,M]+)',
        r'(?i).*if.*goal.*(\$?[\d,M]+)',
        r'(?i).*set.*goal.*(\$?[\d,M]+)',
        r'(?i).*adjust.*goal.*(\$?[\d,M]+)'
    ]
    
    print("New patterns to add:")
    for pattern in new_patterns:
        print(f"  {pattern}")
    
    print("\nRESPONSE FORMAT ISSUES:")
    print("-" * 50)
    print("1. Old technical format still being used")
    print("2. Emoji and bullet points not replaced everywhere")
    print("3. _format_assumptions_text() still adding technical output")
    print("4. Comprehensive mode not using conversational format")

def test_pattern_matching():
    """Test specific pattern matching issues"""
    
    print("\n\n=== PATTERN MATCHING DEEP DIVE ===\n")
    
    # The pattern that should work but doesn't
    problem_pattern = r'(?i).*change.*goal.*(\$?[\d,M]+)'
    problem_query = "what if i increase my goal to 4000000"
    
    print(f"Testing pattern: {problem_pattern}")
    print(f"Against query: '{problem_query}'")
    
    match = re.search(problem_pattern, problem_query)
    
    if match:
        print(f"✓ Pattern matches!")
        print(f"  Groups: {match.groups()}")
    else:
        print(f"✗ Pattern doesn't match")
        
        # Try variations
        print("\nTrying pattern variations:")
        
        variations = [
            r'(?i).*change.*goal.*',  # Without capture group
            r'(?i).*increase.*goal.*(\$?[\d,M]+)',  # With increase
            r'(?i).*goal.*(\$?[\d,M]+)',  # Just goal and number
            r'(?i).*goal.*to.*(\$?[\d,M]+)',  # Goal to number
        ]
        
        for var in variations:
            if re.search(var, problem_query):
                print(f"  ✓ '{var}' matches")
            else:
                print(f"  ✗ '{var}' doesn't match")

if __name__ == "__main__":
    audit_calculation_patterns()
    test_pattern_matching()