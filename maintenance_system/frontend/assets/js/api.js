// assets/js/api.js

const API_BASE_URL = 'http://127.0.0.1:8000/api';

// Helper function to get token from localStorage
function getToken() {
    return localStorage.getItem('access_token');
}

// Helper function to get headers with authorization
function getHeaders(includeAuth = true) {
    const headers = {
        'Content-Type': 'application/json',
    };
    
    if (includeAuth) {
        const token = getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
    }
    
    return headers;
}

// Helper function for API calls
async function apiCall(endpoint, method = 'GET', data = null, includeAuth = true) {
    const url = `${API_BASE_URL}${endpoint}`;
    const options = {
        method: method,
        headers: getHeaders(includeAuth),
    };
    
    if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, options);
        
        // Check if token expired
        if (response.status === 401) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login.html';
            return;
        }
        
        const result = await response.json();
        
        if (!response.ok) {
            throw result;
        }
        
        return result;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Helper for FormData uploads (with files)
async function apiUpload(endpoint, formData) {
    const url = `${API_BASE_URL}${endpoint}`;
    const token = getToken();
    
    const options = {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        body: formData
    };
    
    try {
        const response = await fetch(url, options);
        
        if (response.status === 401) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login.html';
            return;
        }
        
        const result = await response.json();
        
        if (!response.ok) {
            throw result;
        }
        
        return result;
    } catch (error) {
        console.error('Upload Error:', error);
        throw error;
    }
}

// Authentication APIs
const authAPI = {
    login: async (username, password) => {
        return await apiCall('/token/', 'POST', { username, password }, false);
    },
    
    register: async (userData) => {
        return await apiCall('/auth/register/', 'POST', userData, false);
    },
    
    getProfile: async () => {
        return await apiCall('/profiles/me/');
    },
    
    updateProfile: async (data) => {
        return await apiCall('/profiles/update_profile/', 'PUT', data);
    }
};

// Equipment Category APIs
const categoryAPI = {
    getAll: async (search = '') => {
        const query = search ? `?search=${search}` : '';
        return await apiCall(`/categories/${query}`);
    },
    
    getOne: async (id) => {
        return await apiCall(`/categories/${id}/`);
    },
    
    create: async (data) => {
        return await apiCall('/categories/', 'POST', data);
    },
    
    update: async (id, data) => {
        return await apiCall(`/categories/${id}/`, 'PUT', data);
    },
    
    delete: async (id) => {
        return await apiCall(`/categories/${id}/`, 'DELETE');
    }
};

// Equipment APIs
const equipmentAPI = {
    getAll: async (params = {}) => {
        const query = new URLSearchParams(params).toString();
        return await apiCall(`/equipment/${query ? '?' + query : ''}`);
    },
    
    getOne: async (id) => {
        return await apiCall(`/equipment/${id}/`);
    },
    
    create: async (formData) => {
        return await apiUpload('/equipment/', formData);
    },
    
    update: async (id, formData) => {
        const url = `${API_BASE_URL}/equipment/${id}/`;
        const token = getToken();
        
        const response = await fetch(url, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        
        return await response.json();
    },
    
    delete: async (id) => {
        return await apiCall(`/equipment/${id}/`, 'DELETE');
    },
    
    getAvailable: async () => {
        return await apiCall('/equipment/available/');
    }
};

// Repair Request APIs
const repairAPI = {
    getAll: async (params = {}) => {
        const query = new URLSearchParams(params).toString();
        return await apiCall(`/repair-requests/${query ? '?' + query : ''}`);
    },
    
    getOne: async (id) => {
        return await apiCall(`/repair-requests/${id}/`);
    },
    
    create: async (data) => {
        return await apiCall('/repair-requests/', 'POST', data);
    },
    
    update: async (id, data) => {
        return await apiCall(`/repair-requests/${id}/`, 'PATCH', data);
    },
    
    delete: async (id) => {
        return await apiCall(`/repair-requests/${id}/`, 'DELETE');
    },
    
    getMyRequests: async () => {
        return await apiCall('/repair-requests/my_requests/');
    },
    
    getAssignedToMe: async () => {
        return await apiCall('/repair-requests/assigned_to_me/');
    },
    
    assign: async (id, technicianId) => {
        return await apiCall(`/repair-requests/${id}/assign/`, 'POST', {
            technician_id: technicianId
        });
    },
    
    updateStatus: async (id, status, comment = '') => {
        return await apiCall(`/repair-requests/${id}/update_status/`, 'POST', {
            status: status,
            comment: comment
        });
    },
    
    getHistory: async (id) => {
        return await apiCall(`/repair-requests/${id}/history/`);
    }
};

// Dashboard APIs
const dashboardAPI = {
    getStats: async () => {
        return await apiCall('/dashboard/stats/');
    },
    
    getTechnicians: async () => {
        return await apiCall('/technicians/');
    }
};

// Display error message
function showError(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger';
    alertDiv.textContent = message;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
}

// Display success message
function showSuccess(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success';
    alertDiv.textContent = message;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
}

// Format date
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('th-TH', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Format currency
function formatCurrency(amount) {
    if (!amount) return '-';
    return new Intl.NumberFormat('th-TH', {
        style: 'currency',
        currency: 'THB'
    }).format(amount);
}

// Get status badge class
function getStatusBadge(status) {
    const badges = {
        'pending': 'badge-pending',
        'assigned': 'badge-assigned',
        'in_progress': 'badge-in-progress',
        'completed': 'badge-completed',
        'cancelled': 'badge-cancelled'
    };
    return badges[status] || 'badge-pending';
}

// Get priority badge class
function getPriorityBadge(priority) {
    const badges = {
        'low': 'badge-low',
        'medium': 'badge-medium',
        'high': 'badge-high',
        'urgent': 'badge-urgent'
    };
    return badges[priority] || 'badge-medium';
}
