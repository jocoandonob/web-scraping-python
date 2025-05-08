import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from fastapi import HTTPException, status, Request

from app.core.config import settings

logger = logging.getLogger(__name__)

# In-memory storage for rate limiting
# Structure:  {ip_address: [timestamp1, timestamp2, ...]}
request_history: Dict[str, List[datetime]] = {}

def get_client_ip(request: Request) -> str:
    """Get the client IP address from a request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host or "127.0.0.1"

def clean_old_requests() -> None:
    """Clean requests older than 1 minute from the history"""
    now = datetime.now()
    cutoff = now - timedelta(minutes=1)
    
    for ip, timestamps in list(request_history.items()):
        # Filter out old timestamps
        new_timestamps = [ts for ts in timestamps if ts > cutoff]
        
        # Update history or remove empty entries
        if new_timestamps:
            request_history[ip] = new_timestamps
        else:
            del request_history[ip]

def rate_limiter(request: Request) -> None:
    """
    Rate limiting middleware function
    
    Args:
        request: The FastAPI request object
    
    Raises:
        HTTPException: If rate limit is exceeded
    """
    # Clean up old requests
    clean_old_requests()
    
    # Get client IP
    ip = get_client_ip(request)
    
    # Get limit from settings
    limit = settings.RATE_LIMIT_PER_MINUTE
    
    # Initialize request history for this IP if not exists
    if ip not in request_history:
        request_history[ip] = []
    
    # Check if rate limit is exceeded
    if len(request_history[ip]) >= limit:
        logger.warning(f"Rate limit exceeded for IP: {ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": "60"}
        )
    
    # Add current timestamp to history
    request_history[ip].append(datetime.now())

def get_remaining_requests(ip: str = "127.0.0.1") -> int:
    """
    Get remaining requests for an IP
    
    Args:
        ip: IP address to check
        
    Returns:
        Number of remaining requests allowed in current window
    """
    # Clean up old requests first
    clean_old_requests()
    
    # Get limit from settings
    limit = settings.RATE_LIMIT_PER_MINUTE
    
    # Check current usage
    current = len(request_history.get(ip, []))
    
    # Calculate remaining
    return max(0, limit - current)
