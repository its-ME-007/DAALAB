// DOM elements
const codeEditor = document.getElementById('codeEditor');
const runBtn = document.getElementById('runBtn');
const clearBtn = document.getElementById('clearBtn');
const output = document.getElementById('output');
const statusIndicator = document.getElementById('statusIndicator');
const statusDot = statusIndicator.querySelector('.status-dot');
const statusText = statusIndicator.querySelector('.status-text');
const loadingOverlay = document.getElementById('loadingOverlay');

// API configuration
const API_BASE_URL = window.location.origin;
const API_ENDPOINTS = {
    runCode: '/api/run-code',
    health: '/api/health'
};

// State management
let isRunning = false;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Add event listeners
    runBtn.addEventListener('click', runCode);
    clearBtn.addEventListener('click', clearEditor);
    
    // Add keyboard shortcuts
    codeEditor.addEventListener('keydown', function(e) {
        // Ctrl+Enter or Cmd+Enter to run code
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            runCode();
        }
        
        // Tab key handling for indentation
        if (e.key === 'Tab') {
            e.preventDefault();
            insertAtCursor('\t');
        }
    });
    
    // Auto-resize textarea
    codeEditor.addEventListener('input', autoResize);
    
    // Check API health on load
    checkApiHealth();
    
    // Load saved code from localStorage if available
    loadSavedCode();
}

// API functions
async function runCode() {
    if (isRunning) return;
    
    const code = codeEditor.value.trim();
    if (!code) {
        showError('Please enter some code to run!');
        return;
    }
    
    setRunningState(true);
    showLoading(true);
    
    try {
        const response = await fetch(API_ENDPOINTS.runCode, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ code })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            displayResult(result);
        } else {
            showError(result.detail || 'Failed to run code');
        }
        
    } catch (error) {
        console.error('Error running code:', error);
        showError('Network error: Unable to connect to the server');
    } finally {
        setRunningState(false);
        showLoading(false);
    }
}

async function checkApiHealth() {
    try {
        const response = await fetch(API_ENDPOINTS.health);
        if (response.ok) {
            setStatus('ready', 'Ready');
        } else {
            setStatus('error', 'API Error');
        }
    } catch (error) {
        setStatus('error', 'Offline');
    }
}

// UI functions
function displayResult(result) {
    if (result.success) {
        const outputContent = result.output || 'No output generated';
        const runtimeInfo = `Execution time: ${result.runtime.toFixed(3)} seconds`;
        
        output.innerHTML = `
            <div class="output-success">${escapeHtml(outputContent)}</div>
            <div class="runtime-info">${runtimeInfo}</div>
        `;
        
        setStatus('ready', 'Completed');
    } else {
        showError(result.error || 'Unknown error occurred');
    }
}

function showError(message) {
    output.innerHTML = `<div class="output-error">Error: ${escapeHtml(message)}</div>`;
    setStatus('error', 'Error');
}

function setRunningState(running) {
    isRunning = running;
    runBtn.disabled = running;
    runBtn.innerHTML = running ? 
        '<i class="fas fa-spinner fa-spin"></i> Running...' : 
        '<i class="fas fa-play"></i> Run Code';
}

function setStatus(type, text) {
    statusDot.className = `status-dot ${type}`;
    statusText.textContent = text;
}

function showLoading(show) {
    if (show) {
        loadingOverlay.classList.add('show');
    } else {
        loadingOverlay.classList.remove('show');
    }
}

function clearEditor() {
    if (confirm('Are you sure you want to clear the editor?')) {
        codeEditor.value = '';
        output.innerHTML = `
            <div class="welcome-message">
                <i class="fas fa-info-circle"></i>
                <p>Write your Python code and click "Run Code" to execute it.</p>
            </div>
        `;
        setStatus('ready', 'Ready');
        autoResize();
        saveCode();
    }
}

function autoResize() {
    codeEditor.style.height = 'auto';
    codeEditor.style.height = Math.max(400, codeEditor.scrollHeight) + 'px';
}

function insertAtCursor(text) {
    const start = codeEditor.selectionStart;
    const end = codeEditor.selectionEnd;
    const value = codeEditor.value;
    
    codeEditor.value = value.substring(0, start) + text + value.substring(end);
    codeEditor.selectionStart = codeEditor.selectionEnd = start + text.length;
    codeEditor.focus();
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function saveCode() {
    try {
        localStorage.setItem('pythonCodeRunner_code', codeEditor.value);
    } catch (error) {
        console.warn('Could not save code to localStorage:', error);
    }
}

function loadSavedCode() {
    try {
        const savedCode = localStorage.getItem('pythonCodeRunner_code');
        if (savedCode) {
            codeEditor.value = savedCode;
            autoResize();
        }
    } catch (error) {
        console.warn('Could not load code from localStorage:', error);
    }
}

// Auto-save code when user stops typing
let saveTimeout;
codeEditor.addEventListener('input', function() {
    clearTimeout(saveTimeout);
    saveTimeout = setTimeout(saveCode, 1000);
});

// Handle page visibility changes
document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'visible') {
        checkApiHealth();
    }
});

// Handle window resize
window.addEventListener('resize', function() {
    autoResize();
});

// Add some helpful features
function addExampleCode(example) {
    const examples = {
        'hello': `# Hello World
print("Hello, World!")
print("Welcome to Python Code Runner!")`,

        'math': `# Mathematical operations
import math

# Basic arithmetic
a = 10
b = 5
print(f"Addition: {a + b}")
print(f"Subtraction: {a - b}")
print(f"Multiplication: {a * b}")
print(f"Division: {a / b}")
print(f"Power: {a ** b}")

# Math functions
print(f"Square root of {a}: {math.sqrt(a)}")
print(f"Pi: {math.pi}")`,

        'lists': `# List operations
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# Basic list operations
print(f"Original list: {numbers}")
print(f"Length: {len(numbers)}")
print(f"Sum: {sum(numbers)}")
print(f"Average: {sum(numbers) / len(numbers)}")

# List comprehensions
squares = [n**2 for n in numbers]
print(f"Squares: {squares}")

# Filter even numbers
evens = [n for n in numbers if n % 2 == 0]
print(f"Even numbers: {evens}")`,

        'functions': `# Function examples
def greet(name):
    return f"Hello, {name}!"

def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Test functions
print(greet("Python"))
print(f"Factorial of 5: {factorial(5)}")
print(f"Fibonacci(10): {fibonacci(10)}")`,

        'classes': `# Class example
class Calculator:
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def multiply(self, a, b):
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result
    
    def get_history(self):
        return self.history

# Create calculator instance
calc = Calculator()
print(f"5 + 3 = {calc.add(5, 3)}")
print(f"4 * 7 = {calc.multiply(4, 7)}")
print("History:", calc.get_history())`
    };
    
    if (examples[example]) {
        codeEditor.value = examples[example];
        autoResize();
        saveCode();
    }
}

// Add example buttons to the UI (optional enhancement)
function addExampleButtons() {
    const examples = ['hello', 'math', 'lists', 'functions', 'classes'];
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'example-buttons';
    buttonContainer.style.cssText = `
        display: flex;
        gap: 10px;
        margin-bottom: 15px;
        flex-wrap: wrap;
    `;
    
    examples.forEach(example => {
        const btn = document.createElement('button');
        btn.className = 'btn btn-secondary';
        btn.style.fontSize = '0.8rem';
        btn.style.padding = '8px 16px';
        btn.textContent = example.charAt(0).toUpperCase() + example.slice(1);
        btn.onclick = () => addExampleCode(example);
        buttonContainer.appendChild(btn);
    });
    
    const editorSection = document.querySelector('.editor-section');
    editorSection.insertBefore(buttonContainer, editorSection.firstChild);
}

// Uncomment the line below to add example buttons
// addExampleButtons(); 