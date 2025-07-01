from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, CustomerProfile, ProviderProfile
from datetime import datetime
import re

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'first_name', 'last_name', 'user_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate email format
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate password
        is_valid, message = validate_password(data['password'])
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Validate user type
        if data['user_type'] not in ['customer', 'provider']:
            return jsonify({'error': 'User type must be either customer or provider'}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({'error': 'User with this email already exists'}), 409
        
        # Create new user
        user = User(
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data.get('phone'),
            user_type=data['user_type'],
            street_address=data.get('street_address'),
            city=data.get('city'),
            state=data.get('state'),
            postcode=data.get('postcode'),
            bio=data.get('bio')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.flush()  # Get user ID
        
        # Create profile based on user type
        if data['user_type'] == 'customer':
            profile = CustomerProfile(
                user_id=user.id,
                preferred_contact_method=data.get('preferred_contact_method', 'email')
            )
        else:  # provider
            profile = ProviderProfile(
                user_id=user.id,
                business_name=data.get('business_name'),
                abn=data.get('abn'),
                license_number=data.get('license_number'),
                years_experience=data.get('years_experience'),
                hourly_rate=data.get('hourly_rate'),
                service_radius=data.get('service_radius', 25)
            )
        
        db.session.add(profile)
        db.session.commit()
        
        # Set session
        session['user_id'] = user.id
        session['user_type'] = user.user_type
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Find user
        user = User.query.filter_by(email=data['email']).first()
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Check if user is active
        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 401
        
        # Set session
        session['user_id'] = user.id
        session['user_type'] = user.user_type
        
        # Get profile data
        profile_data = None
        if user.user_type == 'customer' and user.customer_profile:
            profile_data = user.customer_profile.to_dict()
        elif user.user_type == 'provider' and user.provider_profile:
            profile_data = user.provider_profile.to_dict()
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'profile': profile_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user"""
    session.clear()
    return jsonify({'message': 'Logout successful'}), 200

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """Get current user information"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user = User.query.get(user_id)
        if not user:
            session.clear()
            return jsonify({'error': 'User not found'}), 404
        
        # Get profile data
        profile_data = None
        if user.user_type == 'customer' and user.customer_profile:
            profile_data = user.customer_profile.to_dict()
        elif user.user_type == 'provider' and user.provider_profile:
            profile_data = user.provider_profile.to_dict()
        
        return jsonify({
            'user': user.to_dict(),
            'profile': profile_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    """Change user password"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({'error': 'Current password and new password are required'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Verify current password
        if not user.check_password(data['current_password']):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Validate new password
        is_valid, message = validate_password(data['new_password'])
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Update password
        user.set_password(data['new_password'])
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

