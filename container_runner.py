import docker
import time
import os
from typing import Tuple

class ContainerRunner:
    def __init__(self):
        self.client = docker.from_env()
        self.image_name = "python:3.13-slim"

    def run_code(self, code: str) -> Tuple[str, float]:
        """
        Run Python code in a container and return the output and runtime.
        """
        try:
            # Get absolute path for code file
            current_dir = os.path.abspath(os.getcwd())
            code_path = os.path.join(current_dir, "code.py")
            
            # Write code to file
            with open(code_path, "w", encoding='utf-8', newline='\n') as f:
                f.write(code)
            
            # Run container
            start_time = time.time()
            container = self.client.containers.run(
                self.image_name,
                command=["python", "-u", "/code/code.py"],
                volumes={
                    code_path: {"bind": "/code/code.py", "mode": "rw"}
                },
                remove=True
            )
            
            runtime = time.time() - start_time
            output = container.decode('utf-8', errors='replace') if container else "No output generated"
            # Sanitize output to ASCII-safe characters for Windows
            output = output.encode('ascii', errors='replace').decode('ascii')
            
            return output, runtime
            
        except Exception as e:
            error_msg = str(e).encode('ascii', errors='replace').decode('ascii')
            return f"Error: {error_msg}", 0.0


class CppContainerRunner:
    def __init__(self):
        self.client = docker.from_env()
        self.image_name = "gcc:latest"  # Use official GCC image

    def run_code(self, code: str) -> Tuple[str, float]:
        """
        Compile and run C++ code in a container and return the output and runtime.
        """
        try:
            # Get absolute path for code file
            current_dir = os.path.abspath(os.getcwd())
            code_path = os.path.join(current_dir, "user.cpp")
            
            # Write code to file
            with open(code_path, "w", encoding='utf-8', newline='\n') as f:
                f.write(code)
            
            # Run container with compilation and execution
            start_time = time.time()
            container = self.client.containers.run(
                self.image_name,
                command=[
                    "sh", "-c", 
                    "g++ -std=c++17 -o /code/program /code/user.cpp && /code/program"
                ],
                volumes={
                    code_path: {"bind": "/code/user.cpp", "mode": "rw"}
                },
                working_dir="/code",
                remove=True
            )
            
            runtime = time.time() - start_time
            output = container.decode('utf-8', errors='replace') if container else "No output generated"
            # Sanitize output to ASCII-safe characters for Windows
            output = output.encode('ascii', errors='replace').decode('ascii')
            
            return output, runtime
            
        except Exception as e:
            error_msg = str(e).encode('ascii', errors='replace').decode('ascii')
            return f"Error: {error_msg}", 0.0

    def compile_only(self, code: str) -> Tuple[str, bool]:
        """
        Compile C++ code without running it, return compilation output and success status.
        """
        try:
            # Get absolute path for code file
            current_dir = os.path.abspath(os.getcwd())
            code_path = os.path.join(current_dir, "user.cpp")
            
            # Write code to file
            with open(code_path, "w", encoding='utf-8', newline='\n') as f:
                f.write(code)
            
            # Run container with compilation only
            container = self.client.containers.run(
                self.image_name,
                command=["g++", "-std=c++17", "-o", "/code/program", "/code/user.cpp"],
                volumes={
                    code_path: {"bind": "/code/user.cpp", "mode": "rw"}
                },
                working_dir="/code",
                remove=True
            )
            
            # If we get here, compilation was successful
            return "Compilation successful", True
            
        except Exception as e:
            error_msg = str(e).encode('ascii', errors='replace').decode('ascii')
            return f"Compilation error: {error_msg}", False 