"""
0/1 Knapsack Problem using Dynamic Programming

The 0/1 knapsack problem is a classic optimization problem where we have:
- A set of items, each with a weight and value
- A knapsack with a maximum weight capacity
- Goal: Maximize the total value while staying within the weight limit
- Constraint: Each item can only be used once (0/1 decision)

Time Complexity: O(n*W) where n is number of items and W is knapsack capacity
Space Complexity: O(n*W) for the DP table
"""

def knapsack_01_recursive(weights, values, capacity, n=None):
    """
    Recursive solution with memoization for 0/1 knapsack
    
    Args:
        weights: List of item weights
        values: List of item values
        capacity: Maximum weight capacity of knapsack
        n: Number of items (defaults to len(weights))
    
    Returns:
        Maximum value that can be achieved
    """
    if n is None:
        n = len(weights)
    
    # Base case: no items or no capacity
    if n == 0 or capacity == 0:
        return 0
    
    # If weight of nth item is more than capacity, skip it
    if weights[n-1] > capacity:
        return knapsack_01_recursive(weights, values, capacity, n-1)
    
    # Return maximum of two cases:
    # 1. Include the nth item
    # 2. Exclude the nth item
    else:
        include = values[n-1] + knapsack_01_recursive(weights, values, capacity - weights[n-1], n-1)
        exclude = knapsack_01_recursive(weights, values, capacity, n-1)
        return max(include, exclude)


def knapsack_01_dp(weights, values, capacity):
    """
    Dynamic programming solution for 0/1 knapsack using bottom-up approach
    
    Args:
        weights: List of item weights
        values: List of item values
        capacity: Maximum weight capacity of knapsack
    
    Returns:
        Maximum value that can be achieved
    """
    n = len(weights)
    
    # Create a 2D DP table
    # dp[i][w] represents the maximum value that can be achieved
    # using items 0 to i-1 with capacity w
    dp = [[0 for _ in range(capacity + 1)] for _ in range(n + 1)]
    
    # Build table dp[][] in bottom-up manner
    for i in range(1, n + 1):
        for w in range(capacity + 1):
            # If weight of current item is less than or equal to current capacity
            if weights[i-1] <= w:
                # Choose maximum of including or excluding current item
                dp[i][w] = max(values[i-1] + dp[i-1][w - weights[i-1]], dp[i-1][w])
            else:
                # Cannot include current item
                dp[i][w] = dp[i-1][w]
    
    return dp[n][capacity]


def knapsack_01_get_items(weights, values, capacity):
    """
    Get the items that should be included in the optimal solution
    
    Args:
        weights: List of item weights
        values: List of item values
        capacity: Maximum weight capacity of knapsack
    
    Returns:
        Tuple of (max_value, selected_items)
    """
    n = len(weights)
    dp = [[0 for _ in range(capacity + 1)] for _ in range(n + 1)]
    
    # Build the DP table
    for i in range(1, n + 1):
        for w in range(capacity + 1):
            if weights[i-1] <= w:
                dp[i][w] = max(values[i-1] + dp[i-1][w - weights[i-1]], dp[i-1][w])
            else:
                dp[i][w] = dp[i-1][w]
    
    # Backtrack to find selected items
    selected_items = []
    w = capacity
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i-1][w]:
            selected_items.append(i-1)  # Item index (0-based)
            w -= weights[i-1]
    
    return dp[n][capacity], selected_items[::-1]  # Reverse to get original order


def knapsack_01_optimized(weights, values, capacity):
    """
    Space-optimized version using only 1D array
    
    Args:
        weights: List of item weights
        values: List of item values
        capacity: Maximum weight capacity of knapsack
    
    Returns:
        Maximum value that can be achieved
    """
    n = len(weights)
    dp = [0] * (capacity + 1)
    
    for i in range(n):
        # Iterate backwards to avoid overwriting values we need
        for w in range(capacity, weights[i] - 1, -1):
            dp[w] = max(dp[w], dp[w - weights[i]] + values[i])
    
    return dp[capacity]


# Example usage and testing
if __name__ == "__main__":
    # Test case
    weights = [2, 3, 4, 5]
    values = [3, 4, 5, 6]
    capacity = 10
    
    print("0/1 Knapsack Problem")
    print("=" * 30)
    print(f"Weights: {weights}")
    print(f"Values: {values}")
    print(f"Capacity: {capacity}")
    print()
    
    # Test all methods
    result_dp = knapsack_01_dp(weights, values, capacity)
    result_opt = knapsack_01_optimized(weights, values, capacity)
    result_with_items = knapsack_01_get_items(weights, values, capacity)
    
    print(f"Maximum value (DP): {result_dp}")
    print(f"Maximum value (Optimized): {result_opt}")
    print(f"Maximum value with items: {result_with_items[0]}")
    print(f"Selected items (indices): {result_with_items[1]}")
    print(f"Selected weights: {[weights[i] for i in result_with_items[1]]}")
    print(f"Selected values: {[values[i] for i in result_with_items[1]]}")
    
    # Verify all methods give same result
    assert result_dp == result_opt == result_with_items[0], "All methods should give same result"
    print("\n✅ All methods produce consistent results!") 