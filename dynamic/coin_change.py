"""
Coin Change Problem using Dynamic Programming

The coin change problem has several variations:
1. Minimum number of coins needed to make a given amount
2. Number of ways to make a given amount using given coins
3. All possible combinations to make a given amount

Problem: Given a set of coin denominations and a target amount, find the minimum
number of coins needed to make that amount, or count the number of ways to make it.

Time Complexity: O(n*amount) where n is the number of coin denominations
Space Complexity: O(n*amount) for the DP table
"""

def coin_change_min_coins(coins, amount):
    """
    Find minimum number of coins needed to make the given amount
    
    Args:
        coins: List of coin denominations
        amount: Target amount to make
    
    Returns:
        Minimum number of coins needed, or -1 if impossible
    """
    if amount == 0:
        return 0
    
    # Initialize dp array with infinity
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0  # Base case: 0 amount needs 0 coins
    
    # Fill dp array
    for i in range(1, amount + 1):
        for coin in coins:
            if coin <= i:
                dp[i] = min(dp[i], dp[i - coin] + 1)
    
    return dp[amount] if dp[amount] != float('inf') else -1


def coin_change_ways(coins, amount):
    """
    Count the number of ways to make the given amount using given coins
    
    Args:
        coins: List of coin denominations
        amount: Target amount to make
    
    Returns:
        Number of ways to make the amount
    """
    n = len(coins)
    dp = [[0 for _ in range(amount + 1)] for _ in range(n + 1)]
    
    # Base case: empty set can make amount 0 in 1 way
    for i in range(n + 1):
        dp[i][0] = 1
    
    # Fill the dp table
    for i in range(1, n + 1):
        for j in range(1, amount + 1):
            if coins[i-1] <= j:
                # Include the current coin
                dp[i][j] = dp[i-1][j] + dp[i][j - coins[i-1]]
            else:
                # Exclude the current coin
                dp[i][j] = dp[i-1][j]
    
    return dp[n][amount]


def coin_change_ways_optimized(coins, amount):
    """
    Space-optimized version to count ways
    
    Args:
        coins: List of coin denominations
        amount: Target amount to make
    
    Returns:
        Number of ways to make the amount
    """
    dp = [0] * (amount + 1)
    dp[0] = 1  # Base case
    
    for coin in coins:
        for i in range(coin, amount + 1):
            dp[i] += dp[i - coin]
    
    return dp[amount]


def coin_change_get_combinations(coins, amount):
    """
    Get all possible combinations to make the given amount
    
    Args:
        coins: List of coin denominations
        amount: Target amount to make
    
    Returns:
        List of all possible combinations (each combination is a list of coin counts)
    """
    def backtrack(target, start, current_combination):
        if target == 0:
            result.append(current_combination[:])
            return
        
        for i in range(start, len(coins)):
            if coins[i] <= target:
                current_combination[i] += 1
                backtrack(target - coins[i], i, current_combination)
                current_combination[i] -= 1
    
    result = []
    current_combination = [0] * len(coins)
    backtrack(amount, 0, current_combination)
    return result


def coin_change_get_min_combination(coins, amount):
    """
    Get the combination that uses minimum number of coins
    
    Args:
        coins: List of coin denominations
        amount: Target amount to make
    
    Returns:
        Tuple of (min_coins, combination) where combination is a list of coin counts
    """
    if amount == 0:
        return 0, [0] * len(coins)
    
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0
    
    # Track which coin was used for each amount
    coin_used = [-1] * (amount + 1)
    
    for i in range(1, amount + 1):
        for j, coin in enumerate(coins):
            if coin <= i and dp[i - coin] + 1 < dp[i]:
                dp[i] = dp[i - coin] + 1
                coin_used[i] = j
    
    if dp[amount] == float('inf'):
        return -1, []
    
    # Reconstruct the combination
    combination = [0] * len(coins)
    current_amount = amount
    while current_amount > 0:
        coin_index = coin_used[current_amount]
        combination[coin_index] += 1
        current_amount -= coins[coin_index]
    
    return dp[amount], combination


def coin_change_unlimited_supply(coins, amount):
    """
    Coin change with unlimited supply of each coin
    
    Args:
        coins: List of coin denominations
        amount: Target amount to make
    
    Returns:
        Minimum number of coins needed
    """
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0
    
    for i in range(1, amount + 1):
        for coin in coins:
            if coin <= i:
                dp[i] = min(dp[i], dp[i - coin] + 1)
    
    return dp[amount] if dp[amount] != float('inf') else -1


def coin_change_limited_supply(coins, counts, amount):
    """
    Coin change with limited supply of each coin
    
    Args:
        coins: List of coin denominations
        counts: List of available counts for each coin
        amount: Target amount to make
    
    Returns:
        Minimum number of coins needed, or -1 if impossible
    """
    n = len(coins)
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0
    
    for i in range(n):
        for j in range(amount, coins[i] - 1, -1):
            for k in range(1, counts[i] + 1):
                if j >= k * coins[i]:
                    dp[j] = min(dp[j], dp[j - k * coins[i]] + k)
    
    return dp[amount] if dp[amount] != float('inf') else -1


# Example usage and testing
if __name__ == "__main__":
    print("Coin Change Problem")
    print("=" * 30)
    
    # Test cases
    test_cases = [
        ([1, 2, 5], 11),
        ([2], 3),
        ([1], 0),
        ([1, 3, 4], 6),
        ([1, 2, 5, 10], 18)
    ]
    
    for coins, amount in test_cases:
        print(f"\nCoins: {coins}")
        print(f"Amount: {amount}")
        
        # Test minimum coins
        min_coins = coin_change_min_coins(coins, amount)
        print(f"Minimum coins needed: {min_coins}")
        
        # Test number of ways
        ways = coin_change_ways(coins, amount)
        ways_opt = coin_change_ways_optimized(coins, amount)
        print(f"Number of ways: {ways}")
        print(f"Number of ways (optimized): {ways_opt}")
        
        # Test getting minimum combination
        min_combination = coin_change_get_min_combination(coins, amount)
        if min_combination[0] != -1:
            print(f"Minimum combination: {min_combination[1]}")
            print(f"Coins used: {[coins[i] for i in range(len(coins)) for _ in range(min_combination[1][i])]}")
        
        # Test unlimited supply
        unlimited = coin_change_unlimited_supply(coins, amount)
        print(f"Minimum coins (unlimited supply): {unlimited}")
        
        # Verify consistency
        assert ways == ways_opt, "Ways calculation should be consistent"
        if min_coins != -1:
            assert min_coins == unlimited, "Minimum coins should be same for unlimited supply"
        
        print("✅ All methods produce consistent results!")
    
    # Test limited supply
    print(f"\nLimited Supply Test:")
    coins = [1, 2, 5]
    counts = [3, 2, 1]  # 3 ones, 2 twos, 1 five
    amount = 8
    limited_result = coin_change_limited_supply(coins, counts, amount)
    print(f"Coins: {coins}")
    print(f"Available counts: {counts}")
    print(f"Amount: {amount}")
    print(f"Minimum coins (limited supply): {limited_result}") 