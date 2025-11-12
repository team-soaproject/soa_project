// assets/js/auth.js

// Check if user is authenticated
function isAuthenticated() {
    return localStorage.getItem('access_token') !== null;
}

// Get current user info
function getCurrentUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
}

// Save auth data
function saveAuthData(accessToken, refreshToken, user) {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
    localStorage.setItem('user', JSON.stringify(user));
}

// Clear auth data
function clearAuthData() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    localStorage.removeItem('profile');
}

// Logout
function logout() {
    clearAuthData();
    window.location.href = '/login.html';
}

// Redirect if not authenticated
function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = '/login.html';
    }
}

// Redirect if already authenticated
function redirectIfAuthenticated() {
    if (isAuthenticated()) {
        window.location.href = '/dashboard.html';
    }
}

// Update navbar with user info
function updateNavbar() {
    const user = getCurrentUser();
    if (!user) return;
    
    const userNameElement = document.getElementById('userName');
    if (userNameElement) {
        userNameElement.textContent = user.username;
    }
}

// Setup logout button
function setupLogoutButton() {
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            if (confirm('คุณต้องการออกจากระบบหรือไม่?')) {
                logout();
            }
        });
    }
}

// Initialize auth on page load
document.addEventListener('DOMContentLoaded', () => {
    updateNavbar();
    setupLogoutButton();
});
