def binary_search(arr: list, target: int) -> int:
    """
    Perform binary search on the given array.
    The array should be sorted before calling this function.
    Returns the index of the target if found, -1 otherwise.
    """
    left = 0
    right = len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
            
    return -1 