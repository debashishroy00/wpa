#!/usr/bin/env python3
"""
Test number extraction improvements
"""

import re

def extract_numbers_from_message(message: str):
    """Extract monetary amounts from message"""
    
    numbers = []
    
    # Pattern 1: Dollar amounts like $3M, $3,000,000, $1.5M
    dollar_pattern = r'\$(\d+(?:[.,]\d+)*)\s*([Mm]illion|[Mm])?'
    for match in re.finditer(dollar_pattern, message):
        number_str = match.group(1).replace(',', '')
        multiplier_str = match.group(2)
        
        try:
            value = float(number_str)
            if multiplier_str and multiplier_str.lower().startswith('m'):
                value *= 1000000
            numbers.append(value)
        except ValueError:
            continue
    
    # Pattern 2: Plain numbers with million/M suffix
    million_pattern = r'(\d+(?:[.,]\d+)*)\s*([Mm]illion|[Mm])\b'
    for match in re.finditer(million_pattern, message):
        number_str = match.group(1).replace(',', '')
        try:
            value = float(number_str) * 1000000
            numbers.append(value)
        except ValueError:
            continue
    
    # Pattern 3: Large plain numbers (likely dollar amounts) including with commas
    large_number_pattern = r'\b(\d{1,3}(?:,\d{3})*)\b'  # Numbers with commas like 2,500,000
    for match in re.finditer(large_number_pattern, message):
        try:
            value = float(match.group(1).replace(',', ''))
            if value >= 1000:  # Only consider significant amounts
                numbers.append(value)
        except ValueError:
            continue
    
    # Pattern 4: Numbers without commas but 6+ digits
    plain_number_pattern = r'\b(\d{6,})\b'  # 6+ digits like 2500000
    for match in re.finditer(plain_number_pattern, message):
        try:
            value = float(match.group(1))
            numbers.append(value)
        except ValueError:
            continue
    
    # Remove duplicates and sort
    return sorted(list(set(numbers)))

def extract_growth_rate(message: str):
    """Extract growth rate percentage from message"""
    
    # Try to find percentage in message
    pct_matches = re.findall(r'(\d+(?:\.\d+)?)\s*%', message)
    if pct_matches:
        try:
            return float(pct_matches[0]) / 100
        except ValueError:
            pass
    
    return None

def main():
    test_queries = [
        "reduced goal to 2,500000, how many years saved",
        "what if my investment growth is 10%", 
        "reduce goal to $3M",
        "consider 7.5% growth rate",
        "If I reduce my retirement goal to $3,000,000"
    ]
    
    print("Testing number and growth rate extraction:")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        numbers = extract_numbers_from_message(query)
        growth_rate = extract_growth_rate(query)
        
        print(f"Numbers extracted: {numbers}")
        print(f"Growth rate extracted: {growth_rate}")
        print("-" * 50)

if __name__ == "__main__":
    main()