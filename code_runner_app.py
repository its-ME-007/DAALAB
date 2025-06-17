import streamlit as st
from container_runner import ContainerRunner

st.set_page_config(
    page_title="Python Code Runner",
    page_icon="🐍",
    layout="wide"
)

st.title("🐍 Python Code Runner")

# Initialize session state for code persistence
if 'code' not in st.session_state:
    st.session_state.code = """# Your code here
# Example with fixed input
numbers = [1, 2, 3, 4, 5]
result = sum(numbers)

# Print the result
print(f"Sum of numbers: {result}")
"""

# Code editor
st.subheader("Python Code")
code = st.text_area(
    "Write your Python code here",
    value=st.session_state.code,
    height=400
)
st.session_state.code = code

# Run button
if st.button("▶️ Run Code", type="primary"):
    if not code.strip():
        st.error("Please enter some code to run!")
    else:
        try:
            with st.spinner("Running code..."):
                runner = ContainerRunner()
                output, runtime = runner.run_code(code)
                
                # Display results
                st.markdown("### Output")
                st.code(output, language="text")
                
                st.markdown("### Runtime")
                st.success(f"Code executed in {runtime:.3f} seconds")
                
                
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Add some helpful information
with st.expander("ℹ️ How to use"):
    st.markdown("""
    ### How to use:
    
    1. Write your Python code in the editor
    2. Include any input values directly in your code
    3. Click "Run Code" to execute
    
    ### Example Code:
    ```python
    # Example with fixed input
    numbers = [1, 2, 3, 4, 5]
    result = sum(numbers)
    
    # Print the result
    print(f"Sum of numbers: {result}")
    ```
    
    ### Notes:
    - Include all input values directly in your code
    - Use print statements to show output
    - The output will be displayed below the code
    """) 