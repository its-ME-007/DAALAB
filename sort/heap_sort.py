"""
Heap Sort Implementation
A complete heap sort algorithm with demonstration.
"""

import sys
import json
import random
import time
from datetime import datetime


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


def read_input(filename="input.txt"):
    """Read input from file"""
    try:
        with open(filename, 'r') as f:
            content = f.read().strip()
            if content == "random":
                return generate_random_array(15, 50)
            return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading input file: {e}")
        return generate_random_array(15, 50)


def write_output(results, filename="output.txt"):
    """Write results to output file"""
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)


def main():
    # Read input
    arr = read_input()
    
    # Create a copy for sorting
    arr_copy = arr.copy()
    
    # Measure execution time using perf_counter for higher precision
    start_time = time.perf_counter()
    sorted_arr = heap_sort(arr_copy)
    end_time = time.perf_counter()
    
    # Calculate execution time in milliseconds
    execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
    
    # Prepare results
    results = {
        "timestamp": datetime.now().isoformat(),
        "original_array": arr,
        "sorted_array": sorted_arr,
        "array_size": len(arr),
        "execution_time_ms": round(execution_time, 5),  # Changed back to milliseconds
        "is_sorted": all(sorted_arr[i] <= sorted_arr[i+1] for i in range(len(sorted_arr)-1))
    }
    
    # Write results to file
    write_output(results)
    
    return 0


if __name__ == "__main__":
    exit(main())