def interpolation_search(arr: list, target: int) -> int:
    """
    Perform interpolation search on the given array.
    The array will be sorted before searching.
    Returns the index of the target if found, -1 otherwise.
    """
    # Sort the array first
    sorted_arr = sorted(arr)
    
    low = 0
    high = len(sorted_arr) - 1
    
    while low <= high and target >= sorted_arr[low] and target <= sorted_arr[high]:
        if low == high:
            if sorted_arr[low] == target:
                return low
            return -1
            
        # Interpolation formula
        pos = low + int(((float(high - low) / (sorted_arr[high] - sorted_arr[low])) * (target - sorted_arr[low])))
        
        if sorted_arr[pos] == target:
            return pos
            
        if sorted_arr[pos] < target:
            low = pos + 1
        else:
            high = pos - 1
            
    return -1 