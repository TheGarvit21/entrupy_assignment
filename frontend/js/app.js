/**
 * Main Application Module
 */

class App {
    constructor() {
        this.currentPage = 0;
        this.pageSize = 20;
        this.filters = {
            skip: 0,
            limit: this.pageSize
        };
        this.init();
    }

    /**
     * Initialize application
     */
    init() {
        this.setupEventListeners();
        this.loadProducts();
        this.loadAnalytics();
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Modal handlers
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                e.target.classList.remove('show');
            }
            if (e.target.classList.contains('close')) {
                e.target.closest('.modal').classList.remove('show');
            }
        });

        // Product form
        const addProductForm = document.getElementById('addProductForm');
        if (addProductForm) {
            addProductForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.addProduct();
            });
        }

        // Filters
        document.getElementById('filterBtn')?.addEventListener('click', () => this.applyFilters());
        document.getElementById('resetBtn')?.addEventListener('click', () => this.resetFilters());

        // Pagination
        document.getElementById('prevBtn')?.addEventListener('click', () => this.previousPage());
        document.getElementById('nextBtn')?.addEventListener('click', () => this.nextPage());

        // Refresh data
        document.getElementById('refreshDataBtn')?.addEventListener('click', () => this.refreshAllData());

        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const sectionId = link.getAttribute('href').substring(1);
                this.navigateTo(sectionId);
            });
        });
    }

    /**
     * Load products with pagination
     */
    async loadProducts() {
        try {
            UI.showLoading();
            const params = {
                skip: this.filters.skip,
                limit: this.filters.limit,
                ...Object.fromEntries(
                    Object.entries({
                        source: document.getElementById('sourceFilter')?.value,
                        category: document.getElementById('categoryFilter')?.value,
                        min_price: document.getElementById('minPrice')?.value,
                        max_price: document.getElementById('maxPrice')?.value
                    }).filter(([_, v]) => v)
                )
            };

            const response = await API.getProducts(params);

            UI.renderProducts(response.items);
            UI.updatePagination(response.total, response.page, response.page_size);
            UI.updateCategoryFilter(response.items);

            this.currentPage = response.page;
        } catch (error) {
            UI.toast('Failed to load products: ' + error.message, 'error');
        } finally {
            UI.hideLoading();
        }
    }

    /**
     * Add new product
     */
    async addProduct() {
        try {
            const productData = {
                external_id: document.getElementById('productId').value,
                source: document.getElementById('productSource').value,
                name: document.getElementById('productName').value,
                category: document.getElementById('productCategory').value,
                current_price: parseFloat(document.getElementById('productPrice').value),
                url: document.getElementById('productUrl').value,
                description: document.getElementById('productDescription').value,
                currency: 'USD'
            };

            // Validate
            if (!productData.external_id || !productData.source || !productData.name || !productData.current_price) {
                UI.toast('Please fill in all required fields', 'error');
                return;
            }

            UI.showLoading();
            await API.createProduct(productData);

            UI.toast('Product added successfully', 'success');
            document.getElementById('addProductForm').reset();
            this.loadProducts();
        } catch (error) {
            UI.toast('Failed to add product: ' + error.message, 'error');
        } finally {
            UI.hideLoading();
        }
    }

    /**
     * Apply filters
     */
    applyFilters() {
        this.filters.skip = 0;
        this.currentPage = 0;
        this.loadProducts();
    }

    /**
     * Reset filters
     */
    resetFilters() {
        document.getElementById('searchInput').value = '';
        document.getElementById('sourceFilter').value = '';
        document.getElementById('categoryFilter').value = '';
        document.getElementById('minPrice').value = '';
        document.getElementById('maxPrice').value = '';
        this.applyFilters();
    }

    /**
     * Next page
     */
    nextPage() {
        this.filters.skip += this.pageSize;
        this.loadProducts();
    }

    /**
     * Previous page
     */
    previousPage() {
        this.filters.skip = Math.max(0, this.filters.skip - this.pageSize);
        this.loadProducts();
    }

    /**
     * Load analytics
     */
    async loadAnalytics() {
        try {
            UI.showLoading();
            const stats = await API.getAnalytics();

            UI.updateStats(stats);
            UI.renderSourceChart(stats);
            UI.renderCategoryStats(stats);

            // Update analytics section
            document.getElementById('sourceStats').innerHTML = this.renderStatsTable(
                stats.products_by_source || {}
            );
        } catch (error) {
            console.error('Failed to load analytics:', error);
        } finally {
            UI.hideLoading();
        }
    }

    /**
     * Render stats table
     */
    renderStatsTable(stats) {
        return Object.entries(stats).map(([key, value]) => `
            <div class="stat-row">
                <span>${this.capitalizeFirstLetter(key)}</span>
                <span><strong>${typeof value === 'object' ? value.count : value}</strong></span>
            </div>
        `).join('');
    }

    /**
     * Refresh all data
     */
    async refreshAllData() {
        try {
            UI.showLoading();
            await this.loadProducts();
            await this.loadAnalytics();
            UI.toast('Data refreshed successfully', 'success');
        } catch (error) {
            UI.toast('Failed to refresh data: ' + error.message, 'error');
        } finally {
            UI.hideLoading();
        }
    }

    /**
     * Navigate to section
     */
    navigateTo(sectionId) {
        document.querySelectorAll('.section').forEach(s => s.style.display = 'none');
        const section = document.getElementById(sectionId);
        if (section) {
            section.style.display = 'block';
            section.scrollIntoView({ behavior: 'smooth' });
        }

        // Reload data if needed
        if (sectionId === 'analytics') {
            this.loadAnalytics();
        } else if (sectionId === 'products') {
            this.loadProducts();
        }
    }

    /**
     * Capitalize first letter
     */
    capitalizeFirstLetter(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});
