"""
Application factory module for creating Flask application with OOP architecture.
"""
import os
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from datetime import timedelta

# Import modules using relative imports
from src.utils.database import DatabaseInterface
from src.repositories.user_repository import UserRepository
from src.repositories.account_repository import AccountRepository
from src.repositories.account_history_repository import AccountHistoryRepository
from src.repositories.tag_repository import TagRepository
from src.repositories.exchange_rate_repository import ExchangeRateRepository
from src.services.user_service import UserService
from src.services.account_service import AccountService
from src.services.exchange_rate_service import ExchangeRateService
from src.services.networth_service import NetworthService
from src.controllers.user_controller import UserController
from src.controllers.account_controller import AccountController
from src.controllers.networth_controller import NetworthController
from src.controllers.user_routes import create_user_blueprint
from src.controllers.account_routes import create_account_blueprint
from src.controllers.networth_routes import create_networth_blueprint


class AppFactory:
    """Factory class for creating and configuring Flask application."""
    
    @staticmethod
    def create_app():
        """Create and configure Flask application with dependency injection."""
        app = Flask(__name__, 
                   template_folder=os.path.abspath('templates'),
                   static_folder=os.path.abspath('static'))
        
        # Application configuration
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
        app.config['DATABASE'] = os.environ.get('DATABASE_PATH', 'networth.db')
        
        # Security configuration
        app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour CSRF token lifetime
        app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)  # 2 hour session timeout
        app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
        
        # Initialize security extensions
        csrf = CSRFProtect(app)
        
        # Rate limiting
        limiter = Limiter(
            key_func=get_remote_address,
            app=app,
            default_limits=["1000 per hour", "100 per minute"]
        )
        
        # Security headers (only in production)
        if os.environ.get('FLASK_ENV') == 'production':
            Talisman(app, 
                    force_https=True,
                    strict_transport_security=True,
                    content_security_policy={
                        'default-src': "'self'",
                        'script-src': ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
                        'style-src': ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
                        'font-src': ["'self'", "https://cdn.jsdelivr.net"],
                        'img-src': ["'self'", "data:"],
                        'connect-src': ["'self'"]
                    })
        
        # Initialize database and dependencies
        db_interface = DatabaseInterface(app.config['DATABASE'])
        db_interface.create_tables()
        
        # Initialize repositories
        user_repository = UserRepository(db_interface)
        account_repository = AccountRepository(db_interface)
        account_history_repository = AccountHistoryRepository(db_interface)
        tag_repository = TagRepository(db_interface)
        exchange_rate_repository = ExchangeRateRepository(db_interface)
        
        # Initialize services
        user_service = UserService(user_repository, db_interface)
        exchange_rate_service = ExchangeRateService(db_interface, exchange_rate_repository)
        account_service = AccountService(account_repository, account_history_repository, tag_repository)
        networth_service = NetworthService(account_repository, account_history_repository, tag_repository, exchange_rate_service)
        
        # Initialize controllers
        user_controller = UserController(user_service)
        account_controller = AccountController(account_service, db_interface)
        networth_controller = NetworthController(networth_service)
        
        # Register blueprints
        AppFactory._register_blueprints(app, user_controller, account_controller, networth_controller, limiter)
        
        return app
    
    @staticmethod
    def _register_blueprints(app, user_controller, account_controller, networth_controller, limiter):
        """Register all blueprints with the application."""
        
        # Create and register blueprints
        user_bp = create_user_blueprint(user_controller, limiter)
        account_bp = create_account_blueprint(account_controller, limiter)
        networth_bp = create_networth_blueprint(networth_controller)
        
        app.register_blueprint(user_bp)
        app.register_blueprint(account_bp)
        app.register_blueprint(networth_bp)