"""
Networth Tracker - Personal Finance Management System

This is the main application entry point that creates and runs the Flask app.
All routes are registered via blueprints in the controllers package.
"""
import os
from src.app_factory import AppFactory

# Create the Flask application using the factory pattern
app = AppFactory.create_app()

if __name__ == '__main__':
    # Development server configuration
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
