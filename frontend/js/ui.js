/**
 * UI Module - Handle UI updates and interactions
 */

class UI {
    /**
     * Show loading spinner
     */
    static showLoading() {
        document.getElementById('loadingSpinner').classList.add('show');
    }

    /**
     * Hide loading spinner
     */
    static hideLoading() {
        document.getElementById('loadingSpinner').classList.remove('show');
    }

    /**
     * Show modal
     */
    static showModal(modalId) {
        document.getElementById(modalId).classList.add('show');
    }

    /**
     * Hide modal
     */
    static hideModal(modalId) {
        document.getElementById(modalId).classList.remove('show');
    }

    /**
     * Show toast notification
     */
    static toast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#2563eb'};
            color: white;
            border-radius: 8px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
            z-index: 3000;
            animation: slideIn 0.3s;
        `;
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'fadeIn 0.3s reverse';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    /**
     * Render products table
     */
    static renderProducts(products) {
        const tbody = document.getElementById('productsList');

        if (!products || products.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">No products found</td></tr>';
            return;
        }

        tbody.innerHTML = products.map(product => `
            <tr>
                <td>
                    <strong style="cursor:pointer; color:#2563eb;" onclick="UI.showProductDetail(${product.id})">
                        ${product.name || 'N/A'}
                    </strong>
                </td>
                <td><span style="background:#e0e7ff; padding:0.25rem 0.75rem; border-radius:4px; font-size:0.85rem;">${product.source}</span></td>
                <td>${product.category || '-'}</td>
                <td><strong>$${(product.current_price || 0).toFixed(2)}</strong></td>
                <td>${new Date(product.updated_at).toLocaleDateString()}</td>
                <td>
                    <button onclick="UI.editProduct(${product.id})" class="btn btn-primary" style="margin-right:0.5rem;">Edit</button>
                    <button onclick="UI.deleteProductConfirm(${product.id})" class="btn btn-secondary">Delete</button>
                </td>
            </tr>
        `).join('');
    }

    /**
     * Show product detail modal
     */
    static async showProductDetail(productId) {
        try {
            UI.showLoading();
            const product = await API.getProduct(productId);

            const priceHistoryHtml = (product.price_history || [])
                .sort((a, b) => new Date(b.recorded_at) - new Date(a.recorded_at))
                .slice(0, 10)
                .map((ph, idx) => {
                    const prevPrice = product.price_history[idx + 1]?.price;
                    const change = prevPrice ? ((ph.price - prevPrice) / prevPrice * 100).toFixed(2) : 0;
                    const changeClass = change > 0 ? 'price-up' : 'price-down';

                    return `
                        <tr>
                            <td>${new Date(ph.recorded_at).toLocaleString()}</td>
                            <td>$${ph.price.toFixed(2)}</td>
                            <td class="${changeClass}">${change > 0 ? '+' : ''}${change}%</td>
                        </tr>
                    `;
                }).join('');

            document.getElementById('detailTitle').textContent = product.name;
            document.getElementById('detailContent').innerHTML = `
                <div>
                    <p><strong>Source:</strong> ${product.source}</p>
                    <p><strong>Category:</strong> ${product.category || 'N/A'}</p>
                    <p><strong>Current Price:</strong> <strong style="font-size:1.5rem;color:#2563eb;">$${product.current_price.toFixed(2)}</strong></p>
                    <p><strong>URL:</strong> <a href="${product.url}" target="_blank">${product.url || 'N/A'}</a></p>
                    <p><strong>Description:</strong> ${product.description || 'N/A'}</p>
                    <p><strong>Last Updated:</strong> ${new Date(product.updated_at).toLocaleString()}</p>
                </div>

                ${priceHistoryHtml ? `
                    <div class="price-history">
                        <h3>Price History (Last 10 entries)</h3>
                        <table>
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Price</th>
                                    <th>Change %</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${priceHistoryHtml}
                            </tbody>
                        </table>
                    </div>
                ` : ''}
            `;

            UI.showModal('detailModal');
        } catch (error) {
            UI.toast('Failed to load product details: ' + error.message, 'error');
        } finally {
            UI.hideLoading();
        }
    }

    /**
     * Delete product with confirmation
     */
    static async deleteProductConfirm(productId) {
        if (!confirm('Are you sure you want to delete this product?')) return;

        try {
            UI.showLoading();
            await API.deleteProduct(productId);
            UI.toast('Product deleted successfully', 'success');
            // Reload products
            window.app?.loadProducts();
        } catch (error) {
            UI.toast('Failed to delete: ' + error.message, 'error');
        } finally {
            UI.hideLoading();
        }
    }

    /**
     * Edit product placeholder
     */
    static editProduct(productId) {
        UI.toast('Edit functionality coming soon', 'info');
    }

    /**
     * Update dashboard statistics
     */
    static updateStats(stats) {
        document.getElementById('totalProducts').textContent = stats.total_products || 0;

        const sourceCount = Object.keys(stats.products_by_source || {}).length;
        document.getElementById('totalSources').textContent = sourceCount;

        document.getElementById('priceChanges').textContent = stats.total_price_changes_today || 0;

        const avgPrice = Object.values(stats.avg_price_by_category || {})
            .reduce((sum, cat) => sum + (cat.average || 0), 0) /
            (Object.keys(stats.avg_price_by_category || {}).length || 1);
        document.getElementById('avgPrice').textContent = `$${avgPrice.toFixed(2)}`;
    }

    /**
     * Render source statistics chart
     */
    static renderSourceChart(stats) {
        const container = document.getElementById('sourceChart');
        const sources = stats.products_by_source || {};

        const maxCount = Math.max(...Object.values(sources), 1);

        container.innerHTML = Object.entries(sources).map(([source, count]) => {
            const height = (count / maxCount) * 100;
            return `
                <div style="
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    flex: 1;
                ">
                    <div class="bar" style="height: ${Math.max(height, 20)}%;">
                        <div class="bar-value">${count}</div>
                    </div>
                    <div class="bar-label">${source}</div>
                </div>
            `;
        }).join('');
    }

    /**
     * Render category statistics
     */
    static renderCategoryStats(stats) {
        const container = document.getElementById('categoryChart');
        const categories = stats.avg_price_by_category || {};

        if (Object.keys(categories).length === 0) {
            container.innerHTML = '<p style="text-align:center;color:#64748b;">No category data available</p>';
            return;
        }

        const maxPrice = Math.max(...Object.values(categories).map(c => c.average), 1);

        container.innerHTML = Object.entries(categories).map(([category, data]) => {
            const height = (data.average / maxPrice) * 100;
            return `
                <div style="
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    flex: 1;
                    font-size: 0.85rem;
                ">
                    <div class="bar" style="height: ${Math.max(height, 20)}%;">
                        <div class="bar-value">$${data.average.toFixed(0)}</div>
                    </div>
                    <div class="bar-label">${category || 'Other'}</div>
                </div>
            `;
        }).join('');
    }

    /**
     * Update pagination
     */
    static updatePagination(total, page, pageSize) {
        const totalPages = Math.ceil(total / pageSize);
        document.getElementById('pageInfo').textContent = `Page ${page + 1} of ${totalPages}`;
        document.getElementById('prevBtn').disabled = page === 0;
        document.getElementById('nextBtn').disabled = page >= totalPages - 1;
    }

    /**
     * Populate category filter from products
     */
    static updateCategoryFilter(products) {
        const categories = [...new Set(products
            .map(p => p.category)
            .filter(c => c))];

        const select = document.getElementById('categoryFilter');
        const currentValue = select.value;

        select.innerHTML = '<option value="">All Categories</option>' +
            categories.map(cat => `<option value="${cat}">${cat}</option>`).join('');

        select.value = currentValue;
    }
}

// Make UI globally available
window.UI = UI;
