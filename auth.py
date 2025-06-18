from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from supabase import create_client
import os
from dotenv import load_dotenv
import json
import jwt

load_dotenv()

auth_bp = APIRouter()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def get_user_id_from_request(request: Request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ')[1]
    try:
        # Supabase JWTs are signed with RS256, but for user_id extraction, you can decode without verification
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded.get('sub')  # 'sub' is the user id in Supabase JWTs
    except Exception as e:
        print("JWT decode error:", e)
        return None

@auth_bp.post('/signup')
async def signup(request: Request):
    try:
        # Check if environment variables are set
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            print("ERROR: Missing Supabase environment variables")
            print(f"SUPABASE_URL: {'SET' if supabase_url else 'MISSING'}")
            print(f"SUPABASE_KEY: {'SET' if supabase_key else 'MISSING'}")
            raise HTTPException(
                status_code=400, 
                detail='Supabase configuration missing. Please set SUPABASE_URL and SUPABASE_KEY environment variables.'
            )
        
        data = await request.json()
        email = data.get('email')
        password = data.get('password')
        username = data.get('username')

        print(f"Attempting to create user: {email}")

        # Create user in Supabase Auth (this uses the built-in auth.users table)
        auth_response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "username": username  # Store username in user metadata
                }
            }
        })

        if auth_response.user:
            print(f"User created successfully: {auth_response.user.id}")
            return JSONResponse(content={
                'success': True,
                'message': 'User created successfully'
            })
        
        print("Failed to create user in Supabase Auth")
        raise HTTPException(status_code=400, detail='Failed to create user')

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"Signup error: {e}")
        raise HTTPException(status_code=400, detail=f'Signup failed: {str(e)}')

@auth_bp.post('/login')
async def login(request: Request):
    try:
        data = await request.json()
        email = data.get('email')
        password = data.get('password')

        print(f"Attempting login for: {email}")

        # Sign in user
        auth_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if auth_response.user:
            print(f"Login successful for user: {auth_response.user.id}")
            # Convert user and session to dicts
            user_dict = auth_response.user.__dict__ if hasattr(auth_response.user, '__dict__') else dict(auth_response.user)
            session_dict = auth_response.session.__dict__ if hasattr(auth_response.session, '__dict__') else dict(auth_response.session)
            return JSONResponse(content={
                'success': True,
                'user': json.loads(auth_response.user.json()),
                'session': json.loads(auth_response.session.json())
            })

        raise HTTPException(status_code=401, detail='Invalid credentials')

    except Exception as e:
        error_msg = str(e)
        print(f"Login error: {error_msg}")
        
        # Provide more specific error messages
        if "Invalid login credentials" in error_msg:
            return JSONResponse(
                status_code=400,
                content={
                    'success': False,
                    'error': 'Invalid email or password. Please check your credentials and try again.'
                }
            )
        elif "Email not confirmed" in error_msg or "not confirmed" in error_msg.lower():
            return JSONResponse(
                status_code=400,
                content={
                    'success': False,
                    'error': 'Please check your email and click the confirmation link before logging in.'
                }
            )
        else:
            return JSONResponse(
                status_code=400,
                content={
                    'success': False,
                    'error': f'Login failed: {error_msg}'
                }
            )

@auth_bp.post('/logout')
async def logout():
    try:
        supabase.auth.sign_out()
        return JSONResponse(content={
            'success': True,
            'message': 'Logged out successfully'
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 