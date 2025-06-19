/* =========================================================================
   📊  Algorithm Performance Visualization
   -------------------------------------------------------------------------
   Handles:
   1. Authentication and user session management
   2. Data fetching from API endpoints
   3. Chart creation and updates using Chart.js
   4. Performance statistics calculation
   5. Interactive filtering and chart type switching
   ========================================================================= */

(() => {
    /* -------------------------------------------------
       🔧  Global Variables
    ------------------------------------------------- */
    const API_BASE_URL = window.location.origin;
    const API_ENDPOINTS = {
        runtimeData: `${API_BASE_URL}/api/runtime-data`,
        runtimeSummary: `${API_BASE_URL}/api/runtime-summary`,
        logout: `${API_BASE_URL}/api/auth/logout`
    };

    let performanceChart = null;
    let allData = [];
    let summaryData = [];

    /* -------------------------------------------------
       🗺️  Auth helpers
    ------------------------------------------------- */
    const getToken = () => localStorage.getItem('token');
    const getUser = () => JSON.parse(localStorage.getItem('user') || 'null');
    const clearSession = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
    };

    const syncAuthUI = () => {
        const token = getToken();
        const user = getUser();
        const usernameDisplay = document.getElementById('username');
        const logoutButton = document.getElementById('logoutButton');

        if (token && user) {
            if (usernameDisplay) usernameDisplay.textContent = user.email;
            if (logoutButton) logoutButton.addEventListener('click', handleLogout);
        } else {
            window.location.replace('login.html');
        }
    };

    /* -------------------------------------------------
       🎬  MAIN: DOMContentLoaded
    ------------------------------------------------- */
    document.addEventListener('DOMContentLoaded', () => {
        syncAuthUI();
        
        // Initialize event listeners
        document.getElementById('refreshBtn')?.addEventListener('click', loadData);
        document.getElementById('algorithmFilter')?.addEventListener('change', updateChart);
        document.getElementById('chartType')?.addEventListener('change', updateChartType);
        
        // Load initial data
        loadData();
    });

    /* -------------------------------------------------
       📊  Data Loading Functions
    ------------------------------------------------- */
    async function loadData() {
        showLoading(true);
        
        try {
            // Load both detailed data and summary data
            const [runtimeData, summaryData] = await Promise.all([
                fetchRuntimeData(),
                fetchRuntimeSummary()
            ]);
            
            allData = runtimeData;
            summaryData = summaryData;
            
            updateStatistics();
            updateAlgorithmFilter();
            createChart();
            updateTable();
            
        } catch (error) {
            console.error('Error loading data:', error);
            showError('Failed to load visualization data');
        } finally {
            showLoading(false);
        }
    }

    async function fetchRuntimeData() {
        const response = await fetch(API_ENDPOINTS.runtimeData, {
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch runtime data');
        }
        
        const result = await response.json();
        return result.data || [];
    }

    async function fetchRuntimeSummary() {
        const response = await fetch(API_ENDPOINTS.runtimeSummary, {
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch summary data');
        }
        
        const result = await response.json();
        return result.data || [];
    }

    /* -------------------------------------------------
       📈  Statistics Functions
    ------------------------------------------------- */
    function updateStatistics() {
        const totalAlgorithms = document.getElementById('totalAlgorithms');
        const totalExecutions = document.getElementById('totalExecutions');
        const avgRuntime = document.getElementById('avgRuntime');
        const lastExecution = document.getElementById('lastExecution');

        if (allData.length === 0) {
            totalAlgorithms.textContent = '0';
            totalExecutions.textContent = '0';
            avgRuntime.textContent = '0ms';
            lastExecution.textContent = '-';
            return;
        }

        // Calculate statistics
        const uniqueAlgorithms = new Set(allData.map(item => item.algorithm_name)).size;
        const totalExecutionsCount = allData.length;
        const avgRuntimeMs = allData.reduce((sum, item) => sum + parseFloat(item.execution_time_ms), 0) / totalExecutionsCount;
        const lastExec = new Date(Math.max(...allData.map(item => new Date(item.created_at))));

        totalAlgorithms.textContent = uniqueAlgorithms;
        totalExecutions.textContent = totalExecutionsCount;
        avgRuntime.textContent = `${avgRuntimeMs.toFixed(1)}ms`;
        lastExecution.textContent = lastExec.toLocaleDateString();
    }

    /* -------------------------------------------------
       📊  Chart Functions
    ------------------------------------------------- */
    function createChart() {
        const ctx = document.getElementById('performanceChart');
        if (!ctx) return;

        // Destroy existing chart
        if (performanceChart) {
            performanceChart.destroy();
        }

        const chartData = prepareChartData();
        
        performanceChart = new Chart(ctx, {
            type: 'line',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Algorithm Performance: Runtime vs Input Size'
                    },
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ${context.parsed.y.toFixed(2)}ms`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Input Size'
                        },
                        type: 'linear'
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Runtime (ms)'
                        },
                        type: 'linear'
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });
    }

    function prepareChartData() {
        const algorithmFilter = document.getElementById('algorithmFilter')?.value;
        const filteredData = algorithmFilter ? 
            allData.filter(item => item.algorithm_name === algorithmFilter) : 
            allData;

        // Group data by algorithm
        const groupedData = {};
        filteredData.forEach(item => {
            if (!groupedData[item.algorithm_name]) {
                groupedData[item.algorithm_name] = [];
            }
            groupedData[item.algorithm_name].push({
                x: parseInt(item.input_size),
                y: parseFloat(item.execution_time_ms)
            });
        });

        // Sort data points by input size
        Object.keys(groupedData).forEach(algorithm => {
            groupedData[algorithm].sort((a, b) => a.x - b.x);
        });

        // Generate colors for algorithms
        const colors = [
            '#667eea', '#f56565', '#48bb78', '#ed8936', 
            '#9f7aea', '#38b2ac', '#ecc94b', '#ed64a6'
        ];

        const datasets = Object.keys(groupedData).map((algorithm, index) => ({
            label: algorithm,
            data: groupedData[algorithm],
            borderColor: colors[index % colors.length],
            backgroundColor: colors[index % colors.length] + '20',
            borderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6,
            tension: 0.1
        }));

        return { datasets };
    }

    function updateChart() {
        if (performanceChart) {
            const chartData = prepareChartData();
            performanceChart.data = chartData;
            performanceChart.update();
        }
    }

    function updateChartType() {
        const chartType = document.getElementById('chartType')?.value;
        if (performanceChart && chartType) {
            performanceChart.config.type = chartType;
            performanceChart.update();
        }
    }

    /* -------------------------------------------------
       🎛️  Filter Functions
    ------------------------------------------------- */
    function updateAlgorithmFilter() {
        const filter = document.getElementById('algorithmFilter');
        if (!filter) return;

        const algorithms = [...new Set(allData.map(item => item.algorithm_name))].sort();
        
        // Clear existing options except "All Algorithms"
        filter.innerHTML = '<option value="">All Algorithms</option>';
        
        algorithms.forEach(algorithm => {
            const option = document.createElement('option');
            option.value = algorithm;
            option.textContent = algorithm;
            filter.appendChild(option);
        });
    }

    /* -------------------------------------------------
       📋  Table Functions
    ------------------------------------------------- */
    function updateTable() {
        const tableBody = document.getElementById('tableBody');
        if (!tableBody) return;

        tableBody.innerHTML = '';

        if (summaryData.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="6" class="no-data">No performance data available</td></tr>';
            return;
        }

        summaryData.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${escapeHtml(item.algorithm_name)}</td>
                <td>${item.input_size.toLocaleString()}</td>
                <td>${item.max_execution_time_ms.toFixed(2)}ms</td>
                <td>${item.execution_count}</td>
                <td>${item.avg_execution_time_ms.toFixed(2)}ms</td>
                <td>${new Date().toLocaleDateString()}</td>
            `;
            tableBody.appendChild(row);
        });
    }

    /* -------------------------------------------------
       🔄  Utility Functions
    ------------------------------------------------- */
    function showLoading(show) {
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            loadingOverlay.classList.toggle('show', show);
        }
    }

    function showError(message) {
        alert(message);
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async function handleLogout() {
        try {
            await fetch(API_ENDPOINTS.logout, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${getToken()}` }
            });
        } catch (_) {
            // Ignore network errors on logout
        } finally {
            clearSession();
            window.location.replace('login.html');
        }
    }
})(); 