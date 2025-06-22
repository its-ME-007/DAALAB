import streamlit as st
import time
import random

# Import sorting algorithms
from sort.heap_sort import heap_sort
from sort.merge_sort import merge_sort
from sort.quick_sort import quick_sort
from sort.insertion_sort import insertion_sort

# Import search algorithms
from search.linear_search import linear_search
from search.binary_search import binary_search
from search.interpolation_search import interpolation_search

# Import greedy algorithms
from greedy import (
    huffman_compression, huffman_decompression,
    fractional_knapsack, generate_sample_data,
    prims_mst, kruskals_mst,
    dijkstras_shortest_path, generate_sample_graph
)

# Import dynamic programming algorithms
from dynamic import (
    knapsack_01_dp, knapsack_01_get_items,
    subset_sum_dp, subset_sum_get_subset,
    coin_change_min_coins, coin_change_ways
)

def generate_random_array(size, max_val):
    return [random.randint(1, max_val) for _ in range(size)]

def measure_execution_time(func, *args, iterations=1000):
    """
    Measure execution time of a function with multiple iterations for accuracy.
    Returns the average execution time in milliseconds.
    """
    # Warm up
    for _ in range(10):
        func(*args)
    
    # Measure
    start_time = time.perf_counter()
    for _ in range(iterations):
        result = func(*args)
    end_time = time.perf_counter()
    
    # Calculate average time in milliseconds
    total_time_ms = (end_time - start_time) * 1000
    avg_time_ms = total_time_ms / iterations
    
    return avg_time_ms, result

def main():
    st.set_page_config(page_title="Algorithm Visualizer", page_icon="🔍", layout="wide")
    st.title("🔍 Algorithm Visualizer")
    st.markdown("---")

    # Mode selection
    mode = st.sidebar.selectbox(
        "Select Algorithm Category:",
        ["sort", "search", "greedy", "dynamic"],
        format_func=lambda x: {"sort": "Sorting Algorithms", "search": "Searching Algorithms", "greedy": "Greedy Algorithms", "dynamic": "Dynamic Programming Algorithms"}[x]
    )

    if mode == "sort":
        handle_sorting()
    elif mode == "search":
        handle_searching()
    elif mode == "greedy":
        handle_greedy()
    else:  # dynamic
        handle_dynamic()

def handle_sorting():
    st.header("📊 Sorting Algorithms")
    
    algorithm = st.radio(
        "Select Sorting Algorithm:",
        ["heap", "merge", "quick", "insertion"],
        format_func=lambda x: {"heap": "Heap Sort", "merge": "Merge Sort", "quick": "Quick Sort", "insertion": "Insertion Sort"}[x],
        horizontal=True
    )

    input_method = st.radio("Choose input method:", ["Manual Input", "Random Array"], horizontal=True)

    if input_method == "Manual Input":
        user_input = st.text_input("Enter numbers separated by spaces:", placeholder="e.g., 5 2 8 1 9")
        if user_input:
            try:
                arr = [int(x) for x in user_input.split()]
            except ValueError:
                st.error("Please enter valid numbers separated by spaces")
                return
        else:
            arr = []
    else:
        size = st.slider("Select array size:", 5, 100, 15)
        max_val = st.slider("Select maximum value:", 10, 1000, 100)
        arr = generate_random_array(size, max_val)

    if arr:
        st.subheader("Original Array")
        st.write(str(arr))
        st.write(f"Array size: {len(arr)}")

        if st.button("Sort Array", type="primary"):
            # Determine number of iterations based on array size
            iterations = min(1000, max(100, len(arr) * 2))
            
            if algorithm == "heap":
                execution_time, sorted_arr = measure_execution_time(heap_sort, arr.copy(), iterations=iterations)
            elif algorithm == "merge":
                execution_time, sorted_arr = measure_execution_time(merge_sort, arr.copy(), iterations=iterations)
            elif algorithm == "quick":
                execution_time, sorted_arr = measure_execution_time(quick_sort, arr.copy(), iterations=iterations)
            else:  # insertion
                execution_time, sorted_arr = measure_execution_time(insertion_sort, arr.copy(), iterations=iterations)
            
            st.subheader("Results")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Original Array", str(arr))
            with col2:
                st.metric("Sorted Array", str(sorted_arr))
            with col3:
                st.metric("Execution Time", f"{execution_time:.6f} ms")
            
            # Show iterations info for transparency
            st.info(f"⏱️ Timing based on {iterations:,} iterations for accuracy")
            
            if sorted_arr == sorted(arr):
                st.success("✅ Array successfully sorted!")
            else:
                st.error("❌ Error in sorting!")

def handle_searching():
    st.header("🔍 Searching Algorithms")
    
    algorithm = st.radio(
        "Select Search Algorithm:",
        ["linear", "binary", "interpolation"],
        format_func=lambda x: {"linear": "Linear Search", "binary": "Binary Search", "interpolation": "Interpolation Search"}[x],
        horizontal=True
    )

    input_method = st.radio("Choose input method:", ["Manual Input", "Random Array"], horizontal=True)

    if input_method == "Manual Input":
        user_input = st.text_input("Enter numbers separated by spaces:", placeholder="e.g., 1 2 3 4 5")
        if user_input:
            try:
                arr = [int(x) for x in user_input.split()]
            except ValueError:
                st.error("Please enter valid numbers separated by spaces")
                return
        else:
            arr = []
    else:
        size = st.slider("Select array size:", 5, 1000, 100)
        max_val = st.slider("Select maximum value:", 10, 10000, 1000)
        arr = generate_random_array(size, max_val)

    if arr:
        if algorithm in ["binary", "interpolation"]:
            arr = sorted(arr)
            st.info("Note: Array has been sorted for binary/interpolation search.")

        st.subheader("Array")
        st.write(str(arr))
        st.write(f"Array size: {len(arr)}")

        target = st.number_input("Enter target number to search:", value=arr[0] if arr else 0)

        if st.button("Search", type="primary"):
            # Determine number of iterations based on array size
            iterations = min(10000, max(1000, len(arr) * 10))
            
            if algorithm == "linear":
                execution_time, result = measure_execution_time(linear_search, arr, target, iterations=iterations)
            elif algorithm == "binary":
                execution_time, result = measure_execution_time(binary_search, arr, target, iterations=iterations)
            else:  # interpolation
                execution_time, result = measure_execution_time(interpolation_search, arr, target, iterations=iterations)
            
            st.subheader("Results")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Array Size", len(arr))
            with col2:
                st.metric("Target", str(target))
            with col3:
                st.metric("Execution Time", f"{execution_time:.6f} ms")
            
            # Show iterations info for transparency
            st.info(f"⏱️ Timing based on {iterations:,} iterations for accuracy")
            
            if result != -1:
                st.success(f"✅ Found {target} at index {result}")
            else:
                st.warning(f"❌ {target} not found in the array")

def handle_greedy():
    st.header("💰 Greedy Algorithms")
    
    algorithm = st.radio(
        "Select Greedy Algorithm:",
        ["huffman", "knapsack", "prims", "kruskals", "dijkstra"],
        format_func=lambda x: {"huffman": "Huffman Coding", "knapsack": "Fractional Knapsack", "prims": "Prim's MST", "kruskals": "Kruskal's MST", "dijkstra": "Dijkstra's Shortest Path"}[x],
        horizontal=True
    )

    if algorithm == "huffman":
        handle_huffman()
    elif algorithm == "knapsack":
        handle_knapsack()
    elif algorithm == "prims":
        handle_prims()
    elif algorithm == "kruskals":
        handle_kruskals()
    else:  # dijkstra
        handle_dijkstra()

def handle_huffman():
    st.subheader("Huffman Coding")
    
    input_method = st.radio("Choose input method:", ["Manual Input", "Sample Text"], horizontal=True)
    
    if input_method == "Manual Input":
        text = st.text_input("Enter text to compress:", placeholder="e.g., hello world")
    else:
        sample_texts = ["hello world", "algorithm visualization", "data structures and algorithms", "greedy algorithms are efficient"]
        text = st.selectbox("Select sample text:", sample_texts)
    
    if text:
        st.write(f"**Input Text:** {text}")
        st.write(f"**Text Length:** {len(text)} characters")
        
        if st.button("Compress Text", type="primary"):
            # Determine number of iterations based on text length
            iterations = min(100, max(10, len(text) // 10))
            
            result = huffman_compression(text)
            
            if "error" not in result:
                st.subheader("Compression Results")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Original Size", f"{result['original_size']} bits")
                with col2:
                    st.metric("Compressed Size", f"{result['compressed_size']} bits")
                with col3:
                    st.metric("Compression Ratio", f"{result['compression_ratio']:.2f}%")
                
                st.metric("Execution Time", f"{result['execution_time_ms']:.6f} ms")
                
                # Display character frequencies
                st.subheader("Character Frequencies")
                freq_data = {"Character": list(result['character_frequencies'].keys()), "Frequency": list(result['character_frequencies'].values())}
                st.bar_chart(freq_data)
                
                # Display Huffman codes
                st.subheader("Huffman Codes")
                codes_data = {"Character": list(result['huffman_codes'].keys()), "Code": list(result['huffman_codes'].values())}
                st.dataframe(codes_data)
                
                # Test decompression
                decomp_result = huffman_decompression(result['encoded_text'], result['tree_root'])
                st.subheader("Decompression Test")
                st.write(f"**Decoded Text:** {decomp_result['decoded_text']}")
                st.write(f"**Decompression Time:** {decomp_result['execution_time_ms']:.6f} ms")
                
                if decomp_result['decoded_text'] == text:
                    st.success("✅ Compression and decompression successful!")
                else:
                    st.error("❌ Decompression failed!")

def handle_knapsack():
    st.subheader("Fractional Knapsack")
    
    input_method = st.radio("Choose input method:", ["Manual Input", "Sample Data"], horizontal=True)
    
    if input_method == "Manual Input":
        col1, col2 = st.columns(2)
        with col1:
            weights_input = st.text_input("Weights (space-separated):", placeholder="e.g., 10 20 30")
        with col2:
            values_input = st.text_input("Values (space-separated):", placeholder="e.g., 60 100 120")
        
        capacity = st.number_input("Knapsack Capacity:", min_value=1, value=50)
        
        if weights_input and values_input:
            try:
                weights = [int(x) for x in weights_input.split()]
                values = [int(x) for x in values_input.split()]
            except ValueError:
                st.error("Please enter valid numbers")
                return
        else:
            weights, values = [], []
    else:
        num_items = st.slider("Number of items:", 3, 10, 5)
        max_weight = st.slider("Maximum weight:", 10, 100, 50)
        max_value = st.slider("Maximum value:", 20, 200, 100)
        capacity = st.slider("Knapsack capacity:", 20, 150, 50)
        
        weights, values, _ = generate_sample_data(num_items, max_weight, max_value, capacity)
    
    if weights and values:
        st.write("**Items:**")
        items_data = {"Item": [f"Item {i+1}" for i in range(len(weights))], "Weight": weights, "Value": values, "Value/Weight": [round(v/w, 2) for w, v in zip(weights, values)]}
        st.dataframe(items_data)
        st.write(f"**Knapsack Capacity:** {capacity}")
        
        if st.button("Solve Knapsack", type="primary"):
            # Determine number of iterations based on problem size
            iterations = min(100, max(10, len(weights) * 2))
            
            result = fractional_knapsack(weights, values, capacity)
            
            if "error" not in result:
                st.subheader("Solution")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Value", f"{result['total_value']:.2f}")
                with col2:
                    st.metric("Remaining Capacity", f"{result['remaining_capacity']:.2f}")
                with col3:
                    st.metric("Execution Time", f"{result['execution_time_ms']:.6f} ms")
                
                st.subheader("Selected Items")
                selected_data = {"Item": [f"Item {item['item_index']+1}" for item in result['selected_items']], 
                               "Original Weight": [item['original_weight'] for item in result['selected_items']],
                               "Original Value": [item['original_value'] for item in result['selected_items']],
                               "Fraction Taken": [f"{item['fraction_taken']:.2f}" for item in result['selected_items']],
                               "Weight Taken": [f"{item['weight_taken']:.2f}" for item in result['selected_items']],
                               "Value Taken": [f"{item['value_taken']:.2f}" for item in result['selected_items']]}
                st.dataframe(selected_data)

def handle_prims():
    st.subheader("Prim's Minimum Spanning Tree")
    
    num_vertices = st.slider("Number of vertices:", 3, 10, 5)
    density = st.slider("Graph density:", 0.3, 1.0, 0.7)
    max_weight = st.slider("Maximum edge weight:", 10, 200, 100)
    start_vertex = st.selectbox("Start vertex:", range(num_vertices))
    
    graph = generate_sample_graph(num_vertices, density, max_weight)
    
    st.write("**Graph (Adjacency Matrix):**")
    st.dataframe(graph)
    
    if st.button("Find MST", type="primary"):
        # Determine number of iterations based on graph size
        iterations = min(50, max(5, num_vertices))
        
        result = prims_mst(graph, start_vertex)
        
        if "error" not in result:
            st.subheader("Minimum Spanning Tree")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("MST Weight", result['mst_weight'])
            with col2:
                st.metric("Edges in MST", result['num_edges_in_mst'])
            with col3:
                st.metric("Execution Time", f"{result['execution_time_ms']:.6f} ms")
            
            st.subheader("MST Edges")
            edges_data = {"From": [edge['from'] for edge in result['mst_edges']], 
                         "To": [edge['to'] for edge in result['mst_edges']], 
                         "Weight": [edge['weight'] for edge in result['mst_edges']]}
            st.dataframe(edges_data)
            
            if result['is_connected']:
                st.success("✅ Connected graph - MST found!")
            else:
                st.warning("⚠️ Disconnected graph - partial MST found")

def handle_kruskals():
    st.subheader("Kruskal's Minimum Spanning Tree")
    
    num_vertices = st.slider("Number of vertices:", 3, 10, 5)
    density = st.slider("Graph density:", 0.3, 1.0, 0.7)
    max_weight = st.slider("Maximum edge weight:", 10, 200, 100)
    
    graph = generate_sample_graph(num_vertices, density, max_weight)
    
    st.write("**Graph (Adjacency Matrix):**")
    st.dataframe(graph)
    
    if st.button("Find MST", type="primary"):
        # Determine number of iterations based on graph size
        iterations = min(50, max(5, num_vertices))
        
        result = kruskals_mst(graph)
        
        if "error" not in result:
            st.subheader("Minimum Spanning Tree")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("MST Weight", result['mst_weight'])
            with col2:
                st.metric("Edges in MST", result['num_edges_in_mst'])
            with col3:
                st.metric("Execution Time", f"{result['execution_time_ms']:.6f} ms")
            
            st.subheader("MST Edges")
            edges_data = {"From": [edge['from'] for edge in result['mst_edges']], 
                         "To": [edge['to'] for edge in result['mst_edges']], 
                         "Weight": [edge['weight'] for edge in result['mst_edges']]}
            st.dataframe(edges_data)
            
            if result['is_connected']:
                st.success("✅ Connected graph - MST found!")
            else:
                st.warning("⚠️ Disconnected graph - partial MST found")

def handle_dijkstra():
    st.subheader("Dijkstra's Shortest Path")
    
    num_vertices = st.slider("Number of vertices:", 3, 10, 5)
    density = st.slider("Graph density:", 0.3, 1.0, 0.7)
    max_weight = st.slider("Maximum edge weight:", 10, 200, 100)
    start_vertex = st.selectbox("Source vertex:", range(num_vertices))
    
    graph = generate_sample_graph(num_vertices, density, max_weight)
    
    st.write("**Graph (Adjacency Matrix):**")
    st.dataframe(graph)
    
    if st.button("Find Shortest Path", type="primary"):
        # Determine number of iterations based on graph size
        iterations = min(50, max(5, num_vertices))
        
        result = dijkstras_shortest_path(graph, start_vertex)
        
        if "error" not in result:
            st.subheader("Shortest Path Results")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Start Vertex", start_vertex)
            with col2:
                st.metric("Execution Time", f"{result['execution_time_ms']:.6f} ms")
            with col3:
                st.metric("Reachable Vertices", result['reachable_count'])
            
            st.subheader("Shortest Distances")
            distances_data = {"Vertex": list(range(num_vertices)), 
                            "Distance": [result['distances'][i] if result['distances'][i] != float('inf') else "∞" for i in range(num_vertices)]}
            st.dataframe(distances_data)
            
            # Show path to a specific vertex
            target_vertex = st.selectbox("Show path to vertex:", range(num_vertices))
            if result['distances'][target_vertex] != float('inf'):
                path = result['paths'][target_vertex]
                st.write(f"**Path to vertex {target_vertex}:** {' → '.join(map(str, path))}")
                st.write(f"**Distance:** {result['distances'][target_vertex]}")
            else:
                st.write(f"**Vertex {target_vertex} is not reachable from {start_vertex}**")

def handle_dynamic():
    st.header("🔍 Dynamic Programming Algorithms")
    
    algorithm = st.radio(
        "Select Dynamic Programming Algorithm:",
        ["knapsack_01", "subset_sum", "coin_change"],
        format_func=lambda x: {"knapsack_01": "0/1 Knapsack", "subset_sum": "Subset Sum", "coin_change": "Coin Change"}[x],
        horizontal=True
    )

    if algorithm == "knapsack_01":
        handle_knapsack_01()
    elif algorithm == "subset_sum":
        handle_subset_sum()
    else:  # coin_change
        handle_coin_change()

def handle_knapsack_01():
    st.subheader("0/1 Knapsack")
    
    input_method = st.radio("Choose input method:", ["Manual Input", "Sample Data"], horizontal=True)
    
    if input_method == "Manual Input":
        col1, col2 = st.columns(2)
        with col1:
            weights_input = st.text_input("Weights (space-separated):", placeholder="e.g., 10 20 30")
        with col2:
            values_input = st.text_input("Values (space-separated):", placeholder="e.g., 60 100 120")
        
        capacity = st.number_input("Knapsack Capacity:", min_value=1, value=50)
        
        if weights_input and values_input:
            try:
                weights = [int(x) for x in weights_input.split()]
                values = [int(x) for x in values_input.split()]
            except ValueError:
                st.error("Please enter valid numbers")
                return
        else:
            weights, values = [], []
    else:
        num_items = st.slider("Number of items:", 3, 10, 5)
        max_weight = st.slider("Maximum weight:", 10, 100, 50)
        max_value = st.slider("Maximum value:", 20, 200, 100)
        capacity = st.slider("Knapsack capacity:", 20, 150, 50)
        
        weights, values, _ = generate_sample_data(num_items, max_weight, max_value, capacity)
    
    if weights and values:
        st.write("**Items:**")
        items_data = {"Item": [f"Item {i+1}" for i in range(len(weights))], "Weight": weights, "Value": values}
        st.dataframe(items_data)
        st.write(f"**Knapsack Capacity:** {capacity}")
        
        if st.button("Solve Knapsack", type="primary"):
            # Determine number of iterations based on problem size
            iterations = min(100, max(10, len(weights) * 2))
            
            # Get maximum value
            execution_time, max_value_result = measure_execution_time(knapsack_01_dp, weights, values, capacity, iterations=iterations)
            
            # Get selected items (single run for this)
            start_time = time.perf_counter()
            max_value_with_items, selected_indices = knapsack_01_get_items(weights, values, capacity)
            items_time = (time.perf_counter() - start_time) * 1000
            
            st.subheader("Solution")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Maximum Value", f"{max_value_result}")
            with col2:
                st.metric("Execution Time", f"{execution_time:.6f} ms")
            with col3:
                st.metric("Selected Items", len(selected_indices))
            
            # Show iterations info for transparency
            st.info(f"⏱️ Timing based on {iterations:,} iterations for accuracy")
            
            st.subheader("Selected Items")
            if selected_indices:
                selected_data = {
                    "Item": [f"Item {idx+1}" for idx in selected_indices],
                    "Weight": [weights[idx] for idx in selected_indices],
                    "Value": [values[idx] for idx in selected_indices]
                }
                st.dataframe(selected_data)
                
                total_weight = sum(weights[idx] for idx in selected_indices)
                st.write(f"**Total Weight Used:** {total_weight}/{capacity}")
                st.write(f"**Total Value:** {max_value_result}")
            else:
                st.info("No items selected")

def handle_subset_sum():
    st.subheader("Subset Sum")
    
    input_method = st.radio("Choose input method:", ["Manual Input", "Sample Data"], horizontal=True)
    
    target = None  # Initialize target
    numbers = []  # Initialize numbers
    
    if input_method == "Manual Input":
        col1, col2 = st.columns(2)
        with col1:
            numbers_input = st.text_input("Numbers (space-separated):", placeholder="e.g., 1 2 3 4 5")
        with col2:
            target = st.number_input("Target sum:", value=9)
        
        if numbers_input:
            try:
                numbers = [int(x) for x in numbers_input.split()]
            except ValueError:
                st.error("Please enter valid numbers")
                return
    else:
        size = st.slider("Select array size:", 5, 10, 5)
        max_val = st.slider("Select maximum value:", 1, 100, 50)
        numbers = generate_random_array(size, max_val)
        target = sum(numbers) // 2  # Use half the sum as target
    
    # Only display and process if we have valid data
    if numbers and target is not None:
        st.write("**Numbers:**")
        st.write(str(numbers))
        st.write(f"**Target Sum:** {target}")
        
        if st.button("Find Subset", type="primary"):
            # Determine number of iterations based on problem size
            iterations = min(100, max(10, len(numbers) * 2))
            
            # Check if subset exists
            execution_time, subset_exists = measure_execution_time(subset_sum_dp, numbers, target, iterations=iterations)
            
            # Get the actual subset if it exists (single run for this)
            start_time = time.perf_counter()
            exists, subset = subset_sum_get_subset(numbers, target)
            subset_time = (time.perf_counter() - start_time) * 1000
            
            st.subheader("Results")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Subset Exists", "Yes" if subset_exists else "No")
            with col2:
                st.metric("Execution Time", f"{execution_time:.6f} ms")
            with col3:
                st.metric("Subset Sum", sum(subset) if subset else 0)
            
            # Show iterations info for transparency
            st.info(f"⏱️ Timing based on {iterations:,} iterations for accuracy")
            
            if subset_exists and subset:
                st.success("✅ Subset found!")
                st.write(f"**Subset:** {subset}")
                st.write(f"**Subset Sum:** {sum(subset)}")
            else:
                st.warning("❌ No subset found")

def handle_coin_change():
    st.subheader("Coin Change")
    
    input_method = st.radio("Choose input method:", ["Manual Input", "Sample Data"], horizontal=True)
    
    amount = None  # Initialize amount
    
    if input_method == "Manual Input":
        col1, col2 = st.columns(2)
        with col1:
            coins_input = st.text_input("Coins (space-separated):", placeholder="e.g., 1 2 5")
        with col2:
            amount_input = st.number_input("Amount:", value=11)
        
        if coins_input:
            try:
                coins = [int(x) for x in coins_input.split()]
                amount = int(amount_input)
            except ValueError:
                st.error("Please enter valid numbers")
                return
        else:
            coins = []
    else:
        size = st.slider("Number of coin types:", 3, 8, 4)
        max_val = st.slider("Maximum coin value:", 1, 20, 10)
        coins = sorted(generate_random_array(size, max_val))
        amount = sum(coins) // 2  # Use half the sum as amount
    
    if coins and amount is not None:
        st.write("**Coins:**")
        st.write(str(coins))
        st.write(f"**Amount:** {amount}")
        
        if st.button("Find Minimum Coins", type="primary"):
            # Determine number of iterations based on problem size
            iterations = min(100, max(10, len(coins) * 2))
            
            # Find minimum coins needed
            execution_time, min_coins = measure_execution_time(coin_change_min_coins, coins, amount, iterations=iterations)
            
            # Count number of ways (single run for this)
            start_time = time.perf_counter()
            num_ways = coin_change_ways(coins, amount)
            ways_time = (time.perf_counter() - start_time) * 1000
            
            st.subheader("Solution")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Minimum Coins", f"{min_coins}" if min_coins != -1 else "Impossible")
            with col2:
                st.metric("Number of Ways", f"{num_ways}")
            with col3:
                st.metric("Execution Time", f"{execution_time:.6f} ms")
            
            # Show iterations info for transparency
            st.info(f"⏱️ Timing based on {iterations:,} iterations for accuracy")
            
            if min_coins != -1:
                st.success(f"✅ Can make {amount} with {min_coins} coins")
                st.write(f"**Total ways to make {amount}:** {num_ways}")
            else:
                st.error(f"❌ Cannot make {amount} with given coins")

if __name__ == "__main__":
    main() 