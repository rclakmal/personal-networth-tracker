"""
Networth controller for handling networth and chart-related API endpoints.
Controller layer: HTTP handling only - validate auth, call service, return JSON.
"""
from flask import request, jsonify, session
from src.services.networth_service import NetworthService


class NetworthController:
    """Controller for networth-related operations."""
    
    def __init__(self, networth_service: NetworthService):
        """Initialize controller with networth service."""
        self.networth_service = networth_service
    
    def _get_current_user_id(self):
        """Get current user ID from session."""
        return session.get('user_id')
    
    def _require_authentication(self):
        """Check if user is authenticated."""
        user_id = self._get_current_user_id()
        if not user_id:
            return None, jsonify({'error': 'Authentication required'}), 401
        return user_id, None, None
    
    def get_networth(self, period):
        """Get networth data for a specific period."""
        user_id, error_response, status_code = self._require_authentication()
        if error_response:
            return error_response, status_code
        
        target_currency = request.args.get('currency', session.get('currency', 'EUR'))
        
        # Call service to calculate networth
        result = self.networth_service.calculate_networth_for_period(user_id, period, target_currency)
        
        # Check for errors
        if 'error' in result:
            if result['error'] == 'Invalid period':
                return jsonify({'error': 'Invalid period'}), 400
            else:
                return jsonify({'error': result['error']}), 503
        
        return jsonify(result)
    
    def get_tags(self):
        """Get all unique tags used by the current user."""
        user_id, error_response, status_code = self._require_authentication()
        if error_response:
            return error_response, status_code
        
        tags = self.networth_service.get_all_tags()
        return jsonify({'tags': tags})
    
    def get_currencies(self):
        """Get list of available currencies from database or exchange rate API."""
        result = self.networth_service.get_currency_list()
        
        if 'error' in result:
            return jsonify(result), 503
        
        return jsonify(result)
    
    def get_exchange_rates(self, base_currency):
        """Get exchange rates for a base currency."""
        result = self.networth_service.get_exchange_rates_for_base(base_currency)
        
        if 'error' in result:
            if 'not found' in result['error']:
                return jsonify(result), 400
            else:
                return jsonify(result), 503
        
        return jsonify(result)