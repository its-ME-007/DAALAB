import streamlit as st
import json
import requests
from heap_sort import generate_random_array

# API endpoint
API_URL = "http://localhost:8000/sort"

def main():
    st.set_page_config(
        page_title="Heap Sort Visualizer",
        page_icon="📊",
        layout="centered"
    )

    st.title("🔧 Heap Sort Algorithm Visualizer")
    st.markdown("---")

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
                response = requests.post(API_URL, json={"array": arr})
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
                
                # Display algorithm info
                st.subheader("Algorithm Information")
                st.markdown("""
                **Time Complexity:** O(n log n)  
                **Space Complexity:** O(1)  
                **Type:** Comparison-based sorting algorithm
                """)
                
                # Verify sort
                if result["is_sorted"]:
                    st.success("✅ Array successfully sorted!")
                else:
                    st.error("❌ Error in sorting!")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to sorting service: {str(e)}")
                st.info("Make sure the Docker container is running and accessible at http://localhost:8000")

if __name__ == "__main__":
    main() 