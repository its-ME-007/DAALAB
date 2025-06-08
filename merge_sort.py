"""
Merge Sort Implementation
A complete merge sort algorithm with demonstration.
"""

def merge(left, right):
    """
    Merge two sorted arrays into a single sorted array
    """
    result = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    # Add remaining elements
    result.extend(left[i:])
    result.extend(right[j:])
    
    return result

def merge_sort(arr):
    """
    Main function to do merge sort
    """
    if len(arr) <= 1:
        return arr
    
    # Find the middle point
    mid = len(arr) // 2
    
    # Sort first and second halves
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    
    # Merge the sorted halves
    return merge(left, right) 