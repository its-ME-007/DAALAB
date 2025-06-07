from flask import Blueprint, request, jsonify
from supabase import create_client
import os
from dotenv import load_dotenv
import json
import jwt

load_dotenv()

auth_bp = Blueprint('auth', __name__)
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def get_user_id_from_request(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ')[1]
    try:
        # Supabase JWTs are signed with RS256, bu\t for user_id extraction, you can decode without verification
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded.get('sub')  # 'sub' is the user id in Supabase JWTs
    except Exception as e:
        print("JWT decode error:", e)
        return None

@auth_bp.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        username = data.get('username')

        # Create user in Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })

        if auth_response.user:
            # Create user profile
            supabase.table('user_profiles').insert({
                'id': auth_response.user.id,
                'username': username
            }).execute()

            return jsonify({
                'success': True,
                'message': 'User created successfully'
            })
        
        return jsonify({
            'success': False,
            'error': 'Failed to create user'
        }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')

        # Sign in user
        auth_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if auth_response.user:
            # Convert user and session to dicts
            user_dict = auth_response.user.__dict__ if hasattr(auth_response.user, '__dict__') else dict(auth_response.user)
            session_dict = auth_response.session.__dict__ if hasattr(auth_response.session, '__dict__') else dict(auth_response.session)
            return jsonify({
                'success': True,
                'user': json.loads(auth_response.user.json()),
                'session': json.loads(auth_response.session.json())
            })

        return jsonify({
            'success': False,
            'error': 'Invalid credentials'
        }), 401

    except Exception as e:
        print("Login error:", e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@auth_bp.route('/logout', methods=['POST'])
def logout():
    try:
        supabase.auth.sign_out()
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400 