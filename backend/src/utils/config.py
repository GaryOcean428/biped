"""
Advanced configuration management for TradeHub Platform
Provides environment-specific settings and advanced configuration options
"""
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import timedelta


@dataclass
class SecurityConfig:
    """Security configuration settings"""
    jwt_secret_key: str
    jwt_expiration_hours: int = 24
    jwt_refresh_expiration_days: int = 30
    password_min_length: int = 8
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    csrf_token_expiration_hours: int = 1
    https_only: bool = False
    secure_cookies: bool = False


@dataclass
class PerformanceConfig:
    """Performance configuration settings"""
    cache_default_timeout: int = 300  # 5 minutes
    cache_max_size: int = 1000
    response_compression_min_size: int = 1000
    database_pool_size: int = 10
    database_pool_timeout: int = 30
    database_pool_recycle: int = 3600  # 1 hour
    max_content_length: int = 16 * 1024 * 1024  # 16MB


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    auth_requests_per_minute: int = 10
    auth_window_minutes: int = 5
    api_requests_per_minute: int = 100
    api_window_minutes: int = 15
    global_requests_per_hour: int = 1000
    burst_allowance: int = 20


@dataclass
class MonitoringConfig:
    """Monitoring and logging configuration"""
    log_level: str = 'INFO'
    log_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    log_file_max_bytes: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5
    metrics_retention_hours: int = 24
    performance_alert_threshold_ms: int = 1000
    error_alert_threshold: int = 100


class ConfigManager:
    """Advanced configuration manager with environment-specific settings"""
    
    def __init__(self):
        self.environment = os.getenv('FLASK_ENV', 'development')
        self._config_cache: Dict[str, Any] = {}
    
    def get_security_config(self) -> SecurityConfig:
        """Get security configuration based on environment"""
        if 'security' not in self._config_cache:
            base_secret = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
            
            self._config_cache['security'] = SecurityConfig(
                jwt_secret_key=os.getenv('JWT_SECRET_KEY', f"{base_secret}-jwt"),
                jwt_expiration_hours=int(os.getenv('JWT_EXPIRATION_HOURS', '24')),
                jwt_refresh_expiration_days=int(os.getenv('JWT_REFRESH_DAYS', '30')),
                password_min_length=int(os.getenv('PASSWORD_MIN_LENGTH', '8')),
                max_login_attempts=int(os.getenv('MAX_LOGIN_ATTEMPTS', '5')),
                lockout_duration_minutes=int(os.getenv('LOCKOUT_DURATION_MINUTES', '15')),
                csrf_token_expiration_hours=int(os.getenv('CSRF_TOKEN_HOURS', '1')),
                https_only=os.getenv('HTTPS_ONLY', 'false').lower() == 'true',
                secure_cookies=os.getenv('SECURE_COOKIES', 'false').lower() == 'true'
            )
        
        return self._config_cache['security']
    
    def get_performance_config(self) -> PerformanceConfig:
        """Get performance configuration based on environment"""
        if 'performance' not in self._config_cache:
            # Adjust defaults based on environment
            if self.environment == 'production':
                default_cache_timeout = 900  # 15 minutes in production
                default_pool_size = 20
            else:
                default_cache_timeout = 300  # 5 minutes in development
                default_pool_size = 5
            
            self._config_cache['performance'] = PerformanceConfig(
                cache_default_timeout=int(os.getenv('CACHE_TIMEOUT', str(default_cache_timeout))),
                cache_max_size=int(os.getenv('CACHE_MAX_SIZE', '1000')),
                response_compression_min_size=int(os.getenv('COMPRESSION_MIN_SIZE', '1000')),
                database_pool_size=int(os.getenv('DB_POOL_SIZE', str(default_pool_size))),
                database_pool_timeout=int(os.getenv('DB_POOL_TIMEOUT', '30')),
                database_pool_recycle=int(os.getenv('DB_POOL_RECYCLE', '3600')),
                max_content_length=int(os.getenv('MAX_CONTENT_LENGTH', str(16 * 1024 * 1024)))
            )
        
        return self._config_cache['performance']
    
    def get_rate_limit_config(self) -> RateLimitConfig:
        """Get rate limiting configuration"""
        if 'rate_limit' not in self._config_cache:
            # Stricter limits in production
            if self.environment == 'production':
                auth_limit = 5
                api_limit = 60
            else:
                auth_limit = 10
                api_limit = 100
            
            self._config_cache['rate_limit'] = RateLimitConfig(
                auth_requests_per_minute=int(os.getenv('AUTH_RATE_LIMIT', str(auth_limit))),
                auth_window_minutes=int(os.getenv('AUTH_WINDOW_MINUTES', '5')),
                api_requests_per_minute=int(os.getenv('API_RATE_LIMIT', str(api_limit))),
                api_window_minutes=int(os.getenv('API_WINDOW_MINUTES', '15')),
                global_requests_per_hour=int(os.getenv('GLOBAL_RATE_LIMIT', '1000')),
                burst_allowance=int(os.getenv('BURST_ALLOWANCE', '20'))
            )
        
        return self._config_cache['rate_limit']
    
    def get_monitoring_config(self) -> MonitoringConfig:
        """Get monitoring and logging configuration"""
        if 'monitoring' not in self._config_cache:
            # More verbose logging in development
            if self.environment == 'development':
                log_level = 'DEBUG'
            else:
                log_level = 'INFO'
            
            self._config_cache['monitoring'] = MonitoringConfig(
                log_level=os.getenv('LOG_LEVEL', log_level),
                log_format=os.getenv('LOG_FORMAT', 
                                   '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
                log_file_max_bytes=int(os.getenv('LOG_FILE_MAX_BYTES', str(10 * 1024 * 1024))),
                log_backup_count=int(os.getenv('LOG_BACKUP_COUNT', '5')),
                metrics_retention_hours=int(os.getenv('METRICS_RETENTION_HOURS', '24')),
                performance_alert_threshold_ms=int(os.getenv('PERF_ALERT_THRESHOLD_MS', '1000')),
                error_alert_threshold=int(os.getenv('ERROR_ALERT_THRESHOLD', '100'))
            )
        
        return self._config_cache['monitoring']
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration with advanced options"""
        database_url = os.getenv('DATABASE_URL')
        perf_config = self.get_performance_config()
        
        if database_url:
            # Railway PostgreSQL or other cloud database
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://', 1)
            
            config = {
                'SQLALCHEMY_DATABASE_URI': database_url,
                'SQLALCHEMY_ENGINE_OPTIONS': {
                    'pool_size': perf_config.database_pool_size,
                    'pool_pre_ping': True,
                    'pool_recycle': perf_config.database_pool_recycle,
                    'pool_timeout': perf_config.database_pool_timeout,
                    'max_overflow': perf_config.database_pool_size // 2
                }
            }
        else:
            # Local SQLite with optimizations
            db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'app.db')
            config = {
                'SQLALCHEMY_DATABASE_URI': f"sqlite:///{db_path}",
                'SQLALCHEMY_ENGINE_OPTIONS': {
                    'pool_pre_ping': True,
                    'pool_recycle': 300,  # Shorter recycle for SQLite
                    'connect_args': {
                        'check_same_thread': False,
                        'timeout': 30
                    }
                }
            }
        
        config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        config['SQLALCHEMY_RECORD_QUERIES'] = self.environment == 'development'
        
        return config
    
    def get_flask_config(self) -> Dict[str, Any]:
        """Get Flask application configuration"""
        security_config = self.get_security_config()
        performance_config = self.get_performance_config()
        
        config = {
            'SECRET_KEY': os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'),
            'JWT_SECRET_KEY': security_config.jwt_secret_key,
            'JWT_ACCESS_TOKEN_EXPIRES': timedelta(hours=security_config.jwt_expiration_hours),
            'JWT_REFRESH_TOKEN_EXPIRES': timedelta(days=security_config.jwt_refresh_expiration_days),
            'MAX_CONTENT_LENGTH': performance_config.max_content_length,
            'PREFERRED_URL_SCHEME': 'https' if security_config.https_only else 'http',
            'SESSION_COOKIE_SECURE': security_config.secure_cookies,
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SAMESITE': 'Lax',
            'PERMANENT_SESSION_LIFETIME': timedelta(hours=security_config.jwt_expiration_hours)
        }
        
        # Add database configuration
        config.update(self.get_database_config())
        
        # Environment-specific settings
        if self.environment == 'production':
            config.update({
                'DEBUG': False,
                'TESTING': False,
                'PROPAGATE_EXCEPTIONS': False
            })
        elif self.environment == 'development':
            config.update({
                'DEBUG': True,
                'TESTING': False,
                'PROPAGATE_EXCEPTIONS': True
            })
        elif self.environment == 'testing':
            config.update({
                'DEBUG': False,
                'TESTING': True,
                'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
                'WTF_CSRF_ENABLED': False
            })
        
        return config
    
    def validate_config(self) -> list:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Security validation
        security_config = self.get_security_config()
        if security_config.jwt_secret_key == 'dev-secret-key-change-in-production-jwt':
            issues.append("JWT secret key is using default value - change in production")
        
        if self.environment == 'production':
            if not security_config.https_only:
                issues.append("HTTPS should be enabled in production")
            
            if not security_config.secure_cookies:
                issues.append("Secure cookies should be enabled in production")
        
        # Performance validation
        performance_config = self.get_performance_config()
        if performance_config.database_pool_size < 5:
            issues.append("Database pool size might be too small for production")
        
        # Rate limiting validation
        rate_limit_config = self.get_rate_limit_config()
        if rate_limit_config.auth_requests_per_minute > 20:
            issues.append("Authentication rate limit might be too permissive")
        
        return issues
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get current environment information for debugging"""
        return {
            'environment': self.environment,
            'python_version': os.sys.version,
            'config_validation_issues': self.validate_config(),
            'security_config': {
                'jwt_expiration_hours': self.get_security_config().jwt_expiration_hours,
                'https_only': self.get_security_config().https_only,
                'secure_cookies': self.get_security_config().secure_cookies
            },
            'performance_config': {
                'cache_timeout': self.get_performance_config().cache_default_timeout,
                'db_pool_size': self.get_performance_config().database_pool_size,
                'compression_enabled': True
            }
        }


# Global configuration manager instance
config_manager = ConfigManager()