// assets/js/auth.js - Fixed Authentication System

// =====================================================
// Role Permissions Configuration
// =====================================================
const ROLE_PERMISSIONS = {
    user: {
        canCreateRequest: true,
        canViewOwnRequests: true,
        canCancelOwnPendingRequests: true,
        canViewEquipment: true,
        canEditProfile: true,
        canAssignRequests: false,
        canUpdateAnyRequest: false,
        canManageUsers: false,
        canManageEquipment: false,
        canViewAllRequests: false,
        canDeleteRequests: false,
        canViewReports: false,
        canAddEquipment: false
    },
    technician: {
        canCreateRequest: true,
        canViewOwnRequests: true,
        canViewAssignedRequests: true,
        canUpdateAssignedRequests: true,
        canCompleteAssignedRequests: true,
        canViewEquipment: true,
        canEditProfile: true,
        canAssignRequests: false,
        canManageUsers: false,
        canManageEquipment: false,
        canDeleteRequests: false,
        canViewAllRequests: false,
        canViewReports: false,
        canAddEquipment: false
    },
    admin: {
        canCreateRequest: true,
        canViewOwnRequests: true,
        canViewAllRequests: true,
        canAssignRequests: true,
        canUpdateAnyRequest: true,
        canDeleteRequests: true,
        canManageUsers: true,
        canManageEquipment: true,
        canAddEquipment: true,
        canViewEquipment: true,
        canViewReports: true,
        canEditProfile: true,
        canCancelAnyRequest: true
    }
};

// =====================================================
// Authentication Functions
// =====================================================

function isAuthenticated() {
    const token = localStorage.getItem('access_token') || localStorage.getItem('token');
    return !!token;
}

function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = '../login.html';
        return false;
    }
    return true;
}

function redirectIfAuthenticated() {
    if (isAuthenticated()) {
        window.location.href = 'user/dashboard.html';
    }
}

function getCurrentUser() {
    const userStr = localStorage.getItem('user');
    
    if (!userStr) {
        console.warn('⚠️ No user data in localStorage');
        
        // Try to decode from JWT token as fallback
        const token = localStorage.getItem('access_token') || localStorage.getItem('token');
        if (token) {
            try {
                const tokenParts = token.split('.');
                if (tokenParts.length !== 3) {
                    throw new Error('Invalid token format');
                }
                
                const payload = JSON.parse(atob(tokenParts[1]));
                console.log('🔑 Decoded user from JWT:', payload);
                
                const user = {
                    id: payload.user_id || payload.id,
                    username: payload.username || localStorage.getItem('username') || 'user',
                    email: payload.email || '',
                    first_name: payload.first_name || payload.username || 'User',
                    last_name: payload.last_name || '',
                    role: payload.role || 'user',
                    is_staff: payload.is_staff || false,
                    is_superuser: payload.is_superuser || false
                };
                
                // Save for future use
                localStorage.setItem('user', JSON.stringify(user));
                console.log('✅ User data created from JWT and saved:', user);
                return user;
            } catch (e) {
                console.error('❌ Cannot decode JWT token:', e);
                console.log('Token:', token);
            }
        }
        
        console.error('❌ No valid user data available');
        return null;
    }
    
    try {
        const user = JSON.parse(userStr);
        console.log('👤 Current user from localStorage:', user);
        return user;
    } catch (e) {
        console.error('❌ Error parsing user data:', e);
        return null;
    }
}

function getUserRole() {
    const user = getCurrentUser();
    if (!user) {
        console.warn('⚠️ No user found, defaulting to "user" role');
        return 'user';
    }
    
    let role = null;
    
    if (user.role) {
        role = user.role;
    } else if (user.user_type) {
        role = user.user_type;
    } else if (user.is_superuser || user.is_staff) {
        role = 'admin';
    } else {
        role = 'user';
    }
    
    role = role.toLowerCase();
    if (role === 'superadmin') role = 'admin';
    
    console.log('🎭 User role:', role);
    return role;
}

function getRoleText(role) {
    const roleTexts = {
        'admin': 'ผู้ดูแลระบบ',
        'superadmin': 'ผู้ดูแลระบบ',
        'technician': 'ช่างเทคนิค',
        'user': 'ผู้ใช้ทั่วไป'
    };
    return roleTexts[role] || role;
}

// =====================================================
// Permission Checking Functions
// =====================================================

function hasPermission(permission) {
    const role = getUserRole();
    const permissions = ROLE_PERMISSIONS[role] || ROLE_PERMISSIONS.user;
    const result = permissions[permission] === true;
    
    console.log(`🔒 Permission check: ${permission} for role ${role} = ${result}`);
    return result;
}

function requirePermission(permission, redirectUrl = 'dashboard.html') {
    if (!hasPermission(permission)) {
        console.error(`❌ Access denied: missing permission "${permission}"`);
        alert('คุณไม่มีสิทธิ์เข้าถึงหน้านี้');
        window.location.href = redirectUrl;
        return false;
    }
    return true;
}

// =====================================================
// Request-Specific Permission Functions
// =====================================================

function canUpdateRequestStatus(request) {
    const role = getUserRole();
    const user = getCurrentUser();
    
    if (!user) {
        console.error('❌ Cannot check permission: no user data');
        return false;
    }
    
    if (role === 'admin') {
        return true;
    }
    
    if (role === 'technician') {
        return request.assigned_to === user.id && 
               ['ASSIGNED', 'IN_PROGRESS'].includes(request.status);
    }
    
    return false;
}

function canCancelRequest(request) {
    const role = getUserRole();
    const user = getCurrentUser();
    
    if (!user) {
        console.error('❌ Cannot check permission: no user data');
        return false;
    }
    
    if (role === 'admin') {
        return true;
    }
    
    if (role === 'user') {
        return request.requester === user.id && request.status === 'PENDING';
    }
    
    return false;
}

function canDeleteRequest(request) {
    return getUserRole() === 'admin';
}

function canAssignRequest(request) {
    return getUserRole() === 'admin' && request.status === 'PENDING';
}

function canEditEquipment() {
    return getUserRole() === 'admin';
}

function canDeleteEquipment() {
    return getUserRole() === 'admin';
}

function canManageUsers() {
    return getUserRole() === 'admin';
}

// =====================================================
// UI Helper Functions
// =====================================================

function showRoleBasedElements() {
    const role = getUserRole();
    console.log('👁️ Showing elements for role:', role);
    
    document.querySelectorAll('[data-role], [data-roles]').forEach(el => {
        el.style.display = 'none';
    });
    
    document.querySelectorAll(`[data-role="${role}"]`).forEach(el => {
        el.style.display = '';
    });
    
    document.querySelectorAll('[data-roles]').forEach(el => {
        const roles = el.getAttribute('data-roles').split(',').map(r => r.trim());
        if (roles.includes(role)) {
            el.style.display = '';
        }
    });
}

function hideElementsByPermission() {
    document.querySelectorAll('[data-permission]').forEach(el => {
        const permission = el.getAttribute('data-permission');
        if (!hasPermission(permission)) {
            el.style.display = 'none';
        }
    });
}

function disableElementsByPermission() {
    document.querySelectorAll('[data-require-permission]').forEach(el => {
        const permission = el.getAttribute('data-require-permission');
        if (!hasPermission(permission)) {
            el.disabled = true;
            el.style.opacity = '0.5';
            el.style.cursor = 'not-allowed';
        }
    });
}

function updateUserDisplay() {
    const user = getCurrentUser();
    const role = getUserRole();
    
    if (!user) {
        console.warn('⚠️ Cannot update user display: no user data');
        return;
    }
    
    console.log('🖥️ Updating user display:', user.username, role);
    
    const userNameEl = document.getElementById('userName');
    if (userNameEl) {
        userNameEl.textContent = user.first_name || user.username || 'ผู้ใช้';
    }
    
    const userRoleEl = document.getElementById('userRole');
    if (userRoleEl) {
        userRoleEl.textContent = getRoleText(role);
        userRoleEl.className = `role-badge ${role}`;
    }
}

// =====================================================
// Logout Function
// =====================================================

function logout() {
    console.log('🚪 Logging out...');
    
    localStorage.removeItem('token');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    localStorage.removeItem('username');
    localStorage.removeItem('user_profile');
    localStorage.removeItem('user_role');
    
    window.location.href = '../login.html';
}

// =====================================================
// Helper Functions for Status Display
// =====================================================

function getStatusText(status) {
    const statusTexts = {
        'PENDING': 'รอดำเนินการ',
        'ASSIGNED': 'มอบหมายแล้ว',
        'IN_PROGRESS': 'กำลังซ่อม',
        'COMPLETED': 'เสร็จสิ้น',
        'CANCELLED': 'ยกเลิก'
    };
    return statusTexts[status] || status;
}

function getStatusBadge(status) {
    const badges = {
        'PENDING': 'badge-pending',
        'ASSIGNED': 'badge-warning',
        'IN_PROGRESS': 'badge-progress',
        'COMPLETED': 'badge-success',
        'CANCELLED': 'badge-secondary'
    };
    return badges[status] || 'badge-secondary';
}

function getPriorityText(priority) {
    const texts = {
        'LOW': 'ต่ำ',
        'MEDIUM': 'ปานกลาง',
        'HIGH': 'สูง',
        'URGENT': 'เร่งด่วน'
    };
    return texts[priority] || priority;
}

function getPriorityBadge(priority) {
    const badges = {
        'LOW': 'badge-secondary',
        'MEDIUM': 'badge-info',
        'HIGH': 'badge-warning',
        'URGENT': 'badge-danger'
    };
    return badges[priority] || 'badge-secondary';
}

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

function showError(message) {
    console.error('❌', message);
    alert(message);
}

function showSuccess(message) {
    console.log('✅', message);
    alert(message);
}

// =====================================================
// Initialize on Page Load
// =====================================================

function initializeAuth() {
    console.log('🚀 Initializing auth system...');
    
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            logout();
        });
    }
    
    if (isAuthenticated()) {
        showRoleBasedElements();
        hideElementsByPermission();
        disableElementsByPermission();
        updateUserDisplay();
        
        console.log('✅ Auth initialized for user:', getCurrentUser()?.username);
    } else {
        console.log('⚠️ User not authenticated');
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAuth);
} else {
    initializeAuth();
}

console.log('✅ Auth.js loaded successfully');