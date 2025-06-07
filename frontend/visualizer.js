document.addEventListener('DOMContentLoaded', () => {
    const algorithmSelect = document.getElementById('algorithmSelect');
    const runtimeChart = document.getElementById('runtimeChart');
    const executionHistory = document.getElementById('executionHistory');
    
    let chart = null;

    // Initialize Chart.js
    function initChart() {
        const ctx = runtimeChart.getContext('2d');
        chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Runtime (ms)',
                    data: [],
                    borderColor: '#3498db',
                    tension: 0.1
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
                            text: 'Run Number'
                        }
                    }
                }
            }
        });
    }

    // Update chart with new data
    function updateChart(runtimes) {
        const labels = runtimes.map((_, index) => `Run ${index + 1}`);
        const data = runtimes.map(runtime => runtime.runtime_ms);

        chart.data.labels = labels;
        chart.data.datasets[0].data = data;
        chart.update();
    }

    // Update execution history
    function updateExecutionHistory(executions) {
        executionHistory.innerHTML = executions.map(exec => `
            <div class="history-item">
                <div class="history-header">
                    <span class="runtime">${exec.runtime_ms.toFixed(2)}ms</span>
                    <span class="input-size">Input size: ${exec.input_size}</span>
                </div>
                <div class="history-output">${exec.output}</div>
            </div>
        `).join('');
    }

    // Fetch execution history
    async function fetchExecutionHistory(algorithmId) {
        try {
            const response = await fetch(
                `http://localhost:5000/api/visualization/executions?algorithm_id=${algorithmId}`,
                {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                }
            );
            const data = await response.json();
            
            if (data.success) {
                updateChart(data.executions);
                updateExecutionHistory(data.executions);
            }
        } catch (error) {
            console.error('Error fetching execution history:', error);
        }
    }

    // Fetch user's algorithms
    async function fetchAlgorithms() {
        try {
            const response = await fetch('http://localhost:5000/api/algorithms/list', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            const data = await response.json();
            
            if (data.success) {
                algorithmSelect.innerHTML = '<option value="">Select Algorithm</option>';
                data.algorithms.forEach(algorithm => {
                    const option = document.createElement('option');
                    option.value = algorithm.id;
                    option.textContent = algorithm.name;
                    algorithmSelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error fetching algorithms:', error);
        }
    }

    // Event listeners
    algorithmSelect.addEventListener('change', () => {
        if (algorithmSelect.value) {
            fetchExecutionHistory(algorithmSelect.value);
        }
    });

    // Initialize
    initChart();
    fetchAlgorithms();
}); 