#!/usr/bin/env python3
"""
Interest Rate Monitor - Application Entry Point
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app import create_app

# Create application instance
app = create_app()


def validate_config():
    """Validate required configuration."""
    warnings = []

    if not os.getenv('FRED_API_KEY'):
        warnings.append("FRED_API_KEY not set - US rate data will use mock data")

    if not os.getenv('ECOS_API_KEY'):
        warnings.append("ECOS_API_KEY not set - Korean rate data will use mock data")

    if not os.getenv('GEMINI_API_KEY'):
        warnings.append("GEMINI_API_KEY not set - AI analysis will use default messages")

    if warnings:
        print("\n[WARNING] Configuration Warnings:")
        for warning in warnings:
            print(f"   - {warning}")
        print()

    return len(warnings) == 0


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("Interest Rate Monitor")
    print("=" * 60)

    # Validate configuration
    validate_config()

    # Get configuration
    debug = os.getenv('FLASK_DEBUG', '1') == '1'
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))

    print(f"Starting server on http://{host}:{port}")
    print(f"Debug mode: {'ON' if debug else 'OFF'}")
    print("=" * 60 + "\n")
    
    # Run the application
    app.run(
        host=host,
        port=port,
        debug=debug
    )
