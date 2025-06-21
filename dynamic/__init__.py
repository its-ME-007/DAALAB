"""
Dynamic Programming Algorithms Package

This package contains implementations of classic dynamic programming problems:
- 0/1 Knapsack Problem
- Subset Sum Problem  
- Coin Change Problem

Each module provides multiple approaches including recursive, iterative DP,
and optimized versions.
"""

from .knapsack_01 import (
    knapsack_01_recursive,
    knapsack_01_dp,
    knapsack_01_get_items,
    knapsack_01_optimized
)

from .subset_sum import (
    subset_sum_recursive,
    subset_sum_dp,
    subset_sum_optimized,
    subset_sum_get_subset,
    subset_sum_count
)

from .coin_change import (
    coin_change_min_coins,
    coin_change_ways,
    coin_change_ways_optimized,
    coin_change_get_combinations,
    coin_change_get_min_combination,
    coin_change_unlimited_supply,
    coin_change_limited_supply
)

__all__ = [
    # Knapsack functions
    'knapsack_01_recursive',
    'knapsack_01_dp', 
    'knapsack_01_get_items',
    'knapsack_01_optimized',
    
    # Subset Sum functions
    'subset_sum_recursive',
    'subset_sum_dp',
    'subset_sum_optimized',
    'subset_sum_get_subset',
    'subset_sum_count',
    
    # Coin Change functions
    'coin_change_min_coins',
    'coin_change_ways',
    'coin_change_ways_optimized',
    'coin_change_get_combinations',
    'coin_change_get_min_combination',
    'coin_change_unlimited_supply',
    'coin_change_limited_supply'
]

__version__ = "1.0.0"
__author__ = "DAALAB"
__description__ = "Dynamic Programming Algorithms Collection" 