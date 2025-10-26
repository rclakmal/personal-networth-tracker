"""
Account routes blueprint for account management and operations.
"""
from flask import Blueprint

def create_account_blueprint(account_controller, limiter):
    """Create and configure account routes blueprint."""
    account_bp = Blueprint('account', __name__, url_prefix='/api')
    
    # Account CRUD routes - both routes go to same handler
    account_bp.add_url_rule('/accounts', 'get_accounts_default', 
                           account_controller.get_accounts, methods=['GET'])
    account_bp.add_url_rule('/accounts/<currency>', 'get_accounts_currency', 
                           account_controller.get_accounts, methods=['GET'])
    account_bp.add_url_rule('/accounts/<int:account_id>', 'get_account', 
                           account_controller.get_account, methods=['GET'])
    account_bp.add_url_rule('/accounts', 'create_account', 
                           limiter.limit("20 per minute")(account_controller.create_account), 
                           methods=['POST'])
    account_bp.add_url_rule('/accounts/<int:account_id>', 'update_account', 
                           account_controller.update_account, methods=['PUT'])
    account_bp.add_url_rule('/accounts/<int:account_id>/field', 'update_account_field', 
                           account_controller.update_account_field, methods=['PATCH'])
    account_bp.add_url_rule('/accounts/<int:account_id>', 'delete_account', 
                           limiter.limit("10 per minute")(account_controller.delete_account), 
                           methods=['DELETE'])
    
    # Account operations routes
    account_bp.add_url_rule('/accounts/<int:account_id>/archive', 'archive_account', 
                           account_controller.archive_account, methods=['POST'])
    account_bp.add_url_rule('/accounts/<int:account_id>/restore', 'restore_account', 
                           account_controller.unarchive_account, methods=['POST'])
    
    # Account history route
    account_bp.add_url_rule('/asset/<int:account_id>/history', 'get_asset_history',
                           account_controller.get_account_history, methods=['GET'])
    
    return account_bp
