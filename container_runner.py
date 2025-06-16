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
            with open(code_path, "w", newline='\n') as f:
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
            output = container.decode('utf-8') if container else "No output generated"
            
            return output, runtime
            
        except Exception as e:
            return f"Error: {str(e)}", 0.0 