// assets/js/auth.js - Fixed Authentication System

// =====================================================
// Configuration
// =====================================================
const API_BASE_URL = 'http://127.0.0.1:8000';

// =====================================================
// Helper Functions
// =====================================================
function getLoginPath() {
    const currentPath = window.location.pathname;
    if (currentPath.includes('/admin/') || 
        currentPath.includes('/technician/') || 
        currentPath.includes('/user/')) {
        return '../login.html';
    }
    return './login.html';
}

function getToken() {
    return localStorage.getItem('access_token') || localStorage.getItem('token');
}

function setToken(token) {
    localStorage.setItem('access_token', token);
    localStorage.setItem('token', token);
}

// =====================================================
// User Management
// =====================================================
function getCurrentUser() {
    const userStr = localStorage.getItem('user');
    
    if (!userStr) {
        console.warn('⚠️ No user data in localStorage');
        
        const token = getToken();
        if (token) {
            try {
                const tokenParts = token.split('.');
                if (tokenParts.length === 3) {
                    const payload = JSON.parse(atob(tokenParts[1]));
                    const user = {
                        id: payload.user_id || payload.id,
                        username: payload.username || 'user',
                        email: payload.email || '',
                        first_name: payload.first_name || payload.username || 'User',
                        last_name: payload.last_name || '',
                        full_name: payload.full_name || payload.first_name || payload.username || 'User',
                        role: payload.role || 'user',
                        is_staff: payload.is_staff || false,
                        is_superuser: payload.is_superuser || false
                    };
                    
                    localStorage.setItem('user', JSON.stringify(user));
                    return user;
                }
            } catch (e) {
                console.error('❌ Cannot decode JWT token:', e);
            }
        }
        return null;
    }
    
    try {
        return JSON.parse(userStr);
    } catch (e) {
        console.error('❌ Error parsing user data:', e);
        return null;
    }
}

function getUserRole() {
    const user = getCurrentUser();
    if (!user) return 'user';
    
    if (user.is_superuser) return 'admin';
    if (user.is_staff) return 'admin';
    if (user.role) return user.role.toLowerCase();
    
    return 'user';
}

function getUserId() {
    const user = getCurrentUser();
    return user ? user.id : null;
}

// =====================================================
// Authentication Check
// =====================================================
function isAuthenticated() {
    const token = getToken();
    if (!token) return false;
    
    try {
        const tokenParts = token.split('.');
        if (tokenParts.length !== 3) return false;
        
        const payload = JSON.parse(atob(tokenParts[1]));
        const exp = payload.exp;
        
        if (exp && Date.now() >= exp * 1000) {
            console.log('🕐 Token expired');
            logout();
            return false;
        }
        
        return true;
    } catch (e) {
        console.error('❌ Invalid token:', e);
        return false;
    }
}

function requireAuth() {
    if (!isAuthenticated()) {
        console.log('❌ Not authenticated, redirecting to login...');
        const loginPath = getLoginPath();
        window.location.href = loginPath;
        return false;
    }
    return true;
}

// =====================================================
// Role-Based Access Control
// =====================================================
function hasRole(role) {
    const userRole = getUserRole();
    return userRole === role;
}

function isAdmin() {
    return hasRole('admin');
}

function isTechnician() {
    return hasRole('technician');
}

function isUser() {
    return hasRole('user');
}

function requireRole(requiredRole) {
    if (!requireAuth()) return false;
    
    const userRole = getUserRole();
    
    if (userRole !== requiredRole) {
        console.log(`❌ Access denied: required ${requiredRole}, got ${userRole}`);
        alert('คุณไม่มีสิทธิ์เข้าถึงหน้านี้');
        
        // Redirect to appropriate page
        if (userRole === 'admin') {
            window.location.href = '../admin/dashboard.html';
        } else if (userRole === 'technician') {
            window.location.href = '../technician/dashboard.html';
        } else {
            window.location.href = '../user/dashboard.html';
        }
        return false;
    }
    
    return true;
}

// =====================================================
// Logout
// =====================================================
function logout() {
    console.log('🚪 Logging out...');
    localStorage.clear();
    window.location.href = getLoginPath();
}

// =====================================================
// UI Updates
// =====================================================
function updateUserDisplay() {
    const user = getCurrentUser();
    const role = getUserRole();
    
    if (!user) {
        console.warn('⚠️ Cannot update user display: no user data');
        return;
    }
    
    const userNameEl = document.getElementById('userName');
    if (userNameEl) {
        userNameEl.textContent = user.full_name || user.first_name || user.username || 'ผู้ใช้';
    }
    
    const userRoleEl = document.getElementById('userRole');
    if (userRoleEl) {
        const roleTexts = {
            'admin': 'ผู้ดูแลระบบ',
            'technician': 'ช่างเทคนิค',
            'user': 'ผู้ใช้ทั่วไป'
        };
        userRoleEl.textContent = roleTexts[role] || role;
    }
    
    console.log('🖥️ User display updated:', user.username, role);
}

// =====================================================
// Status & Priority Text Helpers
// =====================================================
function getStatusText(status) {
    const texts = {
        'PENDING': 'รอดำเนินการ',
        'ASSIGNED': 'มอบหมายแล้ว',
        'IN_PROGRESS': 'กำลังซ่อม',
        'COMPLETED': 'เสร็จสิ้น',
        'CANCELLED': 'ยกเลิก'
    };
    return texts[status] || status;
}

function getStatusBadge(status) {
    const badges = {
        'PENDING': 'badge-pending',
        'ASSIGNED': 'badge-assigned',
        'IN_PROGRESS': 'badge-in-progress',
        'COMPLETED': 'badge-completed',
        'CANCELLED': 'badge-cancelled'
    };
    return badges[status] || 'badge-secondary';
}

function getPriorityText(priority) {
    const texts = {
        'LOW': 'ปกติ',
        'MEDIUM': 'ด่วน',
        'HIGH': 'ด่วนมาก',
        'URGENT': 'เร่งด่วนที่สุด'
    };
    return texts[priority] || priority;
}

function getPriorityBadge(priority) {
    const badges = {
        'LOW': 'badge-low',
        'MEDIUM': 'badge-medium',
        'HIGH': 'badge-high',
        'URGENT': 'badge-urgent'
    };
    return badges[priority] || 'badge-secondary';
}

// =====================================================
// Date Formatting
// =====================================================
function formatDate(dateString) {
    if (!dateString) return '-';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleString('th-TH', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (e) {
        return dateString;
    }
}

function formatDateShort(dateString) {
    if (!dateString) return '-';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('th-TH', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    } catch (e) {
        return dateString;
    }
}

// =====================================================
// Permission Checks
// =====================================================
function canUpdateRequestStatus(request) {
    const role = getUserRole();
    const userId = getUserId();
    
    if (role === 'admin') return true;
    
    if (role === 'technician') {
        const assignedToId = request.assigned_technician_detail?.user?.id || 
                            request.assigned_to?.id || 
                            request.assigned_to;
        return assignedToId === userId && ['PENDING', 'IN_PROGRESS'].includes(request.status);
    }
    
    return false;
}

function canCancelRequest(request) {
    const role = getUserRole();
    const userId = getUserId();
    
    if (role === 'admin') return true;
    
    if (role === 'user') {
        const requesterId = request.requester?.id || request.requester;
        return requesterId === userId && request.status === 'PENDING';
    }
    
    return false;
}

// =====================================================
// Initialize
// =====================================================
function initializeAuth() {
    console.log('🚀 Initializing auth system...');
    
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            if (confirm('คุณต้องการออกจากระบบหรือไม่?')) {
                logout();
            }
        });
    }
    
    if (isAuthenticated()) {
        updateUserDisplay();
        console.log('✅ Auth initialized for user:', getCurrentUser()?.username);
    }
}

// Auto-initialize on load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAuth);
} else {
    initializeAuth();
}

console.log('✅ Auth.js loaded successfully');