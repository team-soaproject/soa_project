// api.js - Fixed API Management System
// แก้ไข endpoint ให้ตรงกับ Django URLs ทุกจุด

const API_BASE_URL = 'http://127.0.0.1:8000';

// =====================================================
// Core API Functions
// =====================================================

async function apiCall(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const defaultHeaders = {
        'Content-Type': 'application/json',
    };
    
    // Get token
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
        console.log('🌐 API Call:', url, config.method || 'GET');
        
        const response = await fetch(url, config);
        
        // Handle 401 Unauthorized
        if (response.status === 401) {
            console.error('❌ 401 Unauthorized - Session expired');
            localStorage.clear();
            window.location.href = 'login.html';
            throw new Error('Session expired. Please login again.');
        }
        
        // Handle 403 Forbidden
        if (response.status === 403) {
            throw new Error('คุณไม่มีสิทธิ์ในการทำรายการนี้');
        }
        
        // Handle 404 Not Found
        if (response.status === 404) {
            throw new Error('ไม่พบข้อมูลที่ต้องการ');
        }
        
        // Handle 204 No Content (success but no data)
        if (response.status === 204) {
            console.log('✅ API Success (No Content)');
            return null;
        }
        
        // Try to parse JSON response
        let data;
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        } else {
            const text = await response.text();
            console.error('❌ Response is not JSON:', text);
            throw new Error('Server returned invalid response');
        }
        
        if (!response.ok) {
            const errorMessage = data.detail || data.message || data.error || 'เกิดข้อผิดพลาด';
            console.error('❌ API Error:', errorMessage);
            throw new Error(errorMessage);
        }
        
        console.log('✅ API Success:', data);
        return data;
        
    } catch (error) {
        console.error('❌ API Call Failed:', error);
        throw error;
    }
}

// =====================================================
// Authentication API
// =====================================================

const authAPI = {
    async login(username, password) {
        try {
            console.log('🔐 Logging in:', username);
            
            const data = await apiCall('/api/auth/token/', {
                method: 'POST',
                body: JSON.stringify({ username, password }),
            });
            
            if (!data.access) {
                throw new Error('Invalid response from server');
            }
            
            // Store tokens
            localStorage.setItem('access_token', data.access);
            localStorage.setItem('token', data.access);
            localStorage.setItem('refresh_token', data.refresh);
            localStorage.setItem('username', username);
            
            // Store user data from response
            if (data.user) {
                localStorage.setItem('user', JSON.stringify(data.user));
                console.log('✅ User data stored:', data.user);
                console.log('👤 User role:', data.user.role);
            } else {
                console.error('❌ WARNING: No user data in login response!');
                console.log('📦 Full response:', data);
                
                // Fallback: Try to decode JWT token
                try {
                    const tokenParts = data.access.split('.');
                    const payload = JSON.parse(atob(tokenParts[1]));
                    console.log('🔍 JWT Payload:', payload);
                    
                    const fallbackUser = {
                        id: payload.user_id,
                        username: payload.username || username,
                        email: payload.email || '',
                        first_name: payload.first_name || '',
                        last_name: payload.last_name || '',
                        role: payload.role || 'user',
                        is_staff: payload.is_staff || false,
                        is_superuser: payload.is_superuser || false
                    };
                    
                    localStorage.setItem('user', JSON.stringify(fallbackUser));
                    console.log('✅ Fallback user data created:', fallbackUser);
                } catch (e) {
                    console.error('❌ Cannot decode JWT token:', e);
                }
            }
            
            console.log('✅ Login successful');
            return data;
            
        } catch (error) {
            console.error('❌ Login failed:', error);
            throw error;
        }
    },
    
    async register(userData) {
        try {
            const data = await apiCall('/api/auth/register/', {
                method: 'POST',
                body: JSON.stringify(userData),
            });
            
            console.log('✅ Registration successful');
            return data;
        } catch (error) {
            console.error('❌ Registration failed:', error);
            throw error;
        }
    },
    
    async refreshToken() {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
            throw new Error('No refresh token available');
        }
        
        try {
            const data = await apiCall('/api/auth/token/refresh/', {
                method: 'POST',
                body: JSON.stringify({ refresh: refreshToken }),
            });
            
            localStorage.setItem('access_token', data.access);
            localStorage.setItem('token', data.access);
            
            console.log('✅ Token refreshed');
            return data;
        } catch (error) {
            console.error('❌ Token refresh failed:', error);
            localStorage.clear();
            window.location.href = 'login.html';
            throw error;
        }
    }
};

// =====================================================
// Equipment API
// =====================================================

async function getEquipmentList(filters = {}) {
    const params = new URLSearchParams();
    Object.keys(filters).forEach(key => {
        if (filters[key]) params.append(key, filters[key]);
    });
    
    const queryString = params.toString();
    const endpoint = queryString ? `/api/equipment/?${queryString}` : '/api/equipment/';
    
    return await apiCall(endpoint);
}

async function getEquipmentById(id) {
    return await apiCall(`/api/equipment/${id}/`);
}

async function createEquipment(equipmentData) {
    return await apiCall('/api/equipment/', {
        method: 'POST',
        body: JSON.stringify(equipmentData),
    });
}

async function updateEquipment(id, equipmentData) {
    return await apiCall(`/api/equipment/${id}/`, {
        method: 'PUT',
        body: JSON.stringify(equipmentData),
    });
}

async function deleteEquipmentById(id) {
    return await apiCall(`/api/equipment/${id}/`, {
        method: 'DELETE',
    });
}

async function getCategories() {
    // ดึง categories จาก equipment list
    try {
        const response = await getEquipmentList();
        const equipment = response.results || response || [];
        
        // Extract unique categories
        const categories = [...new Set(equipment.map(e => e.category).filter(c => c))];
        
        // Return in format similar to backend
        return categories.map((name, index) => ({
            id: index + 1,
            name: name
        }));
    } catch (error) {
        console.error('Failed to get categories:', error);
        // Return default categories
        return [
            { id: 1, name: 'IT' },
            { id: 2, name: 'อาคารสถานที่' },
            { id: 3, name: 'เครื่องใช้สำนักงาน' },
            { id: 4, name: 'ยานพาหนะ' },
            { id: 5, name: 'อื่นๆ' }
        ];
    }
}

// =====================================================
// Maintenance Requests API
// =====================================================

async function getMaintenanceRequests(filters = {}) {
    const params = new URLSearchParams();
    Object.keys(filters).forEach(key => {
        if (filters[key]) params.append(key, filters[key]);
    });
    
    const queryString = params.toString();
    const endpoint = queryString ? `/api/maintenance-requests/?${queryString}` : '/api/maintenance-requests/';
    
    return await apiCall(endpoint);
}

async function getMaintenanceRequestById(id) {
    return await apiCall(`/api/maintenance-requests/${id}/`);
}

async function createMaintenanceRequest(formData) {
    const token = localStorage.getItem('access_token') || localStorage.getItem('token');
    
    try {
        console.log('📝 Creating maintenance request...');
        
        const response = await fetch(`${API_BASE_URL}/api/maintenance-requests/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                // Don't set Content-Type for FormData - browser sets it with boundary
            },
            body: formData,
        });
        
        if (response.status === 401) {
            localStorage.clear();
            window.location.href = 'login.html';
            throw new Error('Session expired');
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || error.message || 'Failed to create request');
        }
        
        const data = await response.json();
        console.log('✅ Request created:', data);
        return data;
    } catch (error) {
        console.error('❌ Create request failed:', error);
        throw error;
    }
}

async function updateMaintenanceRequestStatus(id, status, comment = '') {
    return await apiCall(`/api/maintenance-requests/${id}/update-status/`, {
        method: 'POST',
        body: JSON.stringify({ status, comment }),
    });
}

async function assignMaintenanceRequest(id, technicianId, comment = '') {
    return await apiCall(`/api/maintenance-requests/${id}/assign/`, {
        method: 'POST',
        body: JSON.stringify({ 
            assigned_to: technicianId,
            comment 
        }),
    });
}

async function deleteMaintenanceRequest(id) {
    return await apiCall(`/api/maintenance-requests/${id}/`, {
        method: 'DELETE',
    });
}

// =====================================================
// Users API
// =====================================================

async function getUsers(filters = {}) {
    const params = new URLSearchParams();
    Object.keys(filters).forEach(key => {
        if (filters[key]) params.append(key, filters[key]);
    });
    
    const queryString = params.toString();
    const endpoint = queryString ? `/api/users/?${queryString}` : '/api/users/';
    
    return await apiCall(endpoint);
}

async function getTechnicians() {
    return await apiCall('/api/technicians/');
}

async function getUserById(id) {
    return await apiCall(`/api/users/${id}/`);
}

async function updateUser(id, userData) {
    return await apiCall(`/api/users/${id}/`, {
        method: 'PUT',
        body: JSON.stringify(userData),
    });
}

async function deleteUser(id) {
    return await apiCall(`/api/users/${id}/`, {
        method: 'DELETE',
    });
}

async function updateUserRole(id, role) {
    return await apiCall(`/api/users/${id}/update-role/`, {
        method: 'POST',
        body: JSON.stringify({ role }),
    });
}

// =====================================================
// Dashboard/Statistics API
// =====================================================

const dashboardAPI = {
    async getStats() {
        try {
            return await apiCall('/api/dashboard/stats/');
        } catch (error) {
            console.error('Dashboard stats not available:', error);
            // Return mock data if endpoint doesn't exist yet
            return {
                total_requests: 0,
                pending_requests: 0,
                in_progress_requests: 0,
                completed_requests: 0,
                total_equipment: 0,
                total_users: 0,
                total_technicians: 0
            };
        }
    }
};

async function getDashboardStats() {
    return await dashboardAPI.getStats();
}

// =====================================================
// Reports API (Admin only)
// =====================================================

async function getReports(type, filters = {}) {
    const params = new URLSearchParams(filters);
    try {
        return await apiCall(`/api/reports/${type}/?${params.toString()}`);
    } catch (error) {
        console.error('Reports not available:', error);
        return { results: [] };
    }
}

// =====================================================
// Test API Connection
// =====================================================

async function testConnection() {
    try {
        console.log('🧪 Testing API connection...');
        const response = await fetch(`${API_BASE_URL}/api/`);
        const data = await response.json();
        console.log('✅ API connection successful:', data);
        return true;
    } catch (error) {
        console.error('❌ API connection failed:', error);
        return false;
    }
}

// Test connection on load
testConnection();

console.log('✅ API.js loaded successfully');
console.log('📡 API Base URL:', API_BASE_URL);