import os
from dotenv import load_dotenv
import platform
import json
import docker
import time
import uuid
import tempfile
import subprocess

# Load .env from the project root
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
print("Loading .env from:", dotenv_path)
load_dotenv(dotenv_path=dotenv_path, override=True)

print("SUPABASE_URL:", os.getenv("SUPABASE_URL"))
print("SUPABASE_KEY:", os.getenv("SUPABASE_KEY"))

from flask import Blueprint, request, jsonify
from supabase import create_client
import jwt

algorithms_bp = Blueprint('algorithms', __name__)
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Initialize Docker client with error handling
try:
    docker_client = docker.from_env()
    docker_available = True
    print("Docker client initialized successfully")
except Exception as e:
    print(f"Docker not available: {e}")
    docker_available = False

def execute_code_docker(code, language):
    """Execute code using Docker containers"""
    try:
        # Create a temporary directory for this execution
        temp_dir = tempfile.mkdtemp()
        
        # Create a temporary file for the code
        extension = '.cpp' if language == 'cpp' else '.c'
        filename = f"code_{uuid.uuid4()}{extension}"
        filepath = os.path.join(temp_dir, filename)
        output_path = os.path.join(temp_dir, "a.out")
        
        with open(filepath, 'w') as f:
            f.write(code)
        
        # Prepare compiler command
        compiler = 'g++' if language == 'cpp' else 'gcc'
        compile_cmd = f"{compiler} /tmp/{filename} -o /tmp/a.out"
        
        # Run GCC container to compile
        try:
            compile_result = docker_client.containers.run(
                'gcc:latest',
                compile_cmd,
                volumes={temp_dir: {'bind': '/tmp', 'mode': 'rw'}},
                remove=True,
                mem_limit='256m',
                timeout=30,
                network_disabled=True,
                stderr=True,
                stdout=True
            )
            print("Compilation successful")
        except docker.errors.ContainerError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            return {
                'success': False,
                'error': f"Compilation error: {error_msg}"
            }
        
        # Check if compilation produced an executable
        if not os.path.exists(output_path):
            return {
                'success': False,
                'error': "Compilation failed: No executable produced"
            }
        
        # Run the compiled program
        start_time = time.time()
        try:
            result = docker_client.containers.run(
                'gcc:latest',
                '/tmp/a.out',
                volumes={temp_dir: {'bind': '/tmp', 'mode': 'ro'}},
                remove=True,
                mem_limit='256m',
                timeout=10,
                network_disabled=True,
                stderr=True,
                stdout=True
            )
            end_time = time.time()
            
            output = result.decode('utf-8') if result else ""
            
        except docker.errors.ContainerError as e:
            end_time = time.time()
            error_msg = e.stderr.decode() if e.stderr else str(e)
            return {
                'success': False,
                'error': f"Runtime error: {error_msg}"
            }
        
        # Clean up
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except Exception as cleanup_error:
            print(f"Cleanup warning: {cleanup_error}")
        
        return {
            'success': True,
            'output': output.strip(),
            'runtime_ms': (end_time - start_time) * 1000
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Execution error: {str(e)}'
        }

def execute_code_local(code, language):
    """Fallback: Execute code using local system (less secure but functional)"""
    try:
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        
        # Create temporary file for code
        extension = '.cpp' if language == 'cpp' else '.c'
        code_file = os.path.join(temp_dir, f"code{extension}")
        exe_file = os.path.join(temp_dir, "a.out")
        
        with open(code_file, 'w') as f:
            f.write(code)
        
        # Compile
        compiler = 'g++' if language == 'cpp' else 'gcc'
        compile_process = subprocess.run(
            [compiler, code_file, '-o', exe_file],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if compile_process.returncode != 0:
            return {
                'success': False,
                'error': f"Compilation error: {compile_process.stderr}"
            }
        
        # Execute
        start_time = time.time()
        exec_process = subprocess.run(
            [exe_file],
            capture_output=True,
            text=True,
            timeout=5
        )
        end_time = time.time()
        
        # Clean up
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except:
            pass
        
        if exec_process.returncode != 0:
            return {
                'success': False,
                'error': f"Runtime error: {exec_process.stderr}"
            }
        
        return {
            'success': True,
            'output': exec_process.stdout.strip(),
            'runtime_ms': (end_time - start_time) * 1000
        }
        
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Execution timeout (5 seconds)'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Execution error: {str(e)}'
        }

def execute_code(code, language):
    """Main execution function with fallback"""
    if docker_available:
        print("Attempting Docker execution...")
        result = execute_code_docker(code, language)
        if result['success']:
            return result
        else:
            print(f"Docker execution failed: {result['error']}")
    
    print("Falling back to local execution...")
    return execute_code_local(code, language)

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

@algorithms_bp.route('/run', methods=['POST'])
def run_algorithm():
    try:
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
            
        code = data.get('code')
        algorithm_name = data.get('name')
        language = data.get('language', 'c')
        user_id = get_user_id_from_request(request)

        # Validation
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401

        if not code or not code.strip():
            return jsonify({
                'success': False,
                'error': 'No code provided'
            }), 400

        if not algorithm_name or not algorithm_name.strip():
            return jsonify({
                'success': False,
                'error': 'No algorithm name provided'
            }), 400
            
        if language not in ['c', 'cpp']:
            return jsonify({
                'success': False,
                'error': 'Invalid language. Must be "c" or "cpp"'
            }), 400

        # Execute code
        print(f"Executing {language} code for algorithm: {algorithm_name}")
        result = execute_code(code, language)
        
        if not result['success']:
            return jsonify(result), 400

        try:
            # Store in database
            algorithm_query = supabase.table('algorithms').select('id').eq('name', algorithm_name).eq('user_id', user_id).execute()
            
            if not algorithm_query.data:
                # Create new algorithm entry
                algorithm_insert = supabase.table('algorithms').insert({
                    'name': algorithm_name,
                    'description': f'Algorithm: {algorithm_name}',
                    'user_id': user_id,
                    'language': language
                }).execute()
                
                if algorithm_insert.data:
                    algorithm_id = algorithm_insert.data[0]['id']
                else:
                    print("Failed to create algorithm entry")
                    algorithm_id = None
            else:
                algorithm_id = algorithm_query.data[0]['id']

            # Log execution if we have an algorithm_id
            if algorithm_id:
                execution_log = supabase.table('execution_logs').insert({
                    'algorithm_id': algorithm_id,
                    'runtime_ms': result['runtime_ms'],
                    'output': result['output'][:1000]  # Limit output length
                }).execute()
                
                if not execution_log.data:
                    print("Failed to log execution")
            
        except Exception as db_error:
            print(f"Database error: {db_error}")
            # Continue execution even if database logging fails

        return jsonify({
            'success': True,
            'runtime_ms': result['runtime_ms'],
            'output': result['output'],
            'algorithm_id': algorithm_id
        })

    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500

@algorithms_bp.route('/list', methods=['GET'])
def list_algorithms():
    try:
        user_id = get_user_id_from_request(request)
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401

        algorithms = supabase.table('algorithms')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .execute()

        return jsonify({
            'success': True,
            'algorithms': algorithms.data or []
        })

    except Exception as e:
        print(f"Error listing algorithms: {e}")
        return jsonify({
            'success': False,
            'error': f'Error retrieving algorithms: {str(e)}'
        }), 500

@algorithms_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'docker_available': docker_available,
        'message': 'Algorithms service is running'
    })