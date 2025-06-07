from flask import Blueprint, request, jsonify
from supabase import create_client
import os
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from dotenv import load_dotenv
import jwt

load_dotenv()


visualization_bp = Blueprint('visualization', __name__)
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def get_user_id_from_request(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ')[1]
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded.get('sub')
    except Exception as e:
        print("JWT decode error:", e)
        return None

@visualization_bp.route('/runtimes', methods=['GET'])
def get_runtimes():
    try:
        algorithm_name = request.args.get('algorithm_name')
        user_id = get_user_id_from_request(request)
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        # Get algorithm ID
        algorithm = supabase.table('algorithms')\
            .select('id')\
            .eq('name', algorithm_name)\
            .eq('user_id', user_id)\
            .execute()
        
        if not algorithm.data:
            return jsonify({'success': False, 'error': 'Algorithm not found'}), 404
            
        algorithm_id = algorithm.data[0]['id']
        
        # Get runtime logs
        runtimes = supabase.table('runtime_logs')\
            .select('*')\
            .eq('algorithm_id', algorithm_id)\
            .order('created_at')\
            .execute()
            
        return jsonify({
            'success': True,
            'runtimes': runtimes.data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@visualization_bp.route('/plot', methods=['GET'])
def generate_plot():
    try:
        algorithm_name = request.args.get('algorithm_name')
        user_id = get_user_id_from_request(request)
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401

        # Get runtime data
        response = get_runtimes()
        if not response.json['success']:
            return response

        runtimes = response.json['runtimes']
        
        # Create plot
        plt.figure(figsize=(10, 6))
        df = pd.DataFrame(runtimes)
        
        plt.plot(df['created_at'], df['runtime_ms'], marker='o')
        plt.title(f'Runtime Performance: {algorithm_name}')
        plt.xlabel('Time')
        plt.ylabel('Runtime (ms)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Convert plot to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()
        
        # Encode to base64
        encoded = base64.b64encode(image_png).decode('utf-8')
        
        return jsonify({
            'success': True,
            'plot': f'data:image/png;base64,{encoded}'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@visualization_bp.route('/executions', methods=['GET'])
def get_executions():
    try:
        user_id = get_user_id_from_request(request)
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401

        algorithm_id = request.args.get('algorithm_id')
        if not algorithm_id:
            return jsonify({
                'success': False,
                'error': 'Algorithm ID is required'
            }), 400

        # Verify algorithm belongs to user
        algorithm = supabase.table('algorithms')\
            .select('id')\
            .eq('id', algorithm_id)\
            .eq('user_id', user_id)\
            .execute()

        if not algorithm.data:
            return jsonify({
                'success': False,
                'error': 'Algorithm not found or access denied'
            }), 404

        # Get execution history
        executions = supabase.table('execution_logs')\
            .select('*')\
            .eq('algorithm_id', algorithm_id)\
            .order('created_at', desc=True)\
            .limit(10)\
            .execute()

        return jsonify({
            'success': True,
            'executions': executions.data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400 