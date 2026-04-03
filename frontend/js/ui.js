/**
 * UI Module - UltraThink Design Implementation
 */

class UI {
    static showLoading() {
        document.getElementById('loadingSpinner').classList.add('show');
    }

    static hideLoading() {
        document.getElementById('loadingSpinner').classList.remove('show');
    }

    static showModal(id) {
        document.getElementById(id).classList.add('show');
    }

    static hideModal(id) {
        document.getElementById(id).classList.remove('show');
    }

    static toast(msg, type = 'info') {
        const t = document.createElement('div');
        t.className = `toast toast-${type}`;
        t.textContent = msg;
        document.body.appendChild(t);
        setTimeout(() => {
            t.style.opacity = '0';
            t.style.transform = 'translateY(10px)';
            setTimeout(() => t.remove(), 300);
        }, 3000);
    }

    /**
     * Multi-phrase cycling typewriter effect for Hero heading
     */
    static initTypewriter() {
        const phrases = [
            { text: "Track Prices.", highlight: false },
            { text: "Beat Competitors.", highlight: false },
            { text: "Move Faster.", highlight: false },
            { text: "Know the Market.", highlight: false },
        ];

        const el = document.getElementById('typewriterHeading');
        if (!el) return;

        // Keep cursor element
        let cursor = el.querySelector('.typewriter-cursor');
        if (!cursor) {
            cursor = document.createElement('span');
            cursor.className = 'typewriter-cursor';
            el.appendChild(cursor);
        }

        let phraseIdx = 0;
        let charIdx = 0;
        let deleting = false;
        let timeout;

        function tick() {
            const phrase = phrases[phraseIdx].text;

            if (!deleting) {
                // Typing
                charIdx++;
                el.textContent = phrase.substring(0, charIdx);
                el.appendChild(cursor);

                if (charIdx === phrase.length) {
                    // Pause at end, then delete
                    timeout = setTimeout(() => { deleting = true; tick(); }, 1800);
                    return;
                }
                timeout = setTimeout(tick, 75);
            } else {
                // Deleting
                charIdx--;
                el.textContent = phrase.substring(0, charIdx);
                el.appendChild(cursor);

                if (charIdx === 0) {
                    deleting = false;
                    phraseIdx = (phraseIdx + 1) % phrases.length;
                    timeout = setTimeout(tick, 400);
                    return;
                }
                timeout = setTimeout(tick, 35);
            }
        }

        clearTimeout(timeout);
        charIdx = 0;
        deleting = false;
        phraseIdx = 0;
        el.textContent = '';
        el.appendChild(cursor);
        setTimeout(tick, 600);
    }

    static updateAuthUI(user) {
        const nav = document.getElementById('mainNavbar');
        const content = document.getElementById('mainAppContent');
        const hero = document.getElementById('landingHero');
        const email = document.getElementById('userEmail');

        if (user) {
            hero.classList.add('hidden');
            hero.classList.remove('active-section');
            nav.classList.remove('hidden');
            content.classList.remove('hidden');
            email.textContent = user.email;
        } else {
            hero.classList.remove('hidden');
            hero.classList.add('active-section');
            nav.classList.add('hidden');
            content.classList.add('hidden');
            email.textContent = '';
            UI.initTypewriter(); // Typewriter only on landing
        }
    }

    static renderProducts(products) {
        const tbody = document.getElementById('productsList');
        if (!products || products.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center empty-state">No listings synced.</td></tr>';
            return;
        }

        tbody.innerHTML = products.map(p => `
            <tr>
                <td>
                    <div class="product-name-link" onclick="UI.showProductDetail(${p.id})">
                        ${p.name || 'Untitled Listing'}
                    </div>
                </td>
                <td><span class="badge source-badge">${p.source}</span></td>
                <td><span style="color: var(--text-mid); font-size: 0.8rem;">${p.category || 'Unsegmented'}</span></td>
                <td><strong style="color: var(--primary); font-weight: 800;">$${(p.current_price || 0).toLocaleString()}</strong></td>
                <td><span style="color: var(--text-low); font-size: 0.8rem;">${new Date(p.updated_at).toLocaleDateString()}</span></td>
                <td class="text-right">
                    <div class="btn-group">
                        <button onclick="UI.refreshProductSync(${p.id})" class="btn btn-sm btn-outline">Sync</button>
                        <button onclick="UI.deleteProductConfirm(${p.id})" class="btn btn-sm btn-outline" style="border-color: rgba(239, 68, 68, 0.2); color: #ef4444;">Drop</button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    static async refreshProductSync(id) {
        try {
            UI.showLoading();
            await API.refreshProduct(id);
            UI.toast('Sync successful.', 'success');
            window.app.loadProducts();
            window.app.loadAnalytics();
        } catch (e) {
            UI.toast('Sync failure: ' + e.message, 'error');
        } finally {
            UI.hideLoading();
        }
    }

    static async showProductDetail(id) {
        try {
            UI.showLoading();
            const p = await API.getProduct(id);

            const historyHtml = (p.price_history || [])
                .sort((a, b) => new Date(b.recorded_at) - new Date(a.recorded_at))
                .slice(0, 8)
                .map((ph, idx) => {
                    const next = p.price_history[idx + 1];
                    let diffHtml = '<span style="color: var(--text-low);">-</span>';
                    if (next) {
                        const d = ((ph.price - next.price) / next.price * 100).toFixed(1);
                        const c = d > 0 ? '#ef4444' : (d < 0 ? '#10b981' : 'inherit');
                        diffHtml = `<span style="color: ${c}; font-weight: 800;">${d > 0 ? '↑' : '↓'} ${Math.abs(d)}%</span>`;
                    }
                    return `
                        <tr>
                            <td>${new Date(ph.recorded_at).toLocaleString()}</td>
                            <td>$${ph.price.toLocaleString()}</td>
                            <td>${diffHtml}</td>
                        </tr>
                    `;
                }).join('');

            document.getElementById('detailTitle').textContent = p.name;
            document.getElementById('detailContent').innerHTML = `
                <div class="product-info-grid">
                    <div class="info-item">
                        <label>Current Valuation</label>
                        <span class="price-large">$${p.current_price.toLocaleString()}</span>
                    </div>
                    <div class="info-item">
                        <label>Asset Origin</label>
                        <span style="color: white; font-weight: 700;">${p.source}</span>
                    </div>
                    <div class="info-item">
                        <label>Category Segment</label>
                        <span style="color: white;">${p.category || 'N/A'}</span>
                    </div>
                    <div class="info-item">
                        <label>Internal ID</label>
                        <span style="color: var(--text-low); font-size: 0.8rem;">${p.external_id}</span>
                    </div>
                </div>
                
                <div style="margin-bottom: 2.5rem; padding: 1.5rem; background: #080808; border-radius: 12px; border: 1px solid #111;">
                    <label style="display: block; font-size: 0.7rem; font-weight: 800; color: var(--text-low); text-transform: uppercase; margin-bottom: 0.5rem;">Asset Description</label>
                    <p style="color: var(--text-mid); font-size: 0.95rem;">${p.description || 'No strategic description available.'}</p>
                </div>

                <div class="price-history">
                    <h3 style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--text-low); margin-bottom: 1.5rem;">Fluctuation History</h3>
                    <table style="width: 100%;">
                        <thead>
                            <tr><th>Timestamp</th><th>Valuation</th><th>Delta</th></tr>
                        </thead>
                        <tbody>${historyHtml}</tbody>
                    </table>
                </div>
            `;
            UI.showModal('detailModal');
        } catch (e) {
            UI.toast('Detail pull error: ' + e.message, 'error');
        } finally {
            UI.hideLoading();
        }
    }

    static async deleteProductConfirm(id) {
        if (!confirm('Drop this asset from intelligence monitoring?')) return;
        try {
            UI.showLoading();
            await API.deleteProduct(id);
            UI.toast('Asset dropped.', 'info');
            window.app?.loadProducts();
            window.app?.loadAnalytics();
        } catch (e) {
            UI.toast('Drop failed', 'error');
        } finally {
            UI.hideLoading();
        }
    }

    static updateStats(s) {
        document.getElementById('totalProducts').textContent = s.total_products || 0;
        document.getElementById('totalSources').textContent = Object.keys(s.products_by_source || {}).length;
        document.getElementById('priceChanges').textContent = s.total_price_changes_today || 0;
        
        const categories = Object.values(s.avg_price_by_category || {});
        const avg = categories.length ? categories.reduce((sum, c) => sum + c.average, 0) / categories.length : 0;
        document.getElementById('avgPrice').textContent = `$${Math.round(avg).toLocaleString()}`;
    }

    static renderSourceChart(s) {
        const c = document.getElementById('sourceChart');
        const sources = s.products_by_source || {};
        const max = Math.max(...Object.values(sources), 1);
        c.innerHTML = Object.entries(sources).map(([name, val]) => `
            <div class="chart-bar-container">
                <div class="bar" style="height: ${Math.max((val / max) * 100, 5)}%;">
                    <span class="bar-value">${val}</span>
                </div>
                <span class="bar-label">${name}</span>
            </div>
        `).join('');
    }

    static renderCategoryStats(s) {
        const c = document.getElementById('categoryChart');
        const cats = s.avg_price_by_category || {};
        const max = Math.max(...Object.values(cats).map(x => x.average), 1);
        c.innerHTML = Object.entries(cats).map(([name, data]) => `
            <div class="chart-bar-container">
                <div class="bar secondary" style="height: ${Math.max((data.average / max) * 100, 5)}%;">
                    <span class="bar-value">$${Math.round(data.average / 1000)}k</span>
                </div>
                <span class="bar-label">${name || 'Other'}</span>
            </div>
        `).join('');
    }

    static renderAnalyticsText(s) {
        const srcContainer = document.getElementById('sourceStats');
        const catContainer = document.getElementById('categoryStats');
        
        if (srcContainer) {
            srcContainer.innerHTML = Object.entries(s.products_by_source || {}).map(([name, count]) => `
                <div class="analytics-row">
                    <span class="analytics-row-label">${name}</span>
                    <span class="analytics-row-value">${count} assets</span>
                </div>
            `).join('') || '<p style="color:var(--text-dim);font-size:0.85rem;">No data yet.</p>';
        }

        if (catContainer) {
            catContainer.innerHTML = Object.entries(s.avg_price_by_category || {}).map(([name, data]) => `
                <div class="analytics-row">
                    <span class="analytics-row-label">${name || 'Other'}</span>
                    <span class="analytics-row-value accent">$${data.average.toFixed(0)} avg</span>
                </div>
            `).join('') || '<p style="color:var(--text-dim);font-size:0.85rem;">No data yet.</p>';
        }
    }

    static updatePagination(total, page, size) {
        const pages = Math.ceil(total / size) || 1;
        document.getElementById('pageInfo').textContent = `Volume ${page + 1} / ${pages}`;
        document.getElementById('prevBtn').disabled = page === 0;
        document.getElementById('nextBtn').disabled = page >= pages - 1;
    }

    static updateCategoryFilter(products) {
        const cats = [...new Set(products.map(p => p.category).filter(c => c))];
        const s = document.getElementById('categoryFilter');
        s.innerHTML = '<option value="">All Segments</option>' + cats.map(c => `<option value="${c}">${c}</option>`).join('');
    }
}

window.UI = UI;
