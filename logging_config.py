"""
Logging configuration for IP-Landing-API
Provides structured logging for better monitoring and debugging
"""
import logging
import sys
from datetime import datetime

def setup_logging(debug_mode=False):
    """Configure application logging"""
    log_level = logging.DEBUG if debug_mode else logging.INFO
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    app_logger = logging.getLogger('ip_landing_api')
    app_logger.setLevel(log_level)
    
    return app_logger

# Create application logger
logger = setup_logging()

def log_visitor_activity(ip_address, action, details=None):
    """Log visitor activities for monitoring"""
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'ip_address': ip_address,
        'action': action
    }
    
    if details:
        log_data.update(details)
    
    logger.info(f"Visitor Activity: {log_data}")

def log_security_event(event_type, ip_address, details=None):
    """Log security-related events"""
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'event_type': event_type,
        'ip_address': ip_address
    }
    
    if details:
        log_data.update(details)
    
    logger.warning(f"Security Event: {log_data}")

def log_api_error(api_name, error, ip_address=None):
    """Log API-related errors"""
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'api_name': api_name,
        'error': str(error)
    }
    
    if ip_address:
        log_data['ip_address'] = ip_address
    
    logger.error(f"API Error: {log_data}")