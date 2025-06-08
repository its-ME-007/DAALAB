import streamlit as st
import json
import requests
from heap_sort import generate_random_array

# API endpoint
API_URL = "http://localhost:8000/sort"

def get_algorithm_info(algorithm):
    """Return algorithm-specific information"""
    if algorithm == "heap":
        return {
            "name": "Heap Sort",
            "time_complexity": "O(n log n)",
            "space_complexity": "O(1)",
            "description": "A comparison-based sorting algorithm that uses a binary heap data structure."
        }
    elif algorithm == "merge":
        return {
            "name": "Merge Sort",
            "time_complexity": "O(n log n)",
            "space_complexity": "O(n)",
            "description": "A divide-and-conquer algorithm that recursively breaks down the problem into smaller subproblems."
        }
    elif algorithm == "quick":
        return {
            "name": "Quick Sort",
            "time_complexity": "O(n log n) average, O(n²) worst",
            "space_complexity": "O(log n)",
            "description": "A divide-and-conquer algorithm that picks an element as pivot and partitions the array around it."
        }
    else:
        return {
            "name": "Insertion Sort",
            "time_complexity": "O(n²)",
            "space_complexity": "O(1)",
            "description": "A simple sorting algorithm that builds the final sorted array one item at a time. Efficient for small data sets and nearly sorted arrays."
        }

def main():
    st.set_page_config(
        page_title="Sorting Algorithms Visualizer",
        page_icon="📊",
        layout="centered"
    )

    st.title("🔧 Sorting Algorithms Visualizer")
    st.markdown("---")

    # Algorithm selection
    algorithm = st.radio(
        "Select Sorting Algorithm:",
        ["heap", "merge", "quick", "insertion"],
        format_func=lambda x: {
            "heap": "Heap Sort",
            "merge": "Merge Sort",
            "quick": "Quick Sort",
            "insertion": "Insertion Sort"
        }[x],
        horizontal=True
    )

    # Display algorithm info
    algo_info = get_algorithm_info(algorithm)
    with st.expander("Algorithm Information"):
        st.markdown(f"""
        **Algorithm:** {algo_info['name']}  
        **Time Complexity:** {algo_info['time_complexity']}  
        **Space Complexity:** {algo_info['space_complexity']}  
        **Description:** {algo_info['description']}
        """)

    # Input section
    st.subheader("Input")
    input_method = st.radio(
        "Choose input method:",
        ["Manual Input", "Random Array"],
        horizontal=True
    )

    if input_method == "Manual Input":
        user_input = st.text_input(
            "Enter numbers separated by spaces:",
            placeholder="e.g., 5 2 8 1 9"
        )
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
        # Display original array
        st.subheader("Original Array")
        st.write(arr)
        st.write(f"Array size: {len(arr)}")

        # Sort button
        if st.button("Sort Array", type="primary"):
            try:
                # Send request to API
                response = requests.post(API_URL, json={
                    "array": arr,
                    "algorithm": algorithm
                })
                response.raise_for_status()
                result = response.json()
                
                # Display results
                st.subheader("Results")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Original Array", str(result["original_array"]))
                with col2:
                    st.metric("Sorted Array", str(result["sorted_array"]))
                
                # Display execution time
                st.metric(
                    "Execution Time",
                    f"{result['execution_time_ms']:.5f} ms",
                    delta=None
                )
                
                # Verify sort
                if result["is_sorted"]:
                    st.success(f"✅ Array successfully sorted using {result['algorithm']}!")
                else:
                    st.error("❌ Error in sorting!")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to sorting service: {str(e)}")
                st.info("Make sure the Docker container is running and accessible at http://localhost:8000")

if __name__ == "__main__":
    main() 