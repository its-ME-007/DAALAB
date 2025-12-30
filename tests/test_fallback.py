#!/usr/bin/env python3
"""
Test script to demonstrate the fallback mechanism
"""

from code_runner import SafeCodeRunner

def test_safe_code():
    """Test safe code that can run locally"""
    runner = SafeCodeRunner()
    
    safe_code = """
# Safe code example
print("Hello, World!")
x = 10
y = 20
print(f"Sum: {x + y}")

# List operations
numbers = [1, 2, 3, 4, 5]
squares = [n**2 for n in numbers]
print(f"Squares: {squares}")

# Function definition
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

print(f"Factorial of 5: {factorial(5)}")
"""
    
    print("Testing safe code...")
    output, runtime = runner.run_code(safe_code)
    print(f"Output: {output}")
    print(f"Runtime: {runtime:.6f} seconds")
    print(f"Docker available: {runner.docker_available}")
    print("-" * 50)

def test_unsafe_code():
    """Test unsafe code that requires Docker"""
    runner = SafeCodeRunner()
    
    unsafe_code = """
import os
print("This should be blocked locally")
print(f"Current directory: {os.getcwd()}")
"""
    
    print("Testing unsafe code...")
    output, runtime = runner.run_code(unsafe_code)
    print(f"Output: {output}")
    print(f"Runtime: {runtime:.6f} seconds")
    print(f"Docker available: {runner.docker_available}")
    print("-" * 50)

def test_docker_preference():
    """Test that Docker is preferred when available"""
    runner = SafeCodeRunner()
    
    code = """
import sys
print(f"Python version: {sys.version}")
print("Running in container or local environment")
"""
    
    print("Testing Docker preference...")
    output, runtime = runner.run_code(code)
    print(f"Output: {output}")
    print(f"Runtime: {runtime:.6f} seconds")
    print(f"Docker available: {runner.docker_available}")
    print("-" * 50)

if __name__ == "__main__":
    print("Testing Code Runner Fallback Mechanism")
    print("=" * 50)
    
    test_safe_code()
    test_unsafe_code()
    test_docker_preference()
    
    print("Test completed!") 