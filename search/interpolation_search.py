def interpolation_search(arr: list, target: int) -> int:
    """
    Perform interpolation search on the given array.
    The array should be sorted before calling this function.
    Returns the index of the target if found, -1 otherwise.
    """
    low = 0
    high = len(arr) - 1
    
    while low <= high and target >= arr[low] and target <= arr[high]:
        if low == high:
            if arr[low] == target:
                return low
            return -1
            
        # Interpolation formula
        pos = low + int(((float(high - low) / (arr[high] - arr[low])) * (target - arr[low])))
        
        if arr[pos] == target:
            return pos
            
        if arr[pos] < target:
            low = pos + 1
        else:
            high = pos - 1
            
    return -1 