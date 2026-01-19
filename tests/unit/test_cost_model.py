"""Unit tests for cost model."""

import pytest
from scheduler.cost_model import (
    complexity_growth,
    estimate_execution_cost,
    estimate_cost_simple,
    get_complexity_class_cost
)
from common.models import ComplexityAnalysis, Language


class TestComplexityGrowth:
    """Test complexity growth calculations."""
    
    def test_constant_complexity(self):
        """O(1) should always return 1.0."""
        assert complexity_growth("O(1)", 10) == 1.0
        assert complexity_growth("O(1)", 1000) == 1.0
        assert complexity_growth("O(1)", 1000000) == 1.0
    
    def test_linear_complexity(self):
        """O(n) should return n."""
        assert complexity_growth("O(n)", 100) == 100.0
        assert complexity_growth("O(n)", 1000) == 1000.0
    
    def test_quadratic_complexity(self):
        """O(n^2) should return n²."""
        assert complexity_growth("O(n^2)", 10) == 100.0
        assert complexity_growth("O(n^2)", 100) == 10000.0
    
    def test_logarithmic_complexity(self):
        """O(log n) should return log2(n)."""
        import math
        n = 1024
        expected = math.log2(n)
        assert abs(complexity_growth("O(log n)", n) - expected) < 0.01
    
    def test_linearithmic_complexity(self):
        """O(n log n) should return n * log2(n)."""
        import math
        n = 1000
        expected = n * math.log2(n)
        result = complexity_growth("O(n log n)", n)
        assert abs(result - expected) < 1.0  # Allow small floating point error
    
    def test_unknown_complexity(self):
        """Unknown complexity should return 1.0."""
        assert complexity_growth("O(unknown)", 1000) == 1.0
        assert complexity_growth("UNKNOWN", 1000) == 1.0


class TestCostEstimation:
    """Test execution cost estimation."""
    
    def test_python_vs_cpp_multiplier(self):
        """Python should be 4x more expensive than C++."""
        analysis = ComplexityAnalysis(
            time_complexity="O(n)",
            confidence=0.9
        )
        
        python_cost = estimate_execution_cost(analysis, Language.PYTHON, 1000)
        cpp_cost = estimate_execution_cost(analysis, Language.CPP, 1000)
        
        assert python_cost / cpp_cost == pytest.approx(4.0, rel=0.01)
    
    def test_low_confidence_returns_default(self):
        """Low confidence should return default cost."""
        from common.constants import DEFAULT_COST_MS
        
        analysis = ComplexityAnalysis(
            time_complexity="O(n^2)",
            confidence=0.3  # Low confidence
        )
        
        cost = estimate_execution_cost(analysis, Language.PYTHON, 1000)
        assert cost == DEFAULT_COST_MS
    
    def test_none_analysis_returns_default(self):
        """None analysis should return default cost."""
        from common.constants import DEFAULT_COST_MS
        
        cost = estimate_execution_cost(None, Language.PYTHON, 1000)
        assert cost == DEFAULT_COST_MS
    
    def test_cost_increases_with_input_size(self):
        """Cost should increase with input size for non-constant complexity."""
        analysis = ComplexityAnalysis(
            time_complexity="O(n)",
            confidence=0.9
        )
        
        cost_small = estimate_execution_cost(analysis, Language.PYTHON, 100)
        cost_large = estimate_execution_cost(analysis, Language.PYTHON, 1000)
        
        assert cost_large > cost_small
        assert cost_large / cost_small == pytest.approx(10.0, rel=0.1)
    
    def test_cost_cap(self):
        """Cost should be capped at maximum value."""
        analysis = ComplexityAnalysis(
            time_complexity="O(n^3)",
            confidence=0.9
        )
        
        cost = estimate_execution_cost(analysis, Language.PYTHON, 1000000)
        assert cost <= 300000.0  # Max cap


class TestSimpleCostEstimation:
    """Test simplified cost estimation API."""
    
    def test_estimate_cost_simple(self):
        """Simplified API should work without Pydantic models."""
        cost = estimate_cost_simple("O(n)", "python", 1000)
        assert cost > 0
    
    def test_get_complexity_class_cost(self):
        """Get base cost for complexity class."""
        from common.constants import COMPLEXITY_BASE_COST
        
        cost = get_complexity_class_cost("O(n)")
        assert cost == COMPLEXITY_BASE_COST["O(n)"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
