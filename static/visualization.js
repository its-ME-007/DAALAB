/* =========================================================================
   📊  Algorithm Performance Visualization with Complexity Analysis
   ========================================================================= */

(() => {
    /* -------------------------------------------------
       🔧  Global Variables
    ------------------------------------------------- */
    const API_BASE_URL = window.location.origin;
    const API_ENDPOINTS = {
        plot: `${API_BASE_URL}/api/plot.png`,
        complexityPlot: `${API_BASE_URL}/api/complexity-plot.png`,
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
        document.getElementById('refreshBtn')?.addEventListener('click', () => {
            loadBackendPlot();
            loadComplexityPlots();
        });
        document.getElementById('refreshEntriesBtn')?.addEventListener('click', loadDatabaseEntries);
        
        // Load all data
        loadComplexityPlots();  // Load complexity first (if available)
        loadBackendPlot();      // Then load runtime plot
        loadDatabaseEntries();  // Finally load database entries
    });

    /* -------------------------------------------------
       📊  Complexity Analysis Functions
    ------------------------------------------------- */
    async function loadComplexityPlots() {
        // Check if we have complexity analysis data from compiler page
        const complexityData = localStorage.getItem('lastComplexityAnalysis');
        
        if (!complexityData) {
            console.log('No complexity analysis data found - skipping complexity plots');
            return;
        }
        
        try {
            const data = JSON.parse(complexityData);
            console.log('Loading complexity plots for:', data);
            
            // Display complexity info card at the top
            displayComplexityInfo(data);
            
            // Load complexity plot (time and space graphs)
            await loadComplexityPlot(data);
            
        } catch (error) {
            console.error('Error loading complexity plots:', error);
        }
    }

    // Update the displayComplexityInfo function in visualization.js:

function displayComplexityInfo(data) {
    const languageIcon = data.language === 'cpp' ? '🔧' : '🐍';
    const languageName = data.language === 'cpp' ? 'C++' : 'Python';
    
    const infoHTML = `
        <div class="complexity-info-section" style="background: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 1.5rem; border: 2px solid #e6f2ff; max-width: 1200px; margin-left: auto; margin-right: auto;">
            <h3 style="color: #667eea; margin: 0 0 1rem 0; font-size: 1.4rem; display: flex; align-items: center; gap: 0.5rem;">
                <i class="fas fa-brain"></i> Latest Complexity Analysis ${languageIcon} ${languageName}
            </h3>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
                <!-- Time Complexity Card -->
                <div style="background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%); padding: 1rem; border-radius: 10px; border: 2px solid #667eea;">
                    <div style="font-size: 0.75rem; color: #718096; margin-bottom: 0.5rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">
                        ⏱️ Time
                    </div>
                    <div style="font-size: 2rem; font-weight: bold; color: #667eea; margin-bottom: 0.25rem;">
                        ${data.time_complexity}
                    </div>
                    <div style="font-size: 0.75rem; color: #4a5568; text-transform: uppercase; font-weight: 600;">
                        ${data.time_class}
                    </div>
                </div>
                
                <!-- Space Complexity Card -->
                <div style="background: linear-gradient(135deg, #f093fb15 0%, #f5576c15 100%); padding: 1rem; border-radius: 10px; border: 2px solid #f093fb;">
                    <div style="font-size: 0.75rem; color: #718096; margin-bottom: 0.5rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">
                        💾 Space
                    </div>
                    <div style="font-size: 2rem; font-weight: bold; color: #f093fb; margin-bottom: 0.25rem;">
                        ${data.space_complexity}
                    </div>
                    <div style="font-size: 0.75rem; color: #4a5568; text-transform: uppercase; font-weight: 600;">
                        ${data.space_class}
                    </div>
                </div>
            </div>
            
            ${data.algorithm_name && data.algorithm_name !== 'Unknown Algorithm' ? `
                <div style="margin-bottom: 0.75rem; padding: 0.75rem; background: #f7fafc; border-radius: 8px; border-left: 3px solid #48bb78; font-size: 0.9rem;">
                    <strong style="color: #2d3748;">🔍 Algorithm:</strong> 
                    <span style="color: #48bb78; font-weight: 600;">${data.algorithm_name}</span>
                    <span style="color: #718096; font-size: 0.85rem; margin-left: 0.5rem;">(${languageName})</span>
                </div>
            ` : ''}
            
            <div style="padding: 0.875rem; background: #f7fafc; border-radius: 8px; border-left: 3px solid #667eea;">
                <strong style="color: #2d3748; display: block; margin-bottom: 0.5rem; font-size: 0.9rem;">📝 Explanation:</strong>
                <p style="margin: 0; line-height: 1.6; color: #4a5568; font-size: 0.875rem;">
                    ${data.explanation}
                </p>
            </div>
        </div>
    `;
    
    // Insert at the very top of main content
    const mainContent = document.querySelector('.main-content') || document.querySelector('main');
    if (mainContent) {
        mainContent.insertAdjacentHTML('afterbegin', infoHTML);
    }
}

    async function loadComplexityPlot(data) {
        try {
            showLoading(true);
            
            const token = getToken();
            const url = `${API_ENDPOINTS.complexityPlot}?time_class=${data.time_class}&space_class=${data.space_class}&algorithm_name=${encodeURIComponent(data.algorithm_name || 'Algorithm')}`;
            
            console.log('Fetching complexity plot from:', url);
            
            const response = await fetch(url, {
                headers: {
                    'Authorization': 'Bearer ' + token
                }
            });
            
            if (!response.ok) {
                throw new Error(`Failed to load complexity plot: ${response.status}`);
            }
            
            const blob = await response.blob();
            const imageUrl = URL.createObjectURL(blob);
            
            // Create a new plot container for complexity
            const complexityPlotHTML = `
                <div class="chart-section" style="margin-bottom: 2rem;">
                    <div class="section-header">
                        <h2><i class="fas fa-chart-area"></i> Theoretical Complexity Visualization</h2>
                        <div style="font-size: 0.875rem; color: #718096; font-weight: normal;">
                            Based on AI analysis of your code
                        </div>
                    </div>
                    <div class="plot-container">
                        <img id="complexityPlot" src="${imageUrl}" alt="Complexity Analysis" style="max-width:100%; border-radius:12px; box-shadow: 0 4px 16px rgba(0,0,0,0.12); border: 1px solid #e2e8f0;">
                        <div class="plot-info" style="margin-top: 1rem; padding: 1rem; background: #edf2f7; border-radius: 8px; border-left: 4px solid #667eea;">
                            <p style="margin: 0; color: #4a5568; font-size: 0.9rem; line-height: 1.6;">
                                <i class="fas fa-info-circle" style="color: #667eea;"></i> 
                                These graphs show theoretical time and space complexity curves based on Big-O notation. 
    You can now see the TRUE curve shapes: quadratic (O(n²)) shows as a parabola, 
    cubic (O(n³)) shows as a steep curve, linear (O(n)) is a straight diagonal line.
                            </p>
                        </div>
                    </div>
                </div>
            `;
            
            // Insert after complexity info card
            const infoSection = document.querySelector('.complexity-info-section');
            if (infoSection) {
                infoSection.insertAdjacentHTML('afterend', complexityPlotHTML);
            }
            
            console.log('✅ Complexity plot loaded successfully');
            
        } catch (error) {
            console.error('❌ Error loading complexity plot:', error);
            showError('Failed to load complexity graphs. Try analyzing code again.');
        } finally {
            showLoading(false);
        }
    }

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
            
            const plotImg = document.getElementById('backendPlot');
            if (plotImg) {
                plotImg.src = url;
            }
            
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
        console.error(message);
        // Could add a toast notification here
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