/* =========================================================================
   📊  Algorithm Performance Visualization
   -------------------------------------------------------------------------
   Handles:
   1. Authentication and user session management
   2. Backend plot loading and refresh
   3. Database entries display and refresh
   4. Loading states and error handling
   ========================================================================= */

(() => {
    /* -------------------------------------------------
       🔧  Global Variables
    ------------------------------------------------- */
    const API_BASE_URL = window.location.origin;
    const API_ENDPOINTS = {
        plot: `${API_BASE_URL}/api/plot.png`,
        runtimeData: `${API_BASE_URL}/api/runtime-data`,
        logout: `${API_BASE_URL}/api/auth/logout`
    };

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
        document.getElementById('refreshBtn')?.addEventListener('click', loadBackendPlot);
        document.getElementById('refreshEntriesBtn')?.addEventListener('click', loadDatabaseEntries);
        
        // Load initial data
        loadBackendPlot();
        loadDatabaseEntries();
    });

    /* -------------------------------------------------
       📊  Backend Plot Functions
    ------------------------------------------------- */
    async function loadBackendPlot() {
        showLoading(true);
        
        try {
            const token = getToken();
            const response = await fetch(API_ENDPOINTS.plot, {
                headers: {
                    'Authorization': 'Bearer ' + token
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to load plot');
            }
            
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            document.getElementById('backendPlot').src = url;
            
        } catch (error) {
            console.error('Error loading plot:', error);
            showError('Failed to load performance plot');
        } finally {
            showLoading(false);
        }
    }

    /* -------------------------------------------------
       📋  Database Entries Functions
    ------------------------------------------------- */
    async function loadDatabaseEntries() {
        try {
            const token = getToken();
            const response = await fetch(API_ENDPOINTS.runtimeData, {
                headers: {
                    'Authorization': 'Bearer ' + token
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to fetch database entries');
            }
            
            const result = await response.json();
            const entries = result.data || [];
            
            displayDatabaseEntries(entries);
            
        } catch (error) {
            console.error('Error loading database entries:', error);
            showError('Failed to load database entries');
        }
    }

    function displayDatabaseEntries(entries) {
        const entriesList = document.getElementById('entriesList');
        if (!entriesList) return;

        if (entries.length === 0) {
            entriesList.innerHTML = '<div class="no-entries">No database entries found</div>';
            return;
        }

        // Sort entries by creation date (newest first)
        entries.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

        entriesList.innerHTML = entries.map(entry => {
            const createdDate = new Date(entry.created_at);
            const formattedDate = createdDate.toLocaleDateString();
            const formattedTime = createdDate.toLocaleTimeString();
            
            return `
                <div class="entry-item">
                    <div class="entry-header">
                        <span class="entry-algorithm">${escapeHtml(entry.algorithm_name || 'Unknown')}</span>
                        <span class="entry-detail-value">${entry.execution_time_ms ? parseFloat(entry.execution_time_ms).toFixed(2) + 'ms' : 'N/A'}</span>
                    </div>
                    <div class="entry-details">
                        <div class="entry-detail">
                            <span class="entry-detail-label">Input Size:</span>
                            <span class="entry-detail-value">${entry.input_size ? entry.input_size.toLocaleString() : 'N/A'}</span>
                        </div>
                        <div class="entry-detail">
                            <span class="entry-detail-label">User ID:</span>
                            <span class="entry-detail-value">${entry.user_id ? entry.user_id.substring(0, 8) + '...' : 'N/A'}</span>
                        </div>
                    </div>
                    <div class="entry-time">
                        ${formattedDate} at ${formattedTime}
                    </div>
                </div>
            `;
        }).join('');
    }

    /* -------------------------------------------------
       🔄  Utility Functions
    ------------------------------------------------- */
    function showLoading(show) {
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            loadingOverlay.style.display = show ? 'flex' : 'none';
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