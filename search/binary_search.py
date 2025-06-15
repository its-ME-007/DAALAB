def binary_search(arr: list, target: int) -> int:
    """
    Perform binary search on the given array.
    The array will be sorted before searching.
    Returns the index of the target if found, -1 otherwise.
    """
    # Sort the array first
    sorted_arr = sorted(arr)
    
    left = 0
    right = len(sorted_arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        
        if sorted_arr[mid] == target:
            return mid
        elif sorted_arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
            
    return -1 