
def partition(arr, low, high):
    """
    Partition the array and return the pivot index
    """
    # Choose the rightmost element as pivot
    pivot = arr[high]
    
    # Index of smaller element
    i = low - 1
    
    for j in range(low, high):
        # If current element is smaller than or equal to pivot
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    
    # Place pivot at its correct position
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1

def quick_sort(arr):
    """
    Main function to do quick sort
    """
    def _quick_sort(arr, low, high):
        if low < high:
            # Get the partition index
            pi = partition(arr, low, high)
            
            # Sort elements before and after partition
            _quick_sort(arr, low, pi - 1)
            _quick_sort(arr, pi + 1, high)
    
    # Create a copy to avoid modifying the original array
    arr_copy = arr.copy()
    _quick_sort(arr_copy, 0, len(arr_copy) - 1)
    return arr_copy 