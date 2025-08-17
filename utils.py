"""
Utility functions for IP-Landing-API
Contains helper functions for data validation, security, and common operations
"""
import re
import ipaddress
from datetime import datetime
from typing import Optional, Dict, Any

def validate_ip_address(ip_str: str) -> bool:
    """Validate if string is a valid IP address"""
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False

def is_private_ip(ip_str: str) -> bool:
    """Check if IP address is private/internal"""
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_private
    except ValueError:
        return False

def sanitize_user_agent(user_agent: str) -> str:
    """Sanitize user agent string for safe storage"""
    if not user_agent:
        return "Unknown"
    
    # Remove potentially harmful characters
    sanitized = re.sub(r'[<>"\';\\]', '', user_agent)
    # Limit length
    return sanitized[:500]

def validate_email_format(email: str) -> bool:
    """Enhanced email validation"""
    if not email or len(email) > 255:
        return False
    
    # RFC 5322 compliant regex (simplified)
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def clean_form_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and sanitize form data"""
    cleaned = {}
    for key, value in data.items():
        if isinstance(value, str):
            # Remove leading/trailing whitespace
            value = value.strip()
            # Remove null bytes and control characters
            value = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)
        cleaned[key] = value
    return cleaned

def format_timestamp(timestamp: datetime) -> str:
    """Format timestamp for display"""
    if not timestamp:
        return "Unknown"
    return timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')

def truncate_string(text: str, max_length: int = 100) -> str:
    """Safely truncate string with ellipsis"""
    if not text:
        return ""
    return text[:max_length] + "..." if len(text) > max_length else text

def detect_bot_user_agent(user_agent: str) -> bool:
    """Detect if user agent is likely a bot"""
    if not user_agent:
        return False
    
    bot_indicators = [
        'bot', 'crawler', 'spider', 'scraper', 'curl', 'wget', 
        'python-requests', 'http', 'monitor', 'test', 'scan'
    ]
    
    user_agent_lower = user_agent.lower()
    return any(indicator in user_agent_lower for indicator in bot_indicators)

def get_country_flag_emoji(country_code: str) -> str:
    """Get flag emoji for country code"""
    if not country_code or len(country_code) != 2:
        return "🌍"
    
    # Convert country code to flag emoji
    try:
        # This uses Unicode regional indicator symbols
        flag = ''.join(chr(ord(char) + 127397) for char in country_code.upper())
        return flag
    except:
        return "🌍"