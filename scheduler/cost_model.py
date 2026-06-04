"""Cost estimation model for code execution scheduling.

This module converts AI-derived time complexity (Big-O notation) into concrete
execution time estimates used for complexity-aware scheduling.
"""

import math
from typing import Optional
from common.models import ComplexityAnalysis, Language
from common.constants import (
    LANGUAGE_MULTIPLIER,
    COMPLEXITY_BASE_COST,
    DEFAULT_COST_MS
)


def complexity_growth(complexity: str, input_size: int) -> float:
    """
    Calculate growth factor based on complexity class and input size.
    
    Args:
        complexity: Big-O notation (e.g., "O(n)", "O(n^2)")
        input_size: Input size (n)
    
    Returns:
        Growth factor (unitless)
    
    Examples:
        >>> complexity_growth("O(1)", 1000)
        1.0
        >>> complexity_growth("O(n)", 1000)
        1000.0
        >>> complexity_growth("O(n^2)", 100)
        10000.0
    """
    n = max(input_size, 1)  # Avoid log(0)
    
    # Normalize complexity string (handle variations)
    complexity = complexity.strip().upper()
    
    # Map complexity to growth function
    growth_map = {
        "O(1)": lambda: 1.0,
        "O(LOG N)": lambda: math.log2(n),
        "O(N)": lambda: float(n),
        "O(N LOG N)": lambda: n * math.log2(n),
        "O(N^2)": lambda: float(n * n),
        "O(N**2)": lambda: float(n * n),
        "O(N²)": lambda: float(n * n),
        "O(N^3)": lambda: float(n * n * n),
        "O(N**3)": lambda: float(n * n * n),
        "O(2^N)": lambda: min(2.0 ** min(n, 20), 1e6),  # Cap exponential
        "O(N!)": lambda: min(math.factorial(min(n, 7)), 1e6),  # Cap factorial (7! = 5040)
    }
    
    # Find matching complexity
    for pattern, func in growth_map.items():
        if pattern in complexity:
            return func()
    
    # Unknown complexity - return base value
    return 1.0


def estimate_execution_cost(
    complexity_analysis: Optional[ComplexityAnalysis],
    language: Language,
    input_size: int = 1000
) -> float:
    """
    Estimate execution cost in milliseconds based on complexity and language.
    
    This is the core cost estimation function used by the scheduler to make
    routing decisions.
    
    Args:
        complexity_analysis: AI-derived complexity (can be None)
        language: Programming language (python or cpp)
        input_size: Input size for scaling
    
    Returns:
        Estimated execution time in milliseconds
    
    Algorithm:
        1. If complexity unknown → return DEFAULT_COST_MS
        2. Calculate growth = complexity_growth(complexity, input_size)
        3. Get base_cost from COMPLEXITY_BASE_COST
        4. Apply language multiplier
        5. Return base_cost * growth * language_multiplier
    
    Examples:
        >>> from common.models import ComplexityAnalysis, Language
        >>> analysis = ComplexityAnalysis(time_complexity="O(n)", confidence=0.9)
        >>> estimate_execution_cost(analysis, Language.PYTHON, 1000)
        400000.0  # 100ms base * 1000 growth * 4.0 python multiplier
    """
    # Handle missing complexity analysis
    if complexity_analysis is None or complexity_analysis.confidence < 0.5:
        return DEFAULT_COST_MS
    
    complexity = complexity_analysis.time_complexity
    
    # Get base cost for this complexity class
    base_cost = COMPLEXITY_BASE_COST.get(complexity, DEFAULT_COST_MS)
    
    # Calculate growth factor
    growth = complexity_growth(complexity, input_size)
    
    # Apply language multiplier
    language_str = language.value if isinstance(language, Language) else language
    language_factor = LANGUAGE_MULTIPLIER.get(language_str, 1.0)
    
    # Final cost estimate
    estimated_cost = base_cost * growth * language_factor
    
    # Cap to guard against exponential/factorial blowup only (1 hour). The
    # previous 5-minute cap clamped ordinary polynomial jobs (e.g. O(n) Python at
    # n=1000 = 400,000ms), which collapsed the language multiplier and input-size
    # scaling the scheduler relies on. complexity_growth() already bounds the
    # growth factor for O(2^n)/O(n!), so this only catches genuine blowup.
    return min(estimated_cost, 3_600_000.0)


def estimate_cost_simple(
    complexity: str,
    language: str,
    input_size: int = 1000
) -> float:
    """
    Simplified cost estimation without Pydantic models.
    
    Useful for quick calculations or testing.
    
    Args:
        complexity: Big-O notation string (e.g., "O(n log n)")
        language: Language string ("python" or "cpp")
        input_size: Input size
    
    Returns:
        Estimated cost in milliseconds
    """
    base_cost = COMPLEXITY_BASE_COST.get(complexity, DEFAULT_COST_MS)
    growth = complexity_growth(complexity, input_size)
    language_factor = LANGUAGE_MULTIPLIER.get(language, 1.0)

    return min(base_cost * growth * language_factor, 3_600_000.0)


def get_complexity_class_cost(complexity: str) -> float:
    """
    Get base cost for a complexity class without growth calculation.
    
    Useful for displaying complexity rankings.
    
    Args:
        complexity: Big-O notation
    
    Returns:
        Base cost in milliseconds
    """
    return COMPLEXITY_BASE_COST.get(complexity, DEFAULT_COST_MS)


# ============================================================================
# Cost Model Diagnostics
# ============================================================================

def print_cost_table():
    """Print cost estimation table for all complexity classes and languages."""
    print("=" * 80)
    print("COST ESTIMATION TABLE (input_size=1000)")
    print("=" * 80)
    print(f"{'Complexity':<20} {'Python (ms)':<20} {'C++ (ms)':<20}")
    print("-" * 80)
    
    complexities = ["O(1)", "O(log n)", "O(n)", "O(n log n)", "O(n^2)", "O(n^3)"]
    
    for complexity in complexities:
        python_cost = estimate_cost_simple(complexity, "python", 1000)
        cpp_cost = estimate_cost_simple(complexity, "cpp", 1000)
        print(f"{complexity:<20} {python_cost:<20.2f} {cpp_cost:<20.2f}")
    
    print("=" * 80)


if __name__ == "__main__":
    # Diagnostic output
    print_cost_table()
