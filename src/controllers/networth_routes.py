"""
Networth routes blueprint for charts, currencies, and networth data.
"""
from flask import Blueprint, render_template, session, redirect, url_for

def create_networth_blueprint(networth_controller):
    """Create and configure networth routes blueprint."""
    networth_bp = Blueprint('networth', __name__)
    
    def require_login():
        """Check if user is logged in"""
        if not session.get('user_id'):
            return redirect(url_for('user.login'))
        return None
    
    # Home page
    @networth_bp.route('/')
    def home():
        """Home page"""
        auth_redirect = require_login()
        if auth_redirect:
            return auth_redirect
        return render_template('index.html')
    
    # Static pages
    @networth_bp.route('/about')
    def about():
        return render_template('about.html')
    
    # Networth API routes
    networth_bp.add_url_rule('/api/networth/<period>', 'api_networth', 
                             networth_controller.get_networth, methods=['GET'])
    networth_bp.add_url_rule('/api/currencies', 'api_currencies', 
                             networth_controller.get_currencies, methods=['GET'])
    networth_bp.add_url_rule('/api/tags', 'api_tags', 
                             networth_controller.get_tags, methods=['GET'])
    networth_bp.add_url_rule('/api/exchange-rates/<base_currency>', 'api_exchange_rates', 
                             networth_controller.get_exchange_rates, methods=['GET'])
    
    return networth_bp
