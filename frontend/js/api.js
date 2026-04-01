/**
 * API Communication Module
 */

const API_BASE_URL = 'http://localhost:8000/api';

let authToken = localStorage.getItem('authToken');

class API {
    /**
     * Make authenticated API request
     */
    static async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (authToken) {
            headers['Authorization'] = `Bearer ${authToken}`;
        }

        const config = {
            ...options,
            headers
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
    static async register(email, password) {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
    }

    static async login(email, password) {
        const response = await this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
        authToken = response.access_token;
        localStorage.setItem('authToken', authToken);
        return response;
    }

    static logout() {
        authToken = null;
        localStorage.removeItem('authToken');
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

    /**
     * Check if user is authenticated
     */
    static isAuthenticated() {
        return !!authToken;
    }
}

// Make API globally available
window.API = API;
