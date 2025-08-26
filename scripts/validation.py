"""
Validation utilities for Prawl application.
Provides input validation and sanitization functions.
"""

import logging
from typing import Union, Any, Tuple

logger = logging.getLogger(__name__)

def validate_range(value: Union[int, float], min_val: Union[int, float], max_val: Union[int, float], 
                  default: Union[int, float] = None) -> Union[int, float]:
    """
    Validate that a value is within a specified range.
    
    Args:
        value: Value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        default: Default value if validation fails
        
    Returns:
        Validated value within range
    """
    try:
        if isinstance(value, str):
            value = float(value) if '.' in value else int(value)
            
        if value < min_val:
            logger.warning(f"Value {value} below minimum {min_val}, clamping")
            return min_val
        elif value > max_val:
            logger.warning(f"Value {value} above maximum {max_val}, clamping")
            return max_val
        else:
            return value
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid value type for range validation: {value}, error: {e}")
        return default if default is not None else min_val

def validate_positive_int(value: Any, default: int = 1) -> int:
    """
    Validate that a value is a positive integer.
    
    Args:
        value: Value to validate
        default: Default value if validation fails
        
    Returns:
        Positive integer
    """
    try:
        result = int(value)
        return max(1, result)
    except (ValueError, TypeError):
        logger.warning(f"Invalid integer value: {value}, using default: {default}")
        return default

def validate_frequency(frequency: Any) -> int:
    """
    Validate audio frequency for Windows beep function.
    
    Args:
        frequency: Frequency value to validate
        
    Returns:
        Valid frequency (37-32767 Hz)
    """
    return validate_range(frequency, 37, 32767, 500)

def validate_duration(duration: Any) -> int:
    """
    Validate audio duration for Windows beep function.
    
    Args:
        duration: Duration value to validate
        
    Returns:
        Valid duration (1-5000 ms)
    """
    return validate_range(duration, 1, 5000, 72)

def sanitize_key_name(key_name: str) -> str:
    """
    Sanitize key name input.
    
    Args:
        key_name: Raw key name input
        
    Returns:
        Sanitized key name
    """
    if not isinstance(key_name, str):
        return 'unknown'
        
    # Remove whitespace and convert to lowercase
    sanitized = key_name.strip().lower()
    
    # Validate against allowed characters
    allowed_chars = set('abcdefghijklmnopqrstuvwxyz0123456789_')
    sanitized = ''.join(c for c in sanitized if c in allowed_chars)
    
    return sanitized if sanitized else 'unknown'

def validate_config_value(key: str, value: Any, config_schema: dict) -> Any:
    """
    Validate configuration value against schema.
    
    Args:
        key: Configuration key
        value: Value to validate
        config_schema: Schema defining allowed values/ranges
        
    Returns:
        Validated value
    """
    if key not in config_schema:
        logger.warning(f"Unknown config key: {key}")
        return value
        
    schema = config_schema[key]
    
    if 'type' in schema:
        try:
            if schema['type'] == 'int':
                value = int(value)
            elif schema['type'] == 'float':
                value = float(value)
            elif schema['type'] == 'bool':
                value = bool(value)
            elif schema['type'] == 'str':
                value = str(value)
        except (ValueError, TypeError):
            logger.error(f"Type conversion failed for {key}: {value}")
            return schema.get('default', value)
    
    if 'min' in schema and 'max' in schema:
        value = validate_range(value, schema['min'], schema['max'], schema.get('default'))
    
    return value