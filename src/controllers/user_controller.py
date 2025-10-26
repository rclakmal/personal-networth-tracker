"""
User controller for handling user-related API endpoints.
"""
from flask import request, jsonify, session, render_template, redirect, url_for, flash
from src.services.user_service import UserService
from src.utils.validation import InputValidator


class UserController:
    """Controller for user-related operations."""
    
    def __init__(self, user_service: UserService):
        """Initialize controller with user service."""
        self.user_service = user_service
    
    def _get_client_info(self):
        """Get client IP address and user agent."""
        # Try to get real IP if behind proxy
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip_address and ',' in ip_address:
            ip_address = ip_address.split(',')[0].strip()
        
        user_agent = request.headers.get('User-Agent', '')
        return ip_address, user_agent
    
    def _regenerate_session(self):
        """Regenerate session to prevent session fixation attacks."""
        # Save data before clearing (but NOT currency - that should come from user's preference)
        user_id = session.get('user_id')
        username = session.get('username')
        
        # Clear and regenerate session
        session.clear()
        
        # Restore data (currency will be set separately from user's preferred_currency)
        if user_id:
            session['user_id'] = user_id
        if username:
            session['username'] = username
        
        session.permanent = True
    
    def login(self):
        """Handle user login (both GET and POST)."""
        if request.method == 'GET':
            return render_template('login.html')
        
        # Handle POST request
        data = request.get_json() if request.is_json else request.form
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # Input validation
        if not username or not password:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Username and password required'}), 400
            else:
                flash('Username and password required', 'error')
                return render_template('login.html')
        
        # Sanitize username
        username = InputValidator.sanitize_string(username, 30)
        if not InputValidator.validate_username(username):
            if request.is_json:
                return jsonify({'success': False, 'error': 'Invalid username format'}), 400
            else:
                flash('Invalid username format', 'error')
                return render_template('login.html')
        
        # Get client information for security logging
        ip_address, user_agent = self._get_client_info()
        
        user = self.user_service.authenticate_user(username, password, ip_address, user_agent)
        if user:
            # Set secure session
            self._regenerate_session()  # Prevent session fixation
            session['user_id'] = user.id
            session['username'] = user.username
            session['currency'] = user.preferred_currency or 'EUR'  # Set user's preferred currency
            session.permanent = True  # Use permanent session for timeout
            
            if request.is_json:
                return jsonify({'success': True, 'user': user.to_dict()})
            else:
                flash('Login successful!', 'success')
                return redirect(url_for('networth.home'))
        else:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Invalid credentials or account locked'}), 401
            else:
                flash('Invalid username or password. Account may be locked after multiple failed attempts.', 'error')
                return render_template('login.html')
    
    def logout(self):
        """Handle user logout."""
        # Clear all session data including currency preference
        session.clear()
        if request.is_json:
            return jsonify({'success': True})
        else:
            flash('You have been logged out', 'info')
            return redirect(url_for('user.login'))
    
    def register(self):
        """Handle user registration (both GET and POST)."""
        if request.method == 'GET':
            return render_template('register.html')
        
        # Handle POST request
        data = request.get_json() if request.is_json else request.form
        
        # Sanitize and validate input
        sanitized_data = InputValidator.sanitize_user_data(data)
        
        username = sanitized_data.get('username', '')
        email = sanitized_data.get('email', '')
        password = data.get('password', '')  # Don't sanitize password
        portfolio_type = data.get('portfolio_type', 'empty')
        
        # Validation
        if not username:
            error_msg = 'Username is required and must be 3-30 characters, alphanumeric only'
            if request.is_json:
                return jsonify({'success': False, 'error': error_msg}), 400
            else:
                flash(error_msg, 'error')
                return render_template('register.html')
        
        if not email:
            error_msg = 'Valid email address is required'
            if request.is_json:
                return jsonify({'success': False, 'error': error_msg}), 400
            else:
                flash(error_msg, 'error')
                return render_template('register.html')
        
        # Password validation
        is_valid_password, password_error = InputValidator.validate_password(password)
        if not is_valid_password:
            if request.is_json:
                return jsonify({'success': False, 'error': password_error}), 400
            else:
                flash(password_error, 'error')
                return render_template('register.html')
        
        result = self.user_service.create_user(username, email, password, portfolio_type=portfolio_type)
        
        if result['success']:
            # Auto-login after successful registration
            user = result.get('user')
            if user:
                self._regenerate_session()  # Prevent session fixation
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['currency'] = user.get('preferred_currency', 'EUR')  # Set initial currency preference
                session.permanent = True
            
            if request.is_json:
                return jsonify(result), 201
            else:
                flash('Registration successful! Welcome to Net Worth Tracker!', 'success')
                return redirect(url_for('networth.home'))
        else:
            if request.is_json:
                return jsonify(result), 400
            else:
                flash(result.get('error', 'Registration failed'), 'error')
                return render_template('register.html')
    
    def profile(self):
        """Handle user profile page (both GET and POST)."""
        user_id = session.get('user_id')
        if not user_id:
            if request.is_json:
                return jsonify({'error': 'Not authenticated'}), 401
            else:
                return redirect(url_for('user.login'))
        
        if request.method == 'GET':
            user = self.user_service.get_user_by_id(user_id)
            if user:
                if request.is_json:
                    return jsonify(user.to_dict())
                else:
                    return render_template('profile.html', user=user.to_dict())
            else:
                if request.is_json:
                    return jsonify({'error': 'User not found'}), 404
                else:
                    flash('User not found', 'error')
                    return redirect(url_for('networth.home'))
        
        # Handle POST request (profile update)
        data = request.get_json() if request.is_json else request.form
        result = self.user_service.update_user(user_id, **data)
        
        if result['success']:
            if request.is_json:
                return jsonify(result)
            else:
                flash('Profile updated successfully', 'success')
                return redirect(url_for('user.profile'))
        else:
            if request.is_json:
                return jsonify(result), 400
            else:
                flash(result.get('error', 'Profile update failed'), 'error')
                return redirect(url_for('user.profile'))
    
    def get_profile(self):
        """Get current user profile (API endpoint)."""
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user = self.user_service.get_user_by_id(user_id)
        if user:
            return jsonify(user.to_dict())
        else:
            return jsonify({'error': 'User not found'}), 404
    
    def update_profile(self):
        """Update current user profile (API endpoint)."""
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        result = self.user_service.update_user(user_id, **data)
        
        if result['success']:
            # Update session currency if it was changed
            if 'preferred_currency' in data:
                session['currency'] = data['preferred_currency'].upper()
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    def update_currency(self):
        """Update user's preferred currency."""
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        currency = data.get('currency', '').upper()
        
        # Validate currency code
        from src.utils.validation import InputValidator
        if not InputValidator.validate_currency(currency):
            return jsonify({'error': 'Invalid currency code'}), 400
            
        # Update user's preferred currency
        result = self.user_service.update_user(user_id, preferred_currency=currency)
        
        if result['success']:
            # Update session currency
            session['currency'] = currency
            return jsonify({'success': True, 'currency': currency})
        else:
            return jsonify(result), 400
    
    def delete_account(self):
        """Delete current user account."""
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        result = self.user_service.delete_user(user_id)
        
        if result['success']:
            session.clear()
            return jsonify(result)
        else:
            return jsonify(result), 400
    
    def change_password(self):
        """Handle password change requests."""
        if request.method == 'GET':
            # Render change password form
            return render_template('change_password.html')
        
        # Handle POST request
        user_id = session.get('user_id')
        if not user_id:
            if request.is_json:
                return jsonify({'error': 'Not authenticated'}), 401
            flash('Please log in to change your password', 'error')
            return redirect(url_for('user.login'))
        
        data = request.get_json() if request.is_json else request.form
        
        # Sanitize and validate input
        current_password = InputValidator.sanitize_string(data.get('current_password', ''))
        new_password = InputValidator.sanitize_string(data.get('new_password', ''))
        confirm_password = InputValidator.sanitize_string(data.get('confirm_password', ''))
        
        # Validate input
        errors = []
        if not current_password:
            errors.append('Current password is required')
        if not new_password:
            errors.append('New password is required')
        if not confirm_password:
            errors.append('Password confirmation is required')
        if new_password != confirm_password:
            errors.append('New passwords do not match')
        
        # Validate password strength
        if new_password:
            is_valid_password, password_error = InputValidator.validate_password(new_password)
            if not is_valid_password:
                errors.append(password_error)
        
        if errors:
            if request.is_json:
                return jsonify({'error': '; '.join(errors)}), 400
            for error in errors:
                flash(error, 'error')
            return render_template('change_password.html')
        
        # Get client information for logging
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        # Change password
        result = self.user_service.change_password(user_id, current_password, new_password, ip_address, user_agent)
        
        if request.is_json:
            if result['success']:
                return jsonify(result)
            else:
                return jsonify(result), 400
        else:
            if result['success']:
                flash('Password changed successfully', 'success')
                return redirect(url_for('networth.home'))
            else:
                flash(result['error'], 'error')
                return render_template('change_password.html')