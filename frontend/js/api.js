/**
 * API Communication Module
 */

const API_BASE_URL = window.location.hostname === '127.0.0.1' 
    ? 'http://127.0.0.1:8000/api' 
    : 'http://localhost:8000/api';

class API {
    /**
     * Make API request
     */
    static async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        const config = {
            ...options,
            headers,
            credentials: 'include' // Always include credentials for cookie-based auth
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || `HTTP ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error(`API Error: ${endpoint}`, error);
            throw error;
        }
    }

    /**
     * Authentication endpoints
     */
    static async login(email, password) {
        return this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
    }

    static async register(email, password) {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
    }

    static async logout() {
        return this.request('/auth/logout', {
            method: 'POST'
        });
    }

    static async getMe() {
        return this.request('/auth/me', {
            method: 'GET'
        });
    }

    /**
     * Product endpoints
     */
    static async getProducts(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/products/?${queryString}`, {
            method: 'GET'
        });
    }

    static async getProduct(id) {
        return this.request(`/products/${id}`, {
            method: 'GET'
        });
    }

    static async createProduct(productData) {
        return this.request('/products/', {
            method: 'POST',
            body: JSON.stringify(productData)
        });
    }

    static async updateProduct(id, updates) {
        return this.request(`/products/${id}`, {
            method: 'PUT',
            body: JSON.stringify(updates)
        });
    }

    static async deleteProduct(id) {
        return this.request(`/products/${id}`, {
            method: 'DELETE'
        });
    }

    static async refreshProduct(id) {
        return this.request(`/products/${id}/refresh`, {
            method: 'POST'
        });
    }

    /**
     * Analytics endpoints
     */
    static async getAnalytics() {
        return this.request('/products/analytics/overview', {
            method: 'GET'
        });
    }
}

// Make API globally available
window.API = API;
