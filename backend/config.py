import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # File upload settings
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024 * 1024  # 50GB
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    
    # Database settings
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///migrations.db')
    
    # Migration settings
    MAX_CONCURRENT_MIGRATIONS = int(os.getenv('MAX_CONCURRENT_MIGRATIONS', 5))
    MIGRATION_TIMEOUT = int(os.getenv('MIGRATION_TIMEOUT', 3600))  # 1 hour
    
    # Storage settings
    MIN_FREE_SPACE_PERCENT = float(os.getenv('MIN_FREE_SPACE_PERCENT', 10.0))
    
    # Security settings
    ENABLE_ENCRYPTION = os.getenv('ENABLE_ENCRYPTION', 'true').lower() == 'true'
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', '')
    
    # Logging settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'app.log')
    
    # AWS S3 settings (for cloud migrations)
    AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY', '')
    AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY', '')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    AWS_S3_BUCKET = os.getenv('AWS_S3_BUCKET', '')
    
    # Email settings (for notifications)
    SMTP_SERVER = os.getenv('SMTP_SERVER', '')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    NOTIFICATION_EMAIL = os.getenv('NOTIFICATION_EMAIL', '')
    
    @classmethod
    def init_app(cls, app):
        """Initialize application with configuration"""
        app.config.from_object(cls)
        
        # Ensure upload folder exists
        os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        
        # Configure logging
        import logging
        from logging.handlers import RotatingFileHandler
        
        handler = RotatingFileHandler(
            cls.LOG_FILE,
            maxBytes=1024 * 1024 * 10,  # 10MB
            backupCount=10
        )
        handler.setLevel(getattr(logging, cls.LOG_LEVEL))
        handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        app.logger.addHandler(handler)
        app.logger.setLevel(getattr(logging, cls.LOG_LEVEL))

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
