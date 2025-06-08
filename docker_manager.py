#!/usr/bin/env python3
"""
Docker Heap Sort Manager
A Python application to build and run a Docker container containing a heap sort program.
"""

import subprocess
import sys
import os
import json
import tempfile
import shutil
from pathlib import Path


class DockerHeapSortManager:
    def __init__(self, image_name="heap-sort-app", container_name="heap-sort-container"):
        self.image_name = image_name
        self.container_name = container_name
        self.project_dir = Path("heap_sort_docker")
        
    def create_heap_sort_program(self):
        """Creates the heap sort Python program"""
        heap_sort_code = '''#!/usr/bin/env python3
"""
Heap Sort Implementation
A complete heap sort algorithm with demonstration.
"""

import sys
import json
import random


def heapify(arr, n, i):
    """
    To heapify subtree rooted at index i.
    n is size of heap
    """
    largest = i  # Initialize largest as root
    left = 2 * i + 1     # left = 2*i + 1
    right = 2 * i + 2    # right = 2*i + 2
    
    # If left child exists and is greater than root
    if left < n and arr[left] > arr[largest]:
        largest = left
    
    # If right child exists and is greater than largest so far
    if right < n and arr[right] > arr[largest]:
        largest = right
    
    # If largest is not root
    if largest != i:
        arr[i], arr[largest] = arr[largest], arr[i]  # swap
        
        # Recursively heapify the affected sub-tree
        heapify(arr, n, largest)


def heap_sort(arr):
    """
    Main function to do heap sort
    """
    n = len(arr)
    
    # Build a maxheap
    # Since last parent will be at ((n//2)-1) we can start at that location
    for i in range(n // 2 - 1, -1, -1):
        heapify(arr, n, i)
    
    # One by one extract elements
    for i in range(n-1, 0, -1):
        arr[i], arr[0] = arr[0], arr[i]  # swap
        heapify(arr, i, 0)
    
    return arr


def generate_random_array(size=10, max_val=100):
    """Generate a random array for testing"""
    return [random.randint(1, max_val) for _ in range(size)]


def main():
    print("🔧 Heap Sort Algorithm Demo")
    print("=" * 40)
    
    # Check if input is provided via command line arguments
    if len(sys.argv) > 1:
        try:
            # Try to parse as JSON array
            if sys.argv[1].startswith('['):
                arr = json.loads(sys.argv[1])
            else:
                # Parse as space-separated integers
                arr = [int(x) for x in sys.argv[1:]]
        except (json.JSONDecodeError, ValueError):
            print("❌ Error: Invalid input format")
            print("Usage: python heap_sort.py [1 2 3 4 5] or python heap_sort.py '[1,2,3,4,5]'")
            return 1
    else:
        # Generate random array if no input provided
        arr = generate_random_array(15, 50)
        print("📊 No input provided. Using random array:")
    
    print(f"Original array: {arr}")
    print(f"Array size: {len(arr)}")
    
    # Create a copy for sorting
    arr_copy = arr.copy()
    
    # Perform heap sort
    print("\\n🔄 Sorting using Heap Sort...")
    sorted_arr = heap_sort(arr_copy)
    
    print(f"Sorted array:   {sorted_arr}")
    
    # Verify the sort worked correctly
    is_sorted = all(sorted_arr[i] <= sorted_arr[i+1] for i in range(len(sorted_arr)-1))
    
    if is_sorted:
        print("✅ Array successfully sorted!")
    else:
        print("❌ Error in sorting!")
        return 1
    
    print("\\n📈 Heap Sort Complexity:")
    print("Time Complexity: O(n log n)")
    print("Space Complexity: O(1)")
    
    return 0


if __name__ == "__main__":
    exit(main())
'''
        return heap_sort_code
    
    def create_dockerfile(self):
        """Creates the Dockerfile"""
        dockerfile_content = '''FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy the heap sort program
COPY heap_sort.py .

# Make it executable
RUN chmod +x heap_sort.py

# Set the default command
CMD ["python", "heap_sort.py"]
'''
        return dockerfile_content
    
    def create_requirements_file(self):
        """Creates requirements.txt (empty for this simple program)"""
        return "# No external dependencies required for heap sort\\n"
    
    def setup_project_directory(self):
        """Sets up the project directory with all necessary files"""
        print(f"📁 Setting up project directory: {self.project_dir}")
        
        # Create project directory
        self.project_dir.mkdir(exist_ok=True)
        
        # Create heap sort program
        heap_sort_file = self.project_dir / "heap_sort.py"
        heap_sort_file.write_text(self.create_heap_sort_program())
        
        # Create Dockerfile
        dockerfile = self.project_dir / "Dockerfile"
        dockerfile.write_text(self.create_dockerfile())
        
        # Create requirements.txt
        requirements = self.project_dir / "requirements.txt"
        requirements.write_text(self.create_requirements_file())
        
        print("✅ Project files created successfully")
    
    def check_docker_installed(self):
        """Check if Docker is installed and running"""
        try:
            result = subprocess.run(["docker", "--version"], 
                                  capture_output=True, text=True, check=True)
            print(f"🐳 Docker found: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Docker is not installed or not running")
            print("Please install Docker: https://docs.docker.com/get-docker/")
            return False
    
    def build_docker_image(self):
        """Build the Docker image"""
        print(f"🔨 Building Docker image: {self.image_name}")
        
        try:
            cmd = ["docker", "build", "-t", self.image_name, str(self.project_dir)]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print("✅ Docker image built successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to build Docker image:")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")
            return False
    
    def run_container(self, input_array=None, interactive=False):
        """Run the Docker container"""
        print(f"🚀 Running Docker container: {self.container_name}")
        
        # Remove existing container if it exists
        self.cleanup_container()
        
        cmd = ["docker", "run", "--name", self.container_name]
        
        if interactive:
            cmd.extend(["-it"])
        
        cmd.append(self.image_name)
        
        # Add input array if provided
        if input_array:
            if isinstance(input_array, list):
                cmd.extend([str(x) for x in input_array])
            else:
                cmd.append(str(input_array))
        
        try:
            if interactive:
                # For interactive mode, don't capture output
                subprocess.run(cmd, check=True)
            else:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                print("📋 Container Output:")
                print("-" * 40)
                print(result.stdout)
                if result.stderr:
                    print("stderr:", result.stderr)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to run container:")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")
            return False
    
    def cleanup_container(self):
        """Remove the container if it exists"""
        try:
            subprocess.run(["docker", "rm", "-f", self.container_name], 
                         capture_output=True, check=True)
        except subprocess.CalledProcessError:
            # Container doesn't exist, which is fine
            pass
    
    def cleanup_image(self):
        """Remove the Docker image"""
        try:
            subprocess.run(["docker", "rmi", self.image_name], 
                         capture_output=True, check=True)
            print(f"✅ Removed Docker image: {self.image_name}")
        except subprocess.CalledProcessError:
            print(f"⚠️  Could not remove image: {self.image_name}")
    
    def list_docker_images(self):
        """List Docker images"""
        try:
            result = subprocess.run(["docker", "images"], 
                                  capture_output=True, text=True, check=True)
            print("🐳 Docker Images:")
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to list images: {e.stderr}")
    
    def run_demo(self):
        """Run a complete demonstration"""
        print("🎯 Starting Heap Sort Docker Demo")
        print("=" * 50)
        
        # Check Docker
        if not self.check_docker_installed():
            return False
        
        # Setup project
        self.setup_project_directory()
        
        # Build image
        if not self.build_docker_image():
            return False
        
        # Run with different test cases
        test_cases = [
            None,  # Random array
            [64, 34, 25, 12, 22, 11, 90],
            [5, 2, 8, 1, 9],
            [1],  # Single element
            [3, 3, 3, 3],  # Duplicates
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\\n🧪 Test Case {i}:")
            if test_case is None:
                print("Running with random array...")
            else:
                print(f"Input: {test_case}")
            
            if not self.run_container(test_case):
                return False
        
        print("\\n🎉 Demo completed successfully!")
        return True


def main():
    """Main function with CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Docker Heap Sort Manager")
    parser.add_argument("--demo", action="store_true", help="Run complete demo")
    parser.add_argument("--build", action="store_true", help="Build Docker image only")
    parser.add_argument("--run", nargs="*", help="Run container with optional array input")
    parser.add_argument("--cleanup", action="store_true", help="Clean up Docker resources")
    parser.add_argument("--list-images", action="store_true", help="List Docker images")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    
    args = parser.parse_args()
    
    manager = DockerHeapSortManager()
    
    if args.demo:
        success = manager.run_demo()
        sys.exit(0 if success else 1)
    
    elif args.build:
        manager.setup_project_directory()
        if manager.check_docker_installed():
            success = manager.build_docker_image()
            sys.exit(0 if success else 1)
    
    elif args.run is not None:
        if manager.check_docker_installed():
            input_array = None
            if args.run:
                try:
                    input_array = [int(x) for x in args.run]
                except ValueError:
                    print("❌ Error: All inputs must be integers")
                    sys.exit(1)
            
            success = manager.run_container(input_array, args.interactive)
            sys.exit(0 if success else 1)
    
    elif args.cleanup:
        manager.cleanup_container()
        manager.cleanup_image()
        if manager.project_dir.exists():
            shutil.rmtree(manager.project_dir)
            print(f"✅ Removed project directory: {manager.project_dir}")
    
    elif args.list_images:
        manager.list_docker_images()
    
    else:
        print("🔧 Docker Heap Sort Manager")
        print("Usage examples:")
        print("  python docker_manager.py --demo                    # Run complete demo")
        print("  python docker_manager.py --build                   # Build Docker image")
        print("  python docker_manager.py --run                     # Run with random array")
        print("  python docker_manager.py --run 5 2 8 1 9          # Run with specific array")
        print("  python docker_manager.py --run --interactive       # Run interactively")
        print("  python docker_manager.py --cleanup                 # Clean up resources")
        print("  python docker_manager.py --list-images             # List Docker images")


if __name__ == "__main__":
    main()