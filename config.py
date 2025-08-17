"""
Configuration management for IP-Landing-API
Centralizes environment variables and app settings
"""
import os
from datetime import timedelta

class Config:
    # Basic Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.environ.get('FLASK_DEBUG', '1') == '1'
    
    # Database configuration
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    # Security settings
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    
    # API configuration
    EXTERNAL_API_URL = os.environ.get('EXTERNAL_API_URL', 'http://httpbin.org/post')
    LOCATION_API_TIMEOUT = int(os.environ.get('LOCATION_API_TIMEOUT', '10'))
    
    # Rate limiting
    VISITOR_LOG_COOLDOWN_MINUTES = int(os.environ.get('VISITOR_LOG_COOLDOWN_MINUTES', '5'))
    MAX_FORM_SUBMISSIONS_PER_IP_PER_HOUR = int(os.environ.get('MAX_FORM_SUBMISSIONS_PER_IP_PER_HOUR', '10'))
    
    # Data validation limits
    MAX_NAME_LENGTH = 100
    MAX_EMAIL_LENGTH = 255
    MAX_MESSAGE_LENGTH = 1000
    MIN_NAME_LENGTH = 2
    
    # Performance settings
    MAX_VISITOR_LOGS_DISPLAY = int(os.environ.get('MAX_VISITOR_LOGS_DISPLAY', '100'))
    
class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True