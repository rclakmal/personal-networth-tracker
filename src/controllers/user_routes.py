"""
User routes blueprint for authentication and user management.
"""
from flask import Blueprint

def create_user_blueprint(user_controller, limiter):
    """Create and configure user routes blueprint."""
    user_bp = Blueprint('user', __name__)
    
    # Authentication routes with stricter rate limiting
    user_bp.add_url_rule('/login', 'login', 
                         limiter.limit("10 per minute")(user_controller.login), 
                         methods=['GET', 'POST'])
    user_bp.add_url_rule('/logout', 'logout', user_controller.logout, methods=['POST'])
    user_bp.add_url_rule('/register', 'register', 
                         limiter.limit("5 per minute")(user_controller.register), 
                         methods=['GET', 'POST'])
    
    # User management routes
    user_bp.add_url_rule('/profile', 'profile', user_controller.profile, methods=['GET', 'POST'])
    user_bp.add_url_rule('/change-password', 'change_password', 
                         limiter.limit("5 per minute")(user_controller.change_password), 
                         methods=['GET', 'POST'])
    user_bp.add_url_rule('/api/user/currency', 'api_update_currency',
                         user_controller.update_currency, methods=['POST'])
    
    return user_bp
