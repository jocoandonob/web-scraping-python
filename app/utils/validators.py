import re
from typing import Optional
from urllib.parse import urlparse

class ValidationError(Exception):
    """Custom validation error"""
    pass

def validate_url(url: str) -> bool:
    """
    Validate a URL string
    
    Args:
        url: The URL to validate
        
    Returns:
        True if URL is valid
        
    Raises:
        ValidationError: If the URL is invalid
    """
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            raise ValidationError(f"Invalid URL structure: {url}")
        
        # Check for common schemes
        if result.scheme not in ['http', 'https']:
            raise ValidationError(f"URL must use HTTP or HTTPS scheme: {url}")
        
        # Check if domain looks valid (basic check)
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        if not re.match(domain_pattern, result.netloc):
            raise ValidationError(f"Invalid domain in URL: {url}")
        
        return True
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"URL validation failed: {str(e)}")

def validate_selector(selector: Optional[str]) -> bool:
    """
    Validate a CSS selector string
    
    Args:
        selector: The CSS selector to validate
        
    Returns:
        True if selector is valid or None
        
    Raises:
        ValidationError: If the selector is invalid
    """
    if selector is None:
        return True
    
    # Basic validation for obviously invalid selectors
    if len(selector) > 1000:
        raise ValidationError("Selector is too long")
    
    # Check for common CSS selector injection risks
    dangerous_patterns = [
        r'<\s*script',  # Script tags
        r'javascript:',  # JavaScript protocol
        r'@import',      # CSS imports
        r'expression\(',  # CSS expressions
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, selector, re.IGNORECASE):
            raise ValidationError(f"Selector contains potentially dangerous content: {selector}")
    
    return True
