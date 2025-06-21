# Dynamic Programming Algorithms

This package contains implementations of classic dynamic programming problems with multiple approaches and optimizations.

## Problems Included

### 1. 0/1 Knapsack Problem (`knapsack_01.py`)
- **Problem**: Given items with weights and values, maximize total value while staying within weight capacity
- **Constraint**: Each item can only be used once (0/1 decision)
- **Time Complexity**: O(n*W) where n = number of items, W = capacity
- **Space Complexity**: O(n*W)

**Functions:**
- `knapsack_01_recursive()` - Recursive solution with memoization
- `knapsack_01_dp()` - Bottom-up dynamic programming
- `knapsack_01_get_items()` - Returns optimal items selected
- `knapsack_01_optimized()` - Space-optimized 1D array solution

### 2. Subset Sum Problem (`subset_sum.py`)
- **Problem**: Determine if there exists a subset of given set that sums to target value
- **Time Complexity**: O(n*sum) where n = number of elements
- **Space Complexity**: O(n*sum)

**Functions:**
- `subset_sum_recursive()` - Recursive solution
- `subset_sum_dp()` - Bottom-up dynamic programming
- `subset_sum_optimized()` - Space-optimized 1D array solution
- `subset_sum_get_subset()` - Returns actual subset that sums to target
- `subset_sum_count()` - Counts number of subsets that sum to target

### 3. Coin Change Problem (`coin_change.py`)
- **Problem**: Find minimum coins needed or count ways to make given amount
- **Time Complexity**: O(n*amount) where n = number of coin denominations
- **Space Complexity**: O(n*amount)

**Functions:**
- `coin_change_min_coins()` - Minimum coins needed
- `coin_change_ways()` - Count ways to make amount
- `coin_change_ways_optimized()` - Space-optimized ways counting
- `coin_change_get_combinations()` - All possible combinations
- `coin_change_get_min_combination()` - Optimal combination
- `coin_change_unlimited_supply()` - Unlimited coin supply
- `coin_change_limited_supply()` - Limited coin supply

## Usage Examples

### 0/1 Knapsack
```python
from dynamic import knapsack_01_dp, knapsack_01_get_items

weights = [2, 3, 4, 5]
values = [3, 4, 5, 6]
capacity = 10

max_value = knapsack_01_dp(weights, values, capacity)
print(f"Maximum value: {max_value}")

max_value, selected_items = knapsack_01_get_items(weights, values, capacity)
print(f"Selected items: {selected_items}")
```

### Subset Sum
```python
from dynamic import subset_sum_dp, subset_sum_get_subset

arr = [3, 34, 4, 12, 5, 2]
target = 9

exists = subset_sum_dp(arr, target)
print(f"Subset exists: {exists}")

if exists:
    exists, subset = subset_sum_get_subset(arr, target)
    print(f"One such subset: {subset}")
```

### Coin Change
```python
from dynamic import coin_change_min_coins, coin_change_ways

coins = [1, 2, 5]
amount = 11

min_coins = coin_change_min_coins(coins, amount)
print(f"Minimum coins needed: {min_coins}")

ways = coin_change_ways(coins, amount)
print(f"Number of ways: {ways}")
```

## Running Tests

Each module includes comprehensive test cases. Run them directly:

```bash
# Test 0/1 Knapsack
python knapsack_01.py

# Test Subset Sum
python subset_sum.py

# Test Coin Change
python coin_change.py
```

## Performance Considerations

1. **Space Optimization**: Use the `_optimized` versions for better space efficiency
2. **Large Inputs**: For very large inputs, consider using the recursive versions with memoization
3. **Memory Usage**: The DP table can be large for big inputs - monitor memory usage

## Algorithm Analysis

### Time Complexity Comparison
- **Recursive**: Exponential O(2^n) without memoization
- **DP Bottom-up**: O(n*W) or O(n*sum) depending on problem
- **Optimized**: Same time complexity, better space complexity

### Space Complexity Comparison
- **Standard DP**: O(n*W) or O(n*sum)
- **Optimized**: O(W) or O(sum) - significant improvement

## Contributing

To add new dynamic programming problems:
1. Create a new Python file in the `dynamic/` directory
2. Implement the algorithm with clear documentation
3. Include test cases in the `__main__` section
4. Update `__init__.py` to export the functions
5. Update this README with problem description

## Dependencies

- Python 3.7+
- No external dependencies required (uses only standard library)
- Optional: pytest for testing, matplotlib/numpy for visualization 