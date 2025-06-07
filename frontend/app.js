document.addEventListener('DOMContentLoaded', () => {
    const codeEditor = document.getElementById('codeEditor');
    const runButton = document.getElementById('runButton');
    const visualizeButton = document.getElementById('visualizeButton');
    const algorithmNameInput = document.getElementById('algorithmName');
    const languageSelect = document.getElementById('languageSelect');
    const currentRuntime = document.getElementById('currentRuntime');
    const outputDisplay = document.getElementById('outputDisplay');
    const algorithmSelect = document.getElementById('algorithmSelect');
    const runtimeChart = document.getElementById('runtimeChart');
    const modal = document.getElementById('visualizationModal');
    const closeButton = document.querySelector('.close');

    let chart = null;
    const API_BASE_URL = 'http://localhost:5000/api';

    // Check authentication
    function checkAuth() {
        const token = localStorage.getItem('token');
        if (!token) {
            window.location.href = 'login.html';
            return false;
        }
        return true;
    }

    // Initialize language select options
    if (languageSelect) {
        languageSelect.innerHTML = `
            <option value="c">C</option>
            <option value="cpp">C++</option>
        `;
    }

    // Show loading state
    function showLoading(button, text = 'Loading...') {
        if (button) {
            button.disabled = true;
            button.dataset.originalText = button.textContent;
            button.textContent = text;
        }
    }

    // Hide loading state
    function hideLoading(button) {
        if (button && button.dataset.originalText) {
            button.disabled = false;
            button.textContent = button.dataset.originalText;
        }
    }

    // Show error message
    function showError(message) {
        if (outputDisplay) {
            outputDisplay.innerHTML = `<div class="error">Error: ${message}</div>`;
        } else {
            alert(`Error: ${message}`);
        }
    }

    // Show success message
    function showSuccess(message) {
        if (outputDisplay) {
            outputDisplay.innerHTML = `<div class="success">${message}</div>`;
        }
    }

    // Initialize Chart.js
    function initChart() {
        if (!runtimeChart) return;
        
        const ctx = runtimeChart.getContext('2d');
        chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Runtime (ms)',
                    data: [],
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.1,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Runtime (ms)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Execution'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                }
            }
        });
    }

    // Update chart with new data
    function updateChart(runtimes) {
        if (!chart || !runtimes || runtimes.length === 0) return;
        
        const labels = runtimes.map((_, index) => `Run ${index + 1}`);
        const data = runtimes.map(runtime => runtime.runtime_ms);

        chart.data.labels = labels;
        chart.data.datasets[0].data = data;
        chart.update();
    }

    // Fetch runtime history
    async function fetchRuntimeHistory(algorithmName) {
        if (!algorithmName) return;
        
        try {
            const response = await fetch(
                `${API_BASE_URL}/visualization/runtimes?algorithm_name=${encodeURIComponent(algorithmName)}`,
                {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`,
                        'Content-Type': 'application/json'
                    }
                }
            );
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                updateChart(data.runtimes);
            } else {
                console.error('Failed to fetch runtime history:', data.error);
            }
        } catch (error) {
            console.error('Error fetching runtime history:', error);
            showError('Failed to fetch runtime history');
        }
    }

    // Fetch user's algorithms
    async function fetchAlgorithms() {
        if (!algorithmSelect) return;
        
        try {
            const response = await fetch(`${API_BASE_URL}/algorithms/list`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                algorithmSelect.innerHTML = '<option value="">Select Algorithm</option>';
                data.algorithms.forEach(algorithm => {
                    const option = document.createElement('option');
                    option.value = algorithm.name;
                    option.textContent = `${algorithm.name} (${algorithm.language.toUpperCase()})`;
                    algorithmSelect.appendChild(option);
                });
            } else {
                showError('Failed to load algorithms: ' + data.error);
            }
        } catch (error) {
            console.error('Error fetching algorithms:', error);
            showError('Failed to fetch algorithms');
        }
    }

    // Validate code input
    function validateCode(code, language) {
        if (!code || !code.trim()) {
            return 'Code cannot be empty';
        }
        
        // Basic validation for C/C++
        if (language === 'c' || language === 'cpp') {
            if (!code.includes('main')) {
                return 'Code must contain a main function';
            }
        }
        
        return null;
    }

    // Run algorithm
    async function runAlgorithm() {
        if (!checkAuth()) return;
        
        const code = codeEditor?.value?.trim();
        const algorithmName = algorithmNameInput?.value?.trim();
        const selectedLanguage = languageSelect?.value;

        // Validation
        if (!algorithmName) {
            showError('Please provide an algorithm name');
            return;
        }

        if (!selectedLanguage) {
            showError('Please select a programming language');
            return;
        }

        const codeValidation = validateCode(code, selectedLanguage);
        if (codeValidation) {
            showError(codeValidation);
            return;
        }

        showLoading(runButton, 'Running...');
        
        try {
            const response = await fetch(`${API_BASE_URL}/algorithms/run`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    code,
                    name: algorithmName,
                    language: selectedLanguage
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success) {
                if (currentRuntime) {
                    currentRuntime.textContent = `Last Runtime: ${data.runtime_ms.toFixed(2)}ms`;
                    currentRuntime.className = 'runtime-display success';
                }
                
                if (outputDisplay) {
                    const output = data.output || 'No output produced';
                    outputDisplay.innerHTML = `<div class="output">${output}</div>`;
                }
                
                showSuccess('Code executed successfully!');
            } else {
                showError(data.error || 'Unknown error occurred');
            }
        } catch (error) {
            console.error('Error running algorithm:', error);
            showError('Failed to execute code. Please check your internet connection and try again.');
        } finally {
            hideLoading(runButton);
        }
    }

    // Modal controls
    const isVisualizerPage = window.location.pathname.includes('visualizer.html');

    if (isVisualizerPage) {
        // Visualizer page specific code
        if (visualizeButton) {
            visualizeButton.addEventListener('click', () => {
                if (modal) {
                    modal.style.display = 'block';
                    fetchAlgorithms();
                    if (!chart) initChart();
                }
            });
        }

        if (closeButton) {
            closeButton.addEventListener('click', () => {
                if (modal) modal.style.display = 'none';
            });
        }

        window.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });

        if (algorithmSelect) {
            algorithmSelect.addEventListener('change', () => {
                if (algorithmSelect.value) {
                    fetchRuntimeHistory(algorithmSelect.value);
                }
            });
        }

        // Initialize for visualizer page
        if (checkAuth()) {
            fetchAlgorithms();
        }
    } else {
        // Code execution page specific code
        if (runButton) {
            runButton.addEventListener('click', runAlgorithm);
        }

        // Handle visualize button on main page
        if (visualizeButton) {
            visualizeButton.addEventListener('click', () => {
                window.location.href = 'visualizer.html';
            });
        }
        
        // Add keyboard shortcut for running code (Ctrl+Enter)
        if (codeEditor) {
            codeEditor.addEventListener('keydown', (e) => {
                if (e.ctrlKey && e.key === 'Enter') {
                    e.preventDefault();
                    runAlgorithm();
                }
            });
        }
    }

    // Common functionality
    const logoutButton = document.getElementById('logoutButton');
    if (logoutButton) {
        logoutButton.addEventListener('click', () => {
            localStorage.removeItem('token');
            window.location.href = 'login.html';
        });
    }

    // Display username if available
    const usernameSpan = document.getElementById('username');
    const userToken = localStorage.getItem('token');
    if (usernameSpan && userToken) {
        try {
            const payload = userToken.split('.')[1];
            const decodedToken = JSON.parse(atob(payload));
            usernameSpan.textContent = decodedToken.email || decodedToken.username || 'User';
        } catch (error) {
            console.error('Error decoding token:', error);
            usernameSpan.textContent = 'Guest';
        }
    }

    // Check authentication on page load
    if (!window.location.pathname.includes('login.html') && 
        !window.location.pathname.includes('register.html')) {
        checkAuth();
    }

    // Add some example code for first-time users
    if (codeEditor && !codeEditor.value) {
        const exampleCode = {
            'c': `#include <stdio.h>

int main() {
    printf("Hello, World!\\n");
    return 0;
}`,
            'cpp': `#include <iostream>
using namespace std;

int main() {
    cout << "Hello, World!" << endl;
    return 0;
}`
        };
        
        if (languageSelect) {
            const updateExample = () => {
                codeEditor.value = exampleCode[languageSelect.value] || exampleCode['c'];
            };
            
            languageSelect.addEventListener('change', updateExample);
            updateExample(); // Set initial example
        }
    }
});