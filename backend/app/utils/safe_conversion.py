"""
Safe conversion utilities for handling financial data
Prevents crashes from empty strings, None values, and invalid formats
"""

def safe_float(value, default=0.0):
    """
    Safely convert a value to float with fallback to default
    Handles None, empty strings, and invalid values
    
    Args:
        value: The value to convert
        default: Default value to return if conversion fails
        
    Returns:
        float: The converted value or default
    """
    if value is None:
        return default
    
    if isinstance(value, (int, float)):
        return float(value)
    
    if isinstance(value, str):
        # Handle empty string
        if value.strip() == '':
            return default
        
        # Try to clean common financial formatting
        cleaned = value.replace(',', '').replace('$', '').replace('%', '').strip()
        if cleaned == '':
            return default
        
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return default
    
    # For any other type, try direct conversion
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    """
    Safely convert a value to int with fallback to default
    
    Args:
        value: The value to convert
        default: Default value to return if conversion fails
        
    Returns:
        int: The converted value or default
    """
    if value is None:
        return default
    
    if isinstance(value, int):
        return value
    
    if isinstance(value, float):
        return int(value)
    
    if isinstance(value, str):
        if value.strip() == '':
            return default
        
        cleaned = value.replace(',', '').replace('$', '').strip()
        if cleaned == '':
            return default
        
        try:
            return int(float(cleaned))  # Convert via float to handle decimals
        except (ValueError, TypeError):
            return default
    
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_get_numeric(data_dict, key, default=0.0):
    """
    Safely get a numeric value from a dictionary
    
    Args:
        data_dict: Dictionary to extract from
        key: Key to look for
        default: Default value if key missing or conversion fails
        
    Returns:
        float: The numeric value or default
    """
    if not isinstance(data_dict, dict):
        return default
    
    value = data_dict.get(key)
    return safe_float(value, default)