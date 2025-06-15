import streamlit as st
import json
import requests
from sort.heap_sort import generate_random_array

# API endpoints
SORT_API_URL = "http://localhost:8000/sort"
SEARCH_API_URL = "http://localhost:8001/search"

def get_algorithm_info(algorithm, mode="sort"):
    """Return algorithm-specific information"""
    if mode == "sort":
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
    else:  # search mode
        if algorithm == "linear":
            return {
                "name": "Linear Search",
                "time_complexity": "O(n)",
                "space_complexity": "O(1)",
                "description": "A simple search algorithm that checks each element in sequence until the target is found."
            }
        elif algorithm == "binary":
            return {
                "name": "Binary Search",
                "time_complexity": "O(log n)",
                "space_complexity": "O(1)",
                "description": "An efficient search algorithm that works on sorted arrays by repeatedly dividing the search interval in half."
            }
        else:
            return {
                "name": "Interpolation Search",
                "time_complexity": "O(log log n) average, O(n) worst",
                "space_complexity": "O(1)",
                "description": "An improvement over binary search for uniformly distributed sorted arrays, using position estimation."
            }

def main():
    st.set_page_config(
        page_title="Algorithm Visualizer",
        page_icon="🔍",
        layout="centered"
    )

    st.title("🔍 Algorithm Visualizer")
    st.markdown("---")

    # Mode selection
    mode = st.radio(
        "Select Mode:",
        ["sort", "search"],
        format_func=lambda x: "Sorting" if x == "sort" else "Searching",
        horizontal=True
    )

    if mode == "sort":
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
        algo_info = get_algorithm_info(algorithm, "sort")
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
            st.write(str(arr))
            st.write(f"Array size: {len(arr)}")

            # Sort button
            if st.button("Sort Array", type="primary"):
                try:
                    # Send request to API
                    response = requests.post(SORT_API_URL, json={
                        "array": arr,
                        "algorithm": algorithm
                    })
                    response.raise_for_status()
                    result = response.json()
                    
                    # Display results
                    st.subheader("Results")
                    
                    st.metric("Original Array", str(result["original_array"]))
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

    else:  # search mode
        # Algorithm selection
        algorithm = st.radio(
            "Select Search Algorithm:",
            ["linear", "binary", "interpolation"],
            format_func=lambda x: {
                "linear": "Linear Search",
                "binary": "Binary Search",
                "interpolation": "Interpolation Search"
            }[x],
            horizontal=True
        )

        # Display algorithm info
        algo_info = get_algorithm_info(algorithm, "search")
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
                placeholder="e.g., 1 2 3 4 5"
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
            # For binary and interpolation search, ensure array is sorted
            # This is now handled by the backend search service.
            # st.warning("Note: Binary and Interpolation search require a sorted array. Please provide a sorted array for these algorithms.")
            # if not all(arr[i] <= arr[i+1] for i in range(len(arr)-1)):
            #     st.error("The array is not sorted. Please provide a sorted array for binary/interpolation search.")
            #     return

            # Display array
            st.subheader("Array")
            st.write(str(arr))
            st.write(f"Array size: {len(arr)}")

            # Target input
            target = st.number_input("Enter target number to search:", value=arr[0] if arr else 0)

            # Search button
            if st.button("Search", type="primary"):
                try:
                    # Send request to API
                    response = requests.post(SEARCH_API_URL, json={
                        "array": arr,
                        "target": target,
                        "algorithm": algorithm
                    })
                    response.raise_for_status()
                    result = response.json()
                    
                    # Display results
                    st.subheader("Results")
                    
                    st.metric("Array", str(result["array"]))
                    st.metric("Target", str(result["target"]))
                    
                    # Display execution time
                    st.metric(
                        "Execution Time",
                        f"{result['execution_time_ms']:.5f} ms",
                        delta=None
                    )
                    
                    # Display search result
                    if result.get("found_index") is not None:
                        st.success(result.get("message", "Search successful."))
                    else:
                        st.warning(result.get("message", "Target not found."))
                        
                except requests.exceptions.RequestException as e:
                    st.error(f"Error connecting to search service: {str(e)}")
                    st.info("Make sure the Docker container is running and accessible at http://localhost:8001")
                except json.JSONDecodeError:
                    st.error("Received an unreadable response from the search service.")
                    st.info("Please ensure the search service is running correctly and returning valid JSON.")
                except KeyError as e:
                    st.error(f"An unexpected error occurred: Missing key in response - {e}")
                    st.info("The search service might be returning an unexpected format.")

if __name__ == "__main__":
    main() 