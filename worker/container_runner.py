import docker
import time
import os
from typing import Tuple

def safe_decode(data) -> str:
    """Safely decode bytes to UTF-8 string with error handling."""
    if isinstance(data, bytes):
        return data.decode('utf-8', errors='replace')
    return str(data)


class ContainerRunner:
    def __init__(self):
        self.client = docker.from_env()
        self.image_name = "python:3.13-slim"

    def run_code(self, code: str) -> Tuple[str, float]:
        """Run Python code in a container and return the output and runtime."""
        code_path = None
        try:
            current_dir = os.path.abspath(os.getcwd())
            code_path = os.path.join(current_dir, "user_code.py")
            
            # Write with explicit UTF-8 encoding
            with open(code_path, "w", encoding='utf-8', newline='\n') as f:
                f.write(code)
            
            start_time = time.time()
            
            result = self.client.containers.run(
                self.image_name,
                f"python /code/user_code.py",
                volumes={current_dir: {'bind': '/code', 'mode': 'ro'}},
                remove=True,
                mem_limit="512m",
                cpu_period=100000,
                cpu_quota=50000,
                network_disabled=True,
                stderr=True,
                stdout=True
            )
            
            runtime = time.time() - start_time
            output = result.decode('utf-8', errors='replace') if result else "No output generated"
            # Sanitize output to ASCII-safe characters for Windows
            output = output.encode('ascii', errors='replace').decode('ascii')
            
            return output, runtime
            
        except docker.errors.ContainerError as e:
            error_msg = f"Runtime Error: {e.stderr.decode('utf-8', errors='replace')}"
            return error_msg.encode('ascii', errors='replace').decode('ascii'), 0.0
            
        except Exception as e:
            error_msg = str(e).encode('ascii', errors='replace').decode('ascii')
            return f"Error: {error_msg}", 0.0
            
        finally:
            if code_path and os.path.exists(code_path):
                try:
                    os.remove(code_path)
                except:
                    pass


class CppContainerRunner:
    def __init__(self):
        self.client = docker.from_env()
        self.image_name = "gcc:latest"

    def run_code(self, code: str) -> Tuple[str, float]:
        """Compile and run C++ code in a container and return the output and runtime."""
        code_path = None
        program_path = None
        try:
            current_dir = os.path.abspath(os.getcwd())
            code_path = os.path.join(current_dir, "user.cpp")
            program_path = os.path.join(current_dir, "program")
            
            # Write with explicit UTF-8 encoding
            with open(code_path, "w", encoding='utf-8', newline='\n') as f:
                f.write(code)
            
            start_time = time.time()
            
            result = self.client.containers.run(
                self.image_name,
                'bash -c "g++ -std=c++17 -o /code/program /code/user.cpp && /code/program"',
                volumes={current_dir: {'bind': '/code', 'mode': 'rw'}},
                remove=True,
                mem_limit="512m",
                cpu_period=100000,
                cpu_quota=50000,
                network_disabled=True,
                stderr=True,
                stdout=True
            )
            
            runtime = time.time() - start_time
            output = result.decode('utf-8', errors='replace') if result else "No output generated"
            # Sanitize output to ASCII-safe characters for Windows
            output = output.encode('ascii', errors='replace').decode('ascii')
            
            return output, runtime
            
        except docker.errors.ContainerError as e:
            error_msg = f"Compilation/Runtime Error: {e.stderr.decode('utf-8', errors='replace')}"
            return error_msg.encode('ascii', errors='replace').decode('ascii'), 0.0
            
        except Exception as e:
            error_msg = str(e).encode('ascii', errors='replace').decode('ascii')
            return f"Error: {error_msg}", 0.0
            
        finally:
            for f in [code_path, program_path]:
                if f and os.path.exists(f):
                    try:
                        os.remove(f)
                    except:
                        pass

    def compile_only(self, code: str) -> Tuple[str, bool]:
        """Compile C++ code without running it, return compilation output and success status."""
        code_path = None
        try:
            current_dir = os.path.abspath(os.getcwd())
            code_path = os.path.join(current_dir, "user.cpp")
            
            # Write with explicit UTF-8 encoding
            with open(code_path, "w", encoding='utf-8', newline='\n') as f:
                f.write(code)
            
            container = self.client.containers.run(
                self.image_name,
                command=["g++", "-std=c++17", "-o", "/code/program", "/code/user.cpp"],
                volumes={
                    code_path: {"bind": "/code/user.cpp", "mode": "rw"}
                },
                working_dir="/code",
                remove=True
            )
            
            return "Compilation successful", True
            
        except Exception as e:
            error_msg = str(e).encode('ascii', errors='replace').decode('ascii')
            return f"Compilation error: {error_msg}", False
            
        finally:
            if code_path and os.path.exists(code_path):
                try:
                    os.remove(code_path)
                except:
                    pass 