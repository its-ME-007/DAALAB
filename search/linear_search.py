def linear_search(arr: list, target: int) -> int:
    """
    Perform linear search on the given array.
    Returns the index of the target if found, -1 otherwise.
    """
    for i in range(len(arr)):
        if arr[i] == target:
            return i
    return -1 