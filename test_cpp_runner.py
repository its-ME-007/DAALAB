#!/usr/bin/env python3
"""
Test script for the C++ Container Runner
"""

from container_runner import CppContainerRunner

def test_cpp_runner():
    """Test the C++ container runner with a simple C++ program"""
    
    # Simple C++ code to test
    cpp_code = """
#include <iostream>
#include <vector>
#include <chrono>

int main() {
    std::cout << "Hello from C++!" << std::endl;
    
    // Simple algorithm test
    std::vector<int> numbers = {1, 2, 3, 4, 5};
    int sum = 0;
    
    for (int num : numbers) {
        sum += num;
    }
    
    std::cout << "Sum of numbers: " << sum << std::endl;
    
    return 0;
}
"""
    
    print("Testing C++ Container Runner...")
    print("=" * 50)
    
    # Test compilation and execution
    runner = CppContainerRunner()
    
    print("Running C++ code...")
    output, runtime = runner.run_code(cpp_code)
    
    print(f"Runtime: {runtime:.4f} seconds")
    print(f"Output:\n{output}")
    
    # Test compilation only
    print("\n" + "=" * 50)
    print("Testing compilation only...")
    
    compile_output, success = runner.compile_only(cpp_code)
    print(f"Compilation successful: {success}")
    print(f"Compilation output: {compile_output}")

if __name__ == "__main__":
    test_cpp_runner() 