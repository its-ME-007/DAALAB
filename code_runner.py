import subprocess
import tempfile
import os
import time
import signal
import sys
from typing import Tuple, Optional
import docker
from contextlib import contextmanager

class SafeCodeRunner:
    """
    A safe code runner with fallback mechanisms:
    1. Docker container (preferred - most secure)
    2. Local execution with restrictions (fallback)
    """
    
    def __init__(self):
        self.docker_available = self._check_docker()
        self.image_name = "python:3.13-slim"
        self.timeout_seconds = 10  # Maximum execution time
        
        # Forbidden modules and functions for local execution
        self.forbidden_modules = {
            'os', 'sys', 'subprocess', 'multiprocessing', 'threading',
            'socket', 'urllib', 'requests', 'http', 'ftplib', 'smtplib',
            'sqlite3', 'pickle', 'marshal', 'ctypes', 'mmap', 'fcntl',
            'pwd', 'grp', 'crypt', 'termios', 'tty', 'pty', 'signal',
            'pipes', 'posix', 'nt', 'mac', 'dummy_threading', 'concurrent'
        }
        
        self.forbidden_functions = {
            'eval', 'exec', 'compile', 'input', 'raw_input',
            'open', 'file', 'reload', 'importlib.reload'
        }
    
    def _check_docker(self) -> bool:
        """Check if Docker is available and running"""
        try:
            client = docker.from_env()
            client.ping()
            return True
        except Exception:
            return False
    
    def _check_code_safety(self, code: str) -> Tuple[bool, str]:
        """
        Check if code is safe to run locally
        Returns: (is_safe, error_message)
        """
        # Check for forbidden imports
        lines = code.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                # Extract module name
                if line.startswith('import '):
                    module = line[7:].split()[0].split('.')[0]
                else:  # from ... import
                    module = line[5:].split()[0].split('.')[0]
                
                if module in self.forbidden_modules:
                    return False, f"Forbidden module: {module}"
        
        # Check for forbidden function calls
        for func in self.forbidden_functions:
            if func in code:
                return False, f"Forbidden function: {func}"
        
        # Check for potentially dangerous patterns
        dangerous_patterns = [
            '__import__', 'globals()', 'locals()', 'vars()', 'dir()',
            'getattr', 'setattr', 'delattr', 'hasattr',
            'type', 'isinstance', 'issubclass',
            'super', 'property', 'staticmethod', 'classmethod'
        ]
        
        for pattern in dangerous_patterns:
            if pattern in code:
                return False, f"Dangerous pattern: {pattern}"
        
        return True, ""
    
    def _run_in_docker(self, code: str) -> Tuple[str, float]:
        """Run code in Docker container"""
        try:
            client = docker.from_env()
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Run container
                start_time = time.time()
                container = client.containers.run(
                    self.image_name,
                    command=["python", "-u", "/code/code.py"],
                    volumes={
                        temp_file: {"bind": "/code/code.py", "mode": "ro"}
                    },
                    remove=True,
                    detach=False,
                    timeout=self.timeout_seconds
                )
                
                runtime = time.time() - start_time
                output = container.decode('utf-8') if container else "No output generated"
                
                return output, runtime
                
            finally:
                # Clean up temporary file
                os.unlink(temp_file)
                
        except Exception as e:
            return f"Error: {str(e)}", 0.0
    
    def _run_locally(self, code: str) -> Tuple[str, float]:
        """Run code locally with restrictions"""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Set up process with timeout
                start_time = time.time()
                
                # Run with restricted environment
                env = os.environ.copy()
                env['PYTHONPATH'] = ''  # Clear Python path
                env['PYTHONHOME'] = ''  # Clear Python home
                
                process = subprocess.Popen(
                    [sys.executable, temp_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                    text=True,
                    preexec_fn=os.setsid if hasattr(os, 'setsid') else None
                )
                
                try:
                    stdout, stderr = process.communicate(timeout=self.timeout_seconds)
                    runtime = time.time() - start_time
                    
                    if process.returncode == 0:
                        output = stdout if stdout else "No output generated"
                        if stderr:
                            output += f"\nWarnings: {stderr}"
                    else:
                        output = f"Error: {stderr}" if stderr else "Execution failed"
                    
                    return output, runtime
                    
                except subprocess.TimeoutExpired:
                    # Kill the process group
                    if hasattr(os, 'killpg'):
                        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    else:
                        process.terminate()
                    
                    process.wait()
                    return "Error: Execution timeout exceeded", 0.0
                    
            finally:
                # Clean up temporary file
                os.unlink(temp_file)
                
        except Exception as e:
            return f"Error: {str(e)}", 0.0
    
    def run_code(self, code: str) -> Tuple[str, float]:
        """
        Run Python code with fallback mechanisms
        Returns: (output, runtime)
        """
        if not code.strip():
            return "Error: Code cannot be empty", 0.0
        
        # Try Docker first if available
        if self.docker_available:
            try:
                return self._run_in_docker(code)
            except Exception as e:
                print(f"Docker execution failed: {e}")
                # Fall back to local execution
        
        # Check if code is safe for local execution
        is_safe, error_msg = self._check_code_safety(code)
        if not is_safe:
            return f"Error: {error_msg}. Docker is required for this code.", 0.0
        
        # Run locally with restrictions
        return self._run_locally(code)

# Backward compatibility
class ContainerRunner(SafeCodeRunner):
    """Backward compatibility wrapper"""
    def __init__(self):
        super().__init__() 