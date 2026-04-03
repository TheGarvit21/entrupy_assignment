/**
 * Main Application Module
 */

class App {
    constructor() {
        this.currentPage = 0;
        this.pageSize = 20;
        this.user = null;
        this.filters = {
            skip: 0,
            limit: this.pageSize
        };
        this.init();
    }

    /**
     * Initialize application
     */
    async init() {
        this.setupEventListeners();
        await this.checkAuth();
        if (this.user) {
            this.loadProducts();
            this.loadAnalytics();
        }
    }

    /**
     * Check if user is logged in
     */
    async checkAuth() {
        try {
            this.user = await API.getMe();
            UI.updateAuthUI(this.user);
        } catch (error) {
            this.user = null;
            UI.updateAuthUI(null);
        }
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Close modal buttons
        document.getElementById('closeAuth')?.addEventListener('click', () => {
            UI.hideModal('authModal');
        });

        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                UI.hideModal(e.target.id);
            }
            if (e.target.classList.contains('close')) {
                UI.hideModal(e.target.closest('.modal').id);
            }
        });

        // Add Product Modal trigger
        document.getElementById('openAddProductBtn')?.addEventListener('click', () => {
            UI.showModal('addProductModal');
        });

        // Add Product form submission
        document.getElementById('addProductForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.addProduct();
        });

        // App Start trigger
        document.getElementById('startBtn')?.addEventListener('click', () => {
            UI.showModal('authModal');
        });

        // Logout
        document.getElementById('logoutBtn')?.addEventListener('click', () => {
            this.logout();
        });

        // Auth view switching via inline links
        document.getElementById('goToRegister')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.switchAuthView('register');
        });
        document.getElementById('goToLogin')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.switchAuthView('login');
        });

        // Form submissions
        document.getElementById('loginForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.login();
        });

        document.getElementById('registerForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.register();
        });

        // Filter Actions
        document.getElementById('filterBtn')?.addEventListener('click', () => this.applyFilters());
        document.getElementById('resetBtn')?.addEventListener('click', () => this.resetFilters());
        document.getElementById('prevBtn')?.addEventListener('click', () => this.previousPage());
        document.getElementById('nextBtn')?.addEventListener('click', () => this.nextPage());
        document.getElementById('refreshDataBtn')?.addEventListener('click', () => this.refreshAllData());

        // Nav Logic
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const sectionId = link.getAttribute('href').substring(1);
                this.navigateTo(sectionId);
            });
        });
    }

    /**
     * Sign-in logic
     */
    async login() {
        const email = document.getElementById('loginEmail').value;
        const password = document.getElementById('loginPassword').value;
        const err = document.getElementById('authError');
        
        try {
            UI.showLoading();
            await API.login(email, password);
            this.user = await API.getMe();
            UI.updateAuthUI(this.user);
            UI.hideModal('authModal');
            UI.toast('Access granted. Welcome back.', 'success');
            this.loadProducts();
            this.loadAnalytics();
        } catch (e) {
            const errBox = document.getElementById('authError');
            errBox.textContent = e.message;
            errBox.classList.remove('hidden');
        } finally {
            UI.hideLoading();
        }
    }

    /**
     * Sign-up logic — registers then redirects to login
     */
    async register() {
        const email = document.getElementById('regEmail').value;
        const password = document.getElementById('regPassword').value;
        const errBox = document.getElementById('authError');

        try {
            UI.showLoading();
            await API.register(email, password);

            // Redirect to login view with success hint
            this.switchAuthView('login');

            // Pre-fill email for convenience
            const loginEmailField = document.getElementById('loginEmail');
            if (loginEmailField) loginEmailField.value = email;

            // Show success message
            if (errBox) {
                errBox.textContent = '✓ Account created! Sign in to continue.';
                errBox.style.background = 'rgba(16, 185, 129, 0.08)';
                errBox.style.borderColor = 'rgba(16, 185, 129, 0.2)';
                errBox.style.color = '#10b981';
                errBox.classList.remove('hidden');
            }
        } catch (e) {
            if (errBox) {
                errBox.textContent = e.message;
                errBox.style.background = '';
                errBox.style.borderColor = '';
                errBox.style.color = '';
                errBox.classList.remove('hidden');
            }
        } finally {
            UI.hideLoading();
        }
    }

    /**
     * Sign-out logic
     */
    async logout() {
        try {
            await API.logout();
            this.user = null;
            UI.updateAuthUI(null);
            UI.toast('Session terminated.', 'info');
        } catch (e) {
            UI.toast('Sign-out failed', 'error');
        }
    }

    /**
     * Switch between login/register views in the two-panel modal
     */
    switchAuthView(view) {
        const loginView = document.getElementById('loginView');
        const registerView = document.getElementById('registerView');
        const errBox = document.getElementById('authError');
        if (errBox) errBox.classList.add('hidden');

        if (view === 'login') {
            loginView.classList.remove('hidden');
            registerView.classList.add('hidden');
        } else {
            loginView.classList.add('hidden');
            registerView.classList.remove('hidden');
        }
    }

    /**
     * Create listing logic
     */
    async addProduct() {
        try {
            const data = {
                external_id: document.getElementById('productId').value,
                source: document.getElementById('productSource').value,
                name: document.getElementById('productName').value,
                category: document.getElementById('productCategory').value,
                current_price: parseFloat(document.getElementById('productPrice').value),
                url: document.getElementById('productUrl').value,
                description: document.getElementById('productDescription').value,
                currency: 'USD'
            };

            UI.showLoading();
            await API.createProduct(data);
            UI.toast('Listing successfully registered.', 'success');
            UI.hideModal('addProductModal');
            document.getElementById('addProductForm').reset();
            this.loadProducts();
            this.loadAnalytics();
        } catch (e) {
            UI.toast('Registration failed: ' + e.message, 'error');
        } finally {
            UI.hideLoading();
        }
    }

    async loadProducts() {
        try {
            const source = document.getElementById('sourceFilter').value;
            const category = document.getElementById('categoryFilter').value;
            const minPrice = document.getElementById('minPrice').value;
            const maxPrice = document.getElementById('maxPrice').value;

            const params = {
                skip: this.filters.skip,
                limit: this.pageSize
            };

            if (source) params.source = source;
            if (category) params.category = category;
            if (minPrice) params.min_price = minPrice;
            if (maxPrice) params.max_price = maxPrice;

            const res = await API.getProducts(params);
            UI.renderProducts(res.items);
            UI.updatePagination(res.total, res.page, res.page_size);
            UI.updateCategoryFilter(res.items);
        } catch (e) {
            console.error('Data pull error:', e);
        }
    }

    async loadAnalytics() {
        try {
            const stats = await API.getAnalytics();
            UI.updateStats(stats);
            UI.renderSourceChart(stats);
            UI.renderCategoryStats(stats);
            UI.renderAnalyticsText(stats);
        } catch (e) {
            console.error('Analytics pull error:', e);
        }
    }

    applyFilters() { this.filters.skip = 0; this.loadProducts(); }
    
    resetFilters() {
        document.querySelectorAll('.filter-input').forEach(i => i.value = '');
        this.applyFilters();
    }

    nextPage() { this.filters.skip += this.pageSize; this.loadProducts(); }
    previousPage() { this.filters.skip = Math.max(0, this.filters.skip - this.pageSize); this.loadProducts(); }

    async refreshAllData() {
        UI.showLoading();
        await this.loadProducts();
        await this.loadAnalytics();
        UI.hideLoading();
        UI.toast('Data sync complete.', 'success');
    }

    navigateTo(sectionId) {
        document.querySelectorAll('.section').forEach(s => s.classList.remove('active-section'));
        const target = document.getElementById(sectionId);
        if (target) target.classList.add('active-section');
        
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.toggle('active', link.getAttribute('href') === `#${sectionId}`);
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});
