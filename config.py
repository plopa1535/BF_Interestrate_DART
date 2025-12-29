import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class."""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # API Keys
    FRED_API_KEY = os.getenv('FRED_API_KEY')
    ECOS_API_KEY = os.getenv('ECOS_API_KEY')
    DART_API_KEY = os.getenv('DART_API_KEY')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    
    # Cache Settings (in seconds)
    RATE_CACHE_TTL = 3600  # 1 hour for rate data
    ANALYSIS_CACHE_TTL = 21600  # 6 hours for AI analysis
    NEWS_CACHE_TTL = 1800  # 30 minutes for news
    
    # Data Settings
    DEFAULT_DAYS = 90  # Default period for rate data
    
    # API Rate Limiting
    RATE_LIMIT_PER_MINUTE = 60


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    TESTING = True


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on environment."""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
