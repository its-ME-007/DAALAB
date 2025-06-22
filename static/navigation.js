/**
 * Unified Navigation and Authentication System
 * Provides consistent navigation and authentication across all modules
 */

class UnifiedNavigation {
    constructor() {
        this.token = localStorage.getItem('token');
        this.user = JSON.parse(localStorage.getItem('user') || 'null');
        this.currentPage = window.location.pathname.split('/').pop() || 'index.html';
    }

    // Initialize navigation and authentication
    init() {
        this.checkAuthentication();
        this.setupNavigation();
        this.setupLogout();
    }

    // Check authentication status
    checkAuthentication() {
        if (!this.token || !this.user) {
            window.location.href = '/login.html';
            return false;
        }
        return true;
    }

    // Setup navigation links
    setupNavigation() {
        const usernameElement = document.getElementById('username');
        if (usernameElement) {
            usernameElement.textContent = this.user.email || 'User';
        }
    }

    // Setup logout functionality
    setupLogout() {
        const logoutButton = document.getElementById('logoutButton');
        if (logoutButton) {
            logoutButton.addEventListener('click', () => {
                localStorage.removeItem('token');
                localStorage.removeItem('user');
                window.location.href = '/login.html';
            });
        }
    }

    // Get navigation links for current page
    getNavigationLinks() {
        const links = [
            {
                href: '/compiler.html',
                icon: 'fas fa-python',
                text: 'Python Compiler',
                active: this.currentPage === 'compiler.html'
            },
            {
                href: '/cpp_compiler.html',
                icon: 'fas fa-code',
                text: 'C++ Compiler',
                active: this.currentPage === 'cpp_compiler.html'
            },
            {
                href: '/visualization.html',
                icon: 'fas fa-chart-line',
                text: 'Visualizer',
                active: this.currentPage === 'visualization.html'
            },
            {
                href: 'http://localhost:8000/dev-ui/',
                icon: 'fas fa-robot',
                text: 'Agent',
                active: false
            }
        ];

        return links;
    }

    // Render navigation links
    renderNavigation() {
        const userControls = document.querySelector('.user-controls');
        if (!userControls) return;

        const links = this.getNavigationLinks();
        const usernameSpan = userControls.querySelector('.username');
        const logoutButton = userControls.querySelector('#logoutButton');

        // Clear existing navigation links (keep username and logout)
        const existingLinks = userControls.querySelectorAll('a');
        existingLinks.forEach(link => link.remove());

        // Add navigation links
        links.forEach(link => {
            if (!link.active) { // Don't add link for current page
                const navLink = document.createElement('a');
                navLink.href = link.href;
                navLink.className = 'btn btn-secondary';
                navLink.innerHTML = `<i class="${link.icon}"></i> ${link.text}`;
                userControls.insertBefore(navLink, logoutButton);
            }
        });
    }

    // Get authenticated headers for API calls
    getAuthHeaders() {
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.token}`
        };
    }
}

// Auto-initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const nav = new UnifiedNavigation();
    nav.init();
    nav.renderNavigation();
}); 