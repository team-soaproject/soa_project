// assets/js/api.js - Enhanced API Client

const API_BASE_URL = 'http://127.0.0.1:8000';

// =====================================================
// Core API Call Function
// =====================================================
async function apiCall(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const defaultHeaders = {
        'Content-Type': 'application/json',
    };
    
    const token = localStorage.getItem('access_token') || localStorage.getItem('token');
    if (token) {
        defaultHeaders['Authorization'] = `Bearer ${token}`;
    }
    
    const config = {
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers,
        },
    };
    
    try {
        console.log('🌐 API Call:', options.method || 'GET', url);
        
        const response = await fetch(url, config);
        
        // Handle 401 Unauthorized
        if (response.status === 401) {
            console.error('❌ 401 Unauthorized - Session expired');
            localStorage.clear();
            window.location.href = getLoginPath();
            throw new Error('Session expired. Please login again.');
        }
        
        // Handle 204 No Content
        if (response.status === 204) {
            console.log('✅ API Success (No Content)');
            return null;
        }
        
        // Parse response
        let data;
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        } else {
            const text = await response.text();
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${text}`);
            }
            return text;
        }
        
        if (!response.ok) {
            const errorMessage = data.detail || data.message || data.error || 'เกิดข้อผิดพลาด';
            console.error('❌ API Error:', errorMessage, data);
            throw new Error(errorMessage);
        }
        
        console.log('✅ API Success:', data);
        return data;
        
    } catch (error) {
        console.error('❌ API Call Failed:', error);
        throw error;
    }
}

function getLoginPath() {
    const currentPath = window.location.pathname;
    if (currentPath.includes('/admin/') || 
        currentPath.includes('/technician/') || 
        currentPath.includes('/user/')) {
        return '../login.html';
    }
    return './login.html';
}

// =====================================================
// Authentication API
// =====================================================
const authAPI = {
    async login(username, password) {
        const data = await apiCall('/api/auth/token/', {
            method: 'POST',
            body: JSON.stringify({ username, password }),
        });
        
        if (data.access) {
            localStorage.setItem('access_token', data.access);
            localStorage.setItem('token', data.access);
            localStorage.setItem('refresh_token', data.refresh);
            
            if (data.user) {
                if (!data.user.full_name && data.user.first_name) {
                    data.user.full_name = `${data.user.first_name} ${data.user.last_name || ''}`.trim();
                }
                if (!data.user.full_name) {
                    data.user.full_name = data.user.username;
                }
                localStorage.setItem('user', JSON.stringify(data.user));
            }
        }
        
        return data;
    },
    
    async refreshToken() {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
            throw new Error('No refresh token available');
        }
        
        const data = await apiCall('/api/auth/token/refresh/', {
            method: 'POST',
            body: JSON.stringify({ refresh: refreshToken }),
        });
        
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('token', data.access);
        return data;
    }
};

// =====================================================
// Maintenance Requests API
// =====================================================
const maintenanceAPI = {
    async list(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = queryString ? `/api/maintenance-requests/?${queryString}` : '/api/maintenance-requests/';
        return await apiCall(endpoint);
    },
    
    async get(id) {
        return await apiCall(`/api/maintenance-requests/${id}/`);
    },
    
    async create(formData) {
        const token = localStorage.getItem('access_token');
        
        const response = await fetch(`${API_BASE_URL}/api/maintenance-requests/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
            },
            body: formData,
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create request');
        }
        
        return await response.json();
    },
    
    async update(id, data) {
        return await apiCall(`/api/maintenance-requests/${id}/`, {
            method: 'PATCH',
            body: JSON.stringify(data),
        });
    },
    
    async delete(id) {
        return await apiCall(`/api/maintenance-requests/${id}/`, {
            method: 'DELETE',
        });
    },
    
    async updateStatus(id, status, comment = '') {
        return await apiCall(`/api/maintenance-requests/${id}/update_status/`, {
            method: 'POST',
            body: JSON.stringify({ status, comment }),
        });
    },
    
    async assignTechnician(id, technicianId) {
        return await apiCall(`/api/maintenance-requests/${id}/assign_technician/`, {
            method: 'POST',
            body: JSON.stringify({ technician_id: technicianId }),
        });
    },
    
    async statistics() {
        try {
            return await apiCall('/api/maintenance-requests/statistics/');
        } catch (error) {
            console.warn('Statistics endpoint not available, calculating manually');
            const data = await this.list();
            const requests = data.results || data || [];
            
            return {
                total_requests: requests.length,
                pending_requests: requests.filter(r => r.status === 'PENDING').length,
                in_progress_requests: requests.filter(r => r.status === 'IN_PROGRESS').length,
                completed_requests: requests.filter(r => r.status === 'COMPLETED').length,
                average_completion_time: 0
            };
        }
    }
};

// =====================================================
// Equipment API
// =====================================================
const equipmentAPI = {
    async list(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = queryString ? `/api/equipment/?${queryString}` : '/api/equipment/';
        return await apiCall(endpoint);
    },
    
    async get(id) {
        return await apiCall(`/api/equipment/${id}/`);
    },
    
    async create(data) {
        return await apiCall('/api/equipment/', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },
    
    async update(id, data) {
        return await apiCall(`/api/equipment/${id}/`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    },
    
    async delete(id) {
        return await apiCall(`/api/equipment/${id}/`, {
            method: 'DELETE',
        });
    },
    
    async statistics() {
        try {
            return await apiCall('/api/equipment/statistics/');
        } catch (error) {
            console.warn('Equipment statistics endpoint not available, calculating manually');
            const data = await this.list();
            const equipment = data.results || data || [];
            
            return {
                total_equipment: equipment.length,
                active: equipment.filter(e => e.status === 'ACTIVE').length,
                under_repair: equipment.filter(e => e.status === 'UNDER_REPAIR').length,
                out_of_service: equipment.filter(e => e.status === 'OUT_OF_SERVICE').length,
            };
        }
    }
};

// =====================================================
// Users API
// =====================================================
const usersAPI = {
    async list(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = queryString ? `/api/users/?${queryString}` : '/api/users/';
        return await apiCall(endpoint);
    },
    
    async get(id) {
        return await apiCall(`/api/users/${id}/`);
    },
    
    async update(id, data) {
        return await apiCall(`/api/users/${id}/`, {
            method: 'PATCH',
            body: JSON.stringify(data),
        });
    },
    
    async makeAdmin(id) {
        return await apiCall(`/api/users/${id}/make_admin/`, {
            method: 'POST',
        });
    },
    
    async removeAdmin(id) {
        return await apiCall(`/api/users/${id}/remove_admin/`, {
            method: 'POST',
        });
    },
    
    async rolesSummary() {
        try {
            return await apiCall('/api/users/roles_summary/');
        } catch (error) {
            console.warn('Roles summary endpoint not available, calculating manually');
            const data = await this.list();
            const users = data.results || data || [];
            
            return {
                total: users.length,
                admins: users.filter(u => u.is_staff || u.is_superuser).length,
                technicians: users.filter(u => u.role === 'technician').length,
                users: users.filter(u => u.role === 'user').length,
            };
        }
    }
};

// =====================================================
// Technicians API
// =====================================================
const techniciansAPI = {
    async list(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = queryString ? `/api/technicians/?${queryString}` : '/api/technicians/';
        return await apiCall(endpoint);
    },
    
    async get(id) {
        return await apiCall(`/api/technicians/${id}/`);
    }
};

// =====================================================
// Helper Functions for My Requests & Request Detail Pages
// =====================================================
async function getMaintenanceRequests(params = {}) {
    const queryParams = new URLSearchParams(params).toString();
    const endpoint = queryParams ? `/api/maintenance-requests/?${queryParams}` : '/api/maintenance-requests/';
    return await apiCall(endpoint);
}

async function getMaintenanceRequestById(id) {
    return await apiCall(`/api/maintenance-requests/${id}/`);
}

async function updateMaintenanceRequestStatus(id, status, comment = '') {
    return await apiCall(`/api/maintenance-requests/${id}/update_status/`, {
        method: 'POST',
        body: JSON.stringify({ status, comment }),
    });
}

console.log('✅ API.js loaded successfully');
console.log('🔗 API Base URL:', API_BASE_URL);