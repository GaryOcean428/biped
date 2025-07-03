"""
Railway-Optimized Configuration for Biped Platform
Uses internal service references for PostgreSQL and Redis
"""

import os
from datetime import timedelta

class Config:
    """Base configuration with Railway internal networking"""
    
    # Basic Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Railway Internal Service References (Preferred)
    DATABASE_URL = os.environ.get('DATABASE_PRIVATE_URL') or os.environ.get('DATABASE_URL')
    REDIS_URL = os.environ.get('REDIS_PRIVATE_URL') or os.environ.get('REDIS_URL')
    
    # Fix postgres:// to postgresql:// for SQLAlchemy compatibility
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    # SQLAlchemy Configuration
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 20,
        'pool_timeout': 30
    }
    
    # Redis Configuration for Rate Limiting and Caching
    RATELIMIT_STORAGE_URL = REDIS_URL
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Celery Configuration (Background Tasks)
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TIMEZONE = 'UTC'
    CELERY_ENABLE_UTC = True
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
    
    # Security Configuration
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # CORS Configuration
    CORS_ORIGINS = ['*']  # Configure specific origins in production
    CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization']
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.environ.get('DATA_DIR', '/data') + '/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
    
    # API Configuration
    API_TITLE = 'Biped Platform API'
    API_VERSION = 'v2.0'
    OPENAPI_VERSION = '3.0.2'
    OPENAPI_URL_PREFIX = '/api/docs'
    OPENAPI_SWAGGER_UI_PATH = '/swagger'
    OPENAPI_SWAGGER_UI_URL = 'https://cdn.jsdelivr.net/npm/swagger-ui-dist/'
    
    # Rate Limiting Configuration
    RATELIMIT_DEFAULT = "1000 per hour, 100 per minute"
    RATELIMIT_HEADERS_ENABLED = True
    RATELIMIT_SWALLOW_ERRORS = True  # Don't crash on Redis connection issues
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s %(levelname)s %(name)s %(message)s'
    
    # Environment-Specific Settings
    ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
    DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'
    TESTING = False
    
    # Railway-Specific Configuration
    PORT = int(os.environ.get('PORT', 8080))
    HOST = '0.0.0.0'
    
    # Data Directory (Railway Volume)
    DATA_DIR = os.environ.get('DATA_DIR', '/data')
    
    # Computer Vision Configuration
    OPENCV_HEADLESS = os.environ.get('OPENCV_HEADLESS', 'true').lower() == 'true'
    CV_FALLBACK_MODE = os.environ.get('CV_FALLBACK_MODE', 'true').lower() == 'true'
    
    # Performance Configuration
    SEND_FILE_MAX_AGE_DEFAULT = timedelta(hours=12)
    COMPRESS_MIMETYPES = [
        'text/html', 'text/css', 'text/xml', 'application/json',
        'application/javascript', 'application/xml+rss', 'application/atom+xml',
        'image/svg+xml'
    ]
    COMPRESS_LEVEL = 6
    COMPRESS_MIN_SIZE = 500

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    
    # Use local services if Railway services not available
    if not Config.DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///biped_dev.db'
    
    if not Config.REDIS_URL:
        REDIS_URL = 'redis://localhost:6379/0'
        RATELIMIT_STORAGE_URL = REDIS_URL
        CACHE_REDIS_URL = REDIS_URL
        CELERY_BROKER_URL = REDIS_URL
        CELERY_RESULT_BACKEND = REDIS_URL
    
    # Relaxed security for development
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Production configuration for Railway deployment"""
    DEBUG = False
    TESTING = False
    
    # Enhanced security for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # Force HTTPS
    PREFERRED_URL_SCHEME = 'https'
    
    # Stricter CORS for production
    CORS_ORIGINS = [
        'https://biped.up.railway.app',
        'https://*.railway.app'
    ]
    
    # Production logging
    LOG_LEVEL = 'WARNING'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    
    # Use in-memory databases for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    REDIS_URL = 'redis://localhost:6379/1'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    
    # Faster password hashing for tests
    BCRYPT_LOG_ROUNDS = 4

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('ENVIRONMENT', 'development')
    return config.get(env, config['default'])

