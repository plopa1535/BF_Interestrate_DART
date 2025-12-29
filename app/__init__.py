"""
Flask Application Factory
Creates and configures the Flask application.
"""

from flask import Flask, render_template
from flask_cors import CORS
import logging
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config


def create_app(config_name: str = None):
    """
    Create and configure the Flask application.
    
    Args:
        config_name: Configuration name (development, production, testing)
        
    Returns:
        Configured Flask application
    """
    app = Flask(
        __name__,
        template_folder='../templates',
        static_folder='../static'
    )
    
    # Load configuration
    config = get_config()
    app.config.from_object(config)
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if app.config.get('DEBUG') else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Enable CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:*", "http://127.0.0.1:*"],
            "methods": ["GET", "POST"],
            "allow_headers": ["Content-Type"]
        }
    })
    
    # Register blueprints
    from app.routes.api import api_bp
    app.register_blueprint(api_bp)
    
    # Main page route
    @app.route('/')
    def index():
        """Render the main dashboard page."""
        return render_template('index.html')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {"status": "error", "error": "Resource not found"}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return {"status": "error", "error": "Internal server error"}, 500
    
    # Log startup info
    logger.info("=" * 50)
    logger.info("Interest Rate Monitor Application Started")
    logger.info(f"Debug Mode: {app.config.get('DEBUG')}")
    logger.info(f"FRED API Key: {'Configured' if config.FRED_API_KEY else 'Not Set'}")
    logger.info(f"ECOS API Key: {'Configured' if config.ECOS_API_KEY else 'Not Set'}")
    logger.info(f"DART API Key: {'Configured' if config.DART_API_KEY else 'Not Set'}")
    logger.info(f"Gemini API Key: {'Configured' if config.GEMINI_API_KEY else 'Not Set'}")
    logger.info(f"Groq API Key: {'Configured' if config.GROQ_API_KEY else 'Not Set'}")
    logger.info("=" * 50)
    
    return app
