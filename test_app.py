#!/usr/bin/env python3
"""
Test script to verify all algorithm categories work correctly
"""

def test_imports():
    """Test that all modules can be imported successfully"""
    print("Testing imports...")
    
    # Test sorting algorithms
    from sort.heap_sort import heap_sort
    from sort.merge_sort import merge_sort
    from sort.quick_sort import quick_sort
    from sort.insertion_sort import insertion_sort
    print("✅ Sorting algorithms imported")
    
    # Test search algorithms
    from search.linear_search import linear_search
    from search.binary_search import binary_search
    from search.interpolation_search import interpolation_search
    print("✅ Search algorithms imported")
    
    # Test greedy algorithms
    from greedy import (
        huffman_compression, huffman_decompression,
        fractional_knapsack, generate_sample_data,
        prims_mst, kruskals_mst,
        dijkstras_shortest_path, generate_sample_graph
    )
    print("✅ Greedy algorithms imported")
    
    # Test dynamic programming algorithms
    from dynamic import (
        knapsack_01_dp, knapsack_01_get_items,
        subset_sum_dp, subset_sum_get_subset,
        coin_change_min_coins, coin_change_ways
    )
    print("✅ Dynamic programming algorithms imported")
    
    # Test main app
    from app import main
    print("✅ Main app imported")

def test_algorithms():
    """Test that algorithms work correctly"""
    print("\nTesting algorithms...")
    
    # Test sorting
    arr = [3, 1, 4, 1, 5, 9, 2, 6]
    from sort.quick_sort import quick_sort
    sorted_arr = quick_sort(arr.copy())
    assert sorted_arr == sorted(arr), "Quick sort failed"
    print("✅ Quick sort works")
    
    # Test search
    from search.binary_search import binary_search
    result = binary_search(sorted_arr, 5)
    assert result >= 0, "Binary search failed"
    print("✅ Binary search works")
    
    # Test Huffman coding
    from greedy.huffman import huffman_compression
    result = huffman_compression("hello world")
    assert result["compression_ratio"] > 0, "Huffman compression failed"
    print("✅ Huffman coding works")
    
    # Test dynamic programming
    from dynamic import knapsack_01_dp
    result = knapsack_01_dp([1, 2, 3], [10, 20, 30], 5)
    assert result == 50, "Knapsack failed"
    print("✅ Dynamic programming works")

if __name__ == "__main__":
    try:
        test_imports()
        test_algorithms()
        print("\n🎉 All tests passed! Your algorithm visualizer is ready to use.")
        print("\nTo run the app:")
        print("streamlit run app.py")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc() 