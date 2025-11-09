"""
Basic packet decoder utilities and helper functions.
Provides complement-pair validation and common decoder utilities.
"""


def is_complement_pair(cmp_b: int, val_b: int) -> bool:
    """
    Validate that two bytes form a complement-value pair.
    The complement byte should be the bitwise NOT of the value byte.
    
    Args:
        cmp_b: The complement byte
        val_b: The value byte
    
    Returns:
        True if the bytes form a valid complement pair, False otherwise
    """
    return ((~val_b) & 0xFF) == (cmp_b & 0xFF)


def popcount4(n: int) -> int:
    """
    Count 1-bits in the lower 4 bits (Python 3.8-safe).
    
    Args:
        n: Integer value to count bits in
    
    Returns:
        Number of 1-bits in the lower 4 bits
    """
    n &= 0x0F
    return ((n & 1) + ((n >> 1) & 1) + ((n >> 2) & 1) + ((n >> 3) & 1))


def normalize_value(v: int) -> int:
    """
    Normalize packet value, treating 0xAA (170) as 'no data' sentinel.
    
    Args:
        v: The value to normalize
    
    Returns:
        0 if value is 0xAA, otherwise the original value
    """
    return 0 if v == 0xAA else v
