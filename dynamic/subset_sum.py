"""
Subset Sum Problem using Dynamic Programming

The subset sum problem is to determine if there exists a subset of a given set
whose sum equals a given target value.

Problem: Given a set of non-negative integers and a target sum, determine if
there is a subset of the given set with sum equal to the given target.

Time Complexity: O(n*sum) where n is the number of elements
Space Complexity: O(n*sum) for the DP table
"""

def subset_sum_recursive(arr, target, n=None):
    """
    Recursive solution for subset sum problem
    
    Args:
        arr: List of non-negative integers
        target: Target sum to achieve
        n: Number of elements to consider (defaults to len(arr))
    
    Returns:
        True if subset exists, False otherwise
    """
    if n is None:
        n = len(arr)
    
    # Base cases
    if target == 0:
        return True
    if n == 0 and target != 0:
        return False
    
    # If last element is greater than target, ignore it
    if arr[n-1] > target:
        return subset_sum_recursive(arr, target, n-1)
    
    # Check if target can be achieved by either including or excluding the last element
    return (subset_sum_recursive(arr, target, n-1) or 
            subset_sum_recursive(arr, target - arr[n-1], n-1))


def subset_sum_dp(arr, target):
    """
    Dynamic programming solution for subset sum using bottom-up approach
    
    Args:
        arr: List of non-negative integers
        target: Target sum to achieve
    
    Returns:
        True if subset exists, False otherwise
    """
    n = len(arr)
    
    # Create a 2D DP table
    # dp[i][j] is True if there is a subset of arr[0..i-1] with sum equal to j
    dp = [[False for _ in range(target + 1)] for _ in range(n + 1)]
    
    # Base case: sum 0 can always be achieved with empty subset
    for i in range(n + 1):
        dp[i][0] = True
    
    # Fill the dp table
    for i in range(1, n + 1):
        for j in range(1, target + 1):
            if arr[i-1] <= j:
                # Include or exclude the current element
                dp[i][j] = dp[i-1][j] or dp[i-1][j - arr[i-1]]
            else:
                # Exclude the current element
                dp[i][j] = dp[i-1][j]
    
    return dp[n][target]


def subset_sum_optimized(arr, target):
    """
    Space-optimized version using only 1D array
    
    Args:
        arr: List of non-negative integers
        target: Target sum to achieve
    
    Returns:
        True if subset exists, False otherwise
    """
    n = len(arr)
    dp = [False] * (target + 1)
    dp[0] = True  # Base case: sum 0 can always be achieved
    
    for i in range(n):
        # Iterate backwards to avoid overwriting values we need
        for j in range(target, arr[i] - 1, -1):
            dp[j] = dp[j] or dp[j - arr[i]]
    
    return dp[target]


def subset_sum_get_subset(arr, target):
    """
    Get the actual subset that sums to the target (if it exists)
    
    Args:
        arr: List of non-negative integers
        target: Target sum to achieve
    
    Returns:
        Tuple of (exists, subset) where exists is boolean and subset is list
    """
    n = len(arr)
    dp = [[False for _ in range(target + 1)] for _ in range(n + 1)]
    
    # Base case
    for i in range(n + 1):
        dp[i][0] = True
    
    # Fill the dp table
    for i in range(1, n + 1):
        for j in range(1, target + 1):
            if arr[i-1] <= j:
                dp[i][j] = dp[i-1][j] or dp[i-1][j - arr[i-1]]
            else:
                dp[i][j] = dp[i-1][j]
    
    if not dp[n][target]:
        return False, []
    
    # Backtrack to find the subset
    subset = []
    i, j = n, target
    while i > 0 and j > 0:
        if dp[i][j] and not dp[i-1][j]:
            subset.append(arr[i-1])
            j -= arr[i-1]
        i -= 1
    
    return True, subset[::-1]  # Reverse to get original order


def subset_sum_count(arr, target):
    """
    Count the number of subsets that sum to the target
    
    Args:
        arr: List of non-negative integers
        target: Target sum to achieve
    
    Returns:
        Number of subsets that sum to target
    """
    n = len(arr)
    dp = [[0 for _ in range(target + 1)] for _ in range(n + 1)]
    
    # Base case: empty subset sums to 0
    for i in range(n + 1):
        dp[i][0] = 1
    
    # Fill the dp table
    for i in range(1, n + 1):
        for j in range(1, target + 1):
            if arr[i-1] <= j:
                dp[i][j] = dp[i-1][j] + dp[i-1][j - arr[i-1]]
            else:
                dp[i][j] = dp[i-1][j]
    
    return dp[n][target]


# Example usage and testing
if __name__ == "__main__":
    # Test cases
    test_cases = [
        ([3, 34, 4, 12, 5, 2], 9),
        ([1, 2, 3, 4, 5], 10),
        ([1, 2, 3, 4, 5], 15),
        ([1, 2, 3, 4, 5], 20),  # Should be False
        ([2, 3, 7, 8, 10], 11),
        ([2, 3, 7, 8, 10], 14)
    ]
    
    print("Subset Sum Problem")
    print("=" * 30)
    
    for arr, target in test_cases:
        print(f"\nArray: {arr}")
        print(f"Target: {target}")
        
        # Test all methods
        result_dp = subset_sum_dp(arr, target)
        result_opt = subset_sum_optimized(arr, target)
        result_with_subset = subset_sum_get_subset(arr, target)
        count = subset_sum_count(arr, target)
        
        print(f"Subset exists (DP): {result_dp}")
        print(f"Subset exists (Optimized): {result_opt}")
        print(f"Subset exists (with subset): {result_with_subset[0]}")
        
        if result_with_subset[0]:
            print(f"One such subset: {result_with_subset[1]}")
            print(f"Sum of subset: {sum(result_with_subset[1])}")
        
        print(f"Number of subsets: {count}")
        
        # Verify all methods give same result
        assert result_dp == result_opt == result_with_subset[0], "All methods should give same result"
        print("✅ All methods produce consistent results!") 