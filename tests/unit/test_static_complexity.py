"""Unit tests for the static complexity analyzer (code_assist/static_analyzer.py)."""

import pytest

from code_assist.static_analyzer import analyze_static, _CPP_PARSER
from common.constants import STATIC_CONFIDENCE_THRESHOLD, COMPLEXITY_BASE_COST
from tests.fixtures.code_samples import get_sample


# ============================================================================
# Python backend (stdlib ast) — always available
# ============================================================================

def test_constant_time_python():
    result = analyze_static(get_sample("constant", "python"), "python")
    assert result is not None
    assert result.time_complexity == "O(1)"
    assert result.confidence >= STATIC_CONFIDENCE_THRESHOLD


def test_linear_time_python():
    result = analyze_static(get_sample("linear", "python"), "python")
    assert result is not None
    assert result.time_complexity == "O(n)"
    assert result.confidence >= STATIC_CONFIDENCE_THRESHOLD


def test_quadratic_time_python():
    result = analyze_static(get_sample("quadratic", "python"), "python")
    assert result is not None
    assert result.time_complexity == "O(n^2)"
    assert result.confidence >= STATIC_CONFIDENCE_THRESHOLD


def test_builtin_sort_is_linearithmic():
    # Sample index 1 is the `sorted(arr)` builtin-sort snippet (no explicit loops).
    result = analyze_static(get_sample("linearithmic", "python", index=1), "python")
    assert result is not None
    assert result.time_complexity == "O(n log n)"


def test_recursion_yields_low_confidence():
    # merge_sort (index 0) is recursive — static can't classify divide-and-conquer,
    # so it must defer to the LLM via a sub-threshold confidence.
    result = analyze_static(get_sample("linearithmic", "python", index=0), "python")
    assert result is not None
    assert result.confidence < STATIC_CONFIDENCE_THRESHOLD


def test_three_nested_loops_is_cubic():
    code = """
def triple(arr):
    total = 0
    for a in arr:
        for b in arr:
            for c in arr:
                total += a + b + c
    return total
"""
    result = analyze_static(code, "python")
    assert result is not None
    assert result.time_complexity == "O(n^3)"


def test_nested_comprehension_counts_as_loops():
    code = "matrix = [[i * j for j in range(100)] for i in range(100)]\n"
    result = analyze_static(code, "python")
    assert result is not None
    assert result.time_complexity == "O(n^2)"


def test_syntax_error_returns_none():
    assert analyze_static("def broken(:\n    pass", "python") is None


def test_empty_code_returns_none():
    assert analyze_static("", "python") is None
    assert analyze_static("   \n  ", "python") is None


def test_estimated_time_ms_uses_shared_cost_table():
    result = analyze_static(get_sample("quadratic", "python"), "python")
    assert result is not None
    assert result.estimated_time_ms == COMPLEXITY_BASE_COST["O(n^2)"]


def test_unknown_language_returns_none():
    assert analyze_static("SELECT * FROM t;", "sql") is None


# ============================================================================
# C++ backend (tree-sitter) — skipped if the optional package isn't installed
# ============================================================================

cpp_required = pytest.mark.skipif(
    _CPP_PARSER is None, reason="tree-sitter / tree-sitter-cpp not installed"
)


@cpp_required
def test_linear_time_cpp():
    result = analyze_static(get_sample("linear", "cpp"), "cpp")
    assert result is not None
    assert result.time_complexity == "O(n)"


@cpp_required
def test_quadratic_time_cpp():
    result = analyze_static(get_sample("quadratic", "cpp"), "cpp")
    assert result is not None
    assert result.time_complexity == "O(n^2)"


@cpp_required
def test_std_sort_is_linearithmic_cpp():
    result = analyze_static(get_sample("linearithmic", "cpp"), "cpp")
    assert result is not None
    assert result.time_complexity == "O(n log n)"
