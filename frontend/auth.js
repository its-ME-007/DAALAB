document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const signupForm = document.getElementById('signupForm');
    const logoutButton = document.getElementById('logoutButton');
    const usernameDisplay = document.getElementById('username');

    // Check if user is logged in
    const checkAuth = () => {
        const token = localStorage.getItem('token');
        const user = JSON.parse(localStorage.getItem('user'));
        
        if (token && user) {
            if (usernameDisplay) {
                usernameDisplay.textContent = user.email;
            }
            if (window.location.pathname.includes('login.html') || 
                window.location.pathname.includes('signup.html')) {
                window.location.href = 'index.html';
            }
        } else {
            if (!window.location.pathname.includes('login.html') && 
                !window.location.pathname.includes('signup.html')) {
                window.location.href = 'login.html';
            }
        }
    };

    // Handle login
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            try {
                const response = await fetch('http://localhost:5000/api/auth/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ email, password })
                });

                const data = await response.json();

                if (data.success) {
                    localStorage.setItem('token', data.session.access_token);
                    localStorage.setItem('user', JSON.stringify(data.user));
                    window.location.href = 'index.html';
                } else {
                    alert(data.error || 'Login failed');
                }
            } catch (error) {
                console.error('Login error:', error);
                alert('Login failed. Please try again.');
            }
        });
    }

    // Handle signup
    if (signupForm) {
        signupForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            try {
                const response = await fetch('http://localhost:5000/api/auth/signup', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ username, email, password })
                });

                const data = await response.json();

                if (data.success) {
                    alert('Account created successfully! Please login.');
                    window.location.href = 'login.html';
                } else {
                    alert(data.error || 'Signup failed');
                }
            } catch (error) {
                console.error('Signup error:', error);
                alert('Signup failed. Please try again.');
            }
        });
    }

    // Handle logout
    if (logoutButton) {
        logoutButton.addEventListener('click', async () => {
            try {
                const response = await fetch('http://localhost:5000/api/auth/logout', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                });

                const data = await response.json();

                if (data.success) {
                    localStorage.removeItem('token');
                    localStorage.removeItem('user');
                    window.location.href = 'login.html';
                }
            } catch (error) {
                console.error('Logout error:', error);
                alert('Logout failed. Please try again.');
            }
        });
    }

    // Check authentication status on page load
    checkAuth();
}); 