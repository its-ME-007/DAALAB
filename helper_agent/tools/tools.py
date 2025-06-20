import os

def read_code(code: str) -> str:
    """
    Read the code and return the code in a readable format.
    """
    # Construct the path to code.py relative to this script's location
    # The agent.py is in helper_agent, and code.py is in the parent directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Go up one level from 'tools' to 'helper_agent'
    parent_dir_helper_agent = os.path.join(current_dir, os.pardir)
    
    # Go up another level from 'helper_agent' to 'attempy-daa' (the root)
    root_dir = os.path.join(parent_dir_helper_agent, os.pardir)
    
    # Now, construct the full path to code.py
    file_path = os.path.join(root_dir, 'code.py')

    try:
        with open(file_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        # You might want to print the attempted file_path here for debugging
        # print(f"Debug: Attempted to open: {file_path}")
        return "Error: code.py not found."
    except Exception as e:
        return f"An error occurred: {e}"