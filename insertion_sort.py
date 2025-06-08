"""
Insertion Sort Implementation
A complete insertion sort algorithm with demonstration.
"""

def insertion_sort(arr):
    """
    Main function to do insertion sort
    """
    # Create a copy to avoid modifying the original array
    arr_copy = arr.copy()
    n = len(arr_copy)
    
    # Traverse through 1 to len(arr)
    for i in range(1, n):
        key = arr_copy[i]
        
        # Move elements of arr[0..i-1], that are greater than key,
        # to one position ahead of their current position
        j = i - 1
        while j >= 0 and arr_copy[j] > key:
            arr_copy[j + 1] = arr_copy[j]
            j -= 1
        arr_copy[j + 1] = key
    
    return arr_copy 