# 🐍 Python Code Runner

A secure Python code execution environment that runs code in isolated Docker containers. This project provides two different frontend interfaces for the same backend mechanism.

## Features

- **Secure Execution**: Code runs in isolated Docker containers
- **Real-time Output**: See execution results and runtime immediately
- **Modern UI**: Beautiful, responsive interface
- **Code Persistence**: Your code is automatically saved
- **Keyboard Shortcuts**: Use Ctrl+Enter to run code quickly
- **Error Handling**: Clear error messages and status indicators

## Two Frontend Options

### 1. Web Frontend (Recommended)
A modern, responsive web interface built with HTML, CSS, and JavaScript.

### 2. Streamlit Frontend
A Python-based web interface using Streamlit framework.

## Prerequisites

- Python 3.8+
- Docker installed and running
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd attempy-daa
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Make sure Docker is running on your system.

## Usage

### Option 1: Web Frontend (Recommended)

1. Start the FastAPI server:
```bash
python api_server.py
```

2. Open your browser and navigate to:
```
http://localhost:8000
```

3. Write your Python code in the editor and click "Run Code" or press Ctrl+Enter.

### Option 2: Streamlit Frontend

1. Start the Streamlit app:
```bash
streamlit run code_runner_app.py
```

2. The app will automatically open in your browser, or navigate to:
```
http://localhost:8501
```

## API Endpoints

The web frontend uses a REST API with the following endpoints:

- `GET /` - Serve the main HTML page
- `POST /api/run-code` - Execute Python code
- `GET /api/health` - Health check endpoint

## Example Code

Here are some examples you can try:

### Basic Operations
```python
# Simple calculation
x = 10
y = 20
print(f"Sum: {x + y}")
print(f"Product: {x * y}")
```

### List Operations
```python
# List comprehensions
numbers = [1, 2, 3, 4, 5]
squares = [n**2 for n in numbers]
print(f"Squares: {squares}")

# Filter even numbers
evens = [n for n in numbers if n % 2 == 0]
print(f"Even numbers: {evens}")
```

### Functions
```python
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

print(f"Factorial of 5: {factorial(5)}")
```

### Classes
```python
class Calculator:
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result

calc = Calculator()
print(f"5 + 3 = {calc.add(5, 3)}")
```

## Project Structure

```
attempy-daa/
├── api_server.py          # FastAPI server for web frontend
├── code_runner_app.py     # Streamlit frontend
├── container_runner.py    # Core backend (Docker execution)
├── requirements.txt       # Python dependencies
├── static/               # Web frontend files
│   ├── index.html        # Main HTML page
│   ├── styles.css        # CSS styles
│   └── script.js         # JavaScript functionality
└── README.md            # This file
```

## Security Features

- **Container Isolation**: Each code execution runs in a separate Docker container
- **Resource Limits**: Containers are automatically removed after execution
- **No Network Access**: Containers run without network access by default
- **Timeouts**: Execution is limited to prevent infinite loops

## Customization

### Adding New Examples
You can add more example code by modifying the `addExampleCode` function in `static/script.js`.

### Styling
The web frontend uses CSS custom properties and can be easily customized by modifying `static/styles.css`.

### Backend Configuration
The `ContainerRunner` class in `container_runner.py` can be modified to:
- Use different Python versions
- Add more security restrictions
- Implement resource limits
- Add support for other programming languages

## Troubleshooting

### Docker Issues
- Make sure Docker is running: `docker --version`
- Check if you have permission to run Docker commands
- On Windows/macOS, ensure Docker Desktop is running

### Port Conflicts
- Web frontend uses port 8000 by default
- Streamlit uses port 8501 by default
- Change ports in the respective files if needed

### Code Execution Errors
- Check that your Python syntax is correct
- Ensure all required imports are included
- Remember that input() functions won't work (use fixed values instead)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test both frontends
5. Submit a pull request

## Support

If you encounter any issues:
1. Check the troubleshooting section
2. Ensure all prerequisites are met
3. Try running the code locally first
4. Open an issue with detailed error information 