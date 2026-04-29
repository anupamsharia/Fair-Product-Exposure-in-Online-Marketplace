/**
 * app.js — FairCart Customer Storefront  (Performance Edition)
 *
 * Key improvements:
 *  - Server-side search + category filter (no more downloading all 500 products)
 *  - Pagination / "Load More" — 40 products per page
 *  - Batched impression tracking — 1 POST per page, not 1 per card
 *  - Debounced search (300 ms) so we don't hammer the API every keystroke
 *  - Lazy image loading via loading="lazy"
 */

document.addEventListener('DOMContentLoaded', () => {
    if (typeof requireCustomer === 'function') requireCustomer();

    renderProducts(1);          // load first page

    // ── Category filter ──────────────────────────────────────
    const categorySelect = document.getElementById('category-filter');
    if (categorySelect) {
        categorySelect.addEventListener('change', () => {
            currentPage = 1;
            allProducts = [];
            renderProducts(1);
        });
    }

    // ── Debounced search ─────────────────────────────────────
    const searchInput = document.getElementById('search-input');
    let searchTimer = null;
    if (searchInput) {
        searchInput.addEventListener('keyup', () => {
            clearTimeout(searchTimer);
            searchTimer = setTimeout(() => {
                currentPage = 1;
                allProducts = [];
                renderProducts(1);
            }, 300);   // wait 300 ms after typing stops
        });

        const searchBtn = document.getElementById('search-btn');
        if (searchBtn) {
            searchBtn.addEventListener('click', () => {
                currentPage = 1;
                allProducts = [];
                renderProducts(1);
            });
        }
    }
});

// ── State ─────────────────────────────────────────────────
let currentPage = 1;
let totalProducts = 0;
let allProducts = [];   // accumulated for display
const PAGE_SIZE = 40;
const APP_API_ORIGIN = typeof getFairCartApiOrigin === "function"
    ? getFairCartApiOrigin()
    : (window.location.port === "5000" ? "" : `${window.location.protocol === "https:" ? "https:" : "http:"}//${window.location.hostname || "localhost"}:5000`);
const escapeInlineString = (value) => String(value || '').replace(/\\/g, "\\\\").replace(/'/g, "\\'");
const encodeCartMeta = (product) => encodeURIComponent(JSON.stringify({
    seller_id: product.seller_id || '',
    product_id: product._id || '',
    image_url: product.image || product.image_url || (product.image_urls && product.image_urls[0]) || ''
}));

const formatPrice = (price) => `Rs. ${Number(price || 0).toLocaleString('en-IN')}`;

function fairExposureMeta(product) {
    const impressions = Number(product.impressions || 0);
    const finalScore = Math.round((Number(product.final_score || 0)) * 100);
    const bucket = product.exposure_bucket || (
        impressions === 0 ? "new" :
        impressions < 25 ? "low_exposure" :
        impressions < 100 ? "growing" :
        "established"
    );

    const labels = {
        new: "New Discovery",
        low_exposure: "Low-View Boost",
        growing: "Balanced Growth",
        established: "Quality Ranked"
    };

    return {
        bucket,
        score: Number.isFinite(finalScore) ? finalScore : 0,
        label: labels[bucket] || "Fair Ranked",
        reason: product.fair_exposure_reason || "Balanced by engagement, quality, and seller diversity"
    };
}

function htmlEscape(value) {
    if (window.FairCartCustomer?.escapeHtml) return window.FairCartCustomer.escapeHtml(value);
    return String(value || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// ── Main render ───────────────────────────────────────────
async function renderProducts(page = 1) {
    const grid = document.getElementById('product-grid');
    if (!grid) return;

    // Show loading skeletons
    if (page === 1) {
        grid.innerHTML = buildSkeletons(8); // Show 8 skeleton cards
    }

    try {
        const category = document.getElementById('category-filter')?.value || 'All';
        const search = document.getElementById('search-input')?.value?.trim() || '';

        // Determine endpoint: Use specialized search if query exists
        const endpoint = search ? '/api/product/search' : '/api/product/products';
        const queryParam = search ? 'q' : 'search';

        const params = new URLSearchParams({
            page,
            limit: PAGE_SIZE,
            ...(category && category !== 'All' ? { category } : {}),
            [queryParam]: search
        });

        const API_ORIGIN = APP_API_ORIGIN;

        // Add timeout for slow network (8 seconds)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 8000);

        const res = await fetch(`${API_ORIGIN}${endpoint}?${params}`, {
            signal: controller.signal,
            cache: 'no-store'
        });
        clearTimeout(timeoutId);

        if (!res.ok) {
            let errorMsg = 'API error';
            if (res.status === 404) errorMsg = 'API endpoint not found';
            else if (res.status === 500) errorMsg = 'Server error';
            else if (res.status === 429) errorMsg = 'Too many requests, please try again later';
            throw new Error(`HTTP ${res.status}: ${errorMsg}`);
        }

        const data = await res.json();
        console.log('API response:', { total: data.total, productsCount: data.products?.length, page });

        const newProducts = data.products || [];
        totalProducts = data.total || 0;
        allProducts = [...allProducts, ...newProducts];
        currentPage = page;

        // ── Batch-track impressions for this page (1 request, not 40) ──
        if (newProducts.length > 0) {
            batchTrackImpressions(newProducts.map(p => p._id));
        }

        // ── Render cards ─────────────────────────────────────
        if (page === 1) grid.innerHTML = '';

        console.log('allProducts length:', allProducts.length, 'newProducts length:', newProducts.length);

        if (allProducts.length === 0) {
            grid.innerHTML = `
                <div style="grid-column:1/-1; text-align:center; padding:3rem;">
                    <p style="color:var(--text-secondary); font-size:1.2rem; margin-bottom:1rem;">
                        No products found.
                    </p>
                    <button onclick="renderProducts(1)"
                        style="background:var(--primary-color); color:white; border:none;
                               padding:0.75rem 1.5rem; border-radius:8px; cursor:pointer;">
                        Try Again
                    </button>
                </div>`;
            removePagination();
            return;
        }

        newProducts.forEach(product => {
            grid.appendChild(buildCard(product));
        });
        if (typeof window.renderCustomerHub === "function") {
            window.renderCustomerHub(allProducts);
        }

        // ── Load More button ─────────────────────────────────
        removePagination();
        if (allProducts.length < totalProducts) {
            const btn = document.createElement('div');
            btn.id = 'load-more-btn';
            btn.style.cssText = 'grid-column:1/-1; text-align:center; margin:1.5rem 0;';
            btn.innerHTML = `
                <button onclick="loadMore()"
                    style="background:linear-gradient(135deg,var(--primary-color),#3a7bd5);
                           color:white; border:none; padding:0.9rem 2.5rem;
                           border-radius:12px; font-size:1rem; font-weight:600;
                           cursor:pointer; transition:all 0.2s;">
                    Load More &nbsp;(${allProducts.length} / ${totalProducts})
                </button>`;
            grid.appendChild(btn);
        } else if (totalProducts > PAGE_SIZE) {
            // Show "all loaded" message
            const msg = document.createElement('div');
            msg.id = 'load-more-btn';
            msg.style.cssText = 'grid-column:1/-1; text-align:center; color:var(--text-secondary); padding:1rem;';
            msg.textContent = `\u2713 All ${totalProducts} products loaded`;
            grid.appendChild(msg);
        }

    } catch (err) {
        console.error('Product load error:', err);

        let userMessage = 'Could not load products. ';
        if (err.name === 'AbortError') {
            userMessage += 'Request timed out. Please check your network connection.';
        } else if (err.message.includes('HTTP 5')) {
            userMessage += 'Server error. Please try again later.';
        } else if (err.message.includes('HTTP 4')) {
            userMessage += 'Client error. Please check your request.';
        } else {
            userMessage += 'Is the backend running on port 5000?';
        }

        grid.innerHTML = `
            <div style="grid-column:1/-1; text-align:center; padding:3rem;">
                <p style="color:#ef4444; font-size:1.2rem; margin-bottom:1rem;">
                    \u274C ${userMessage}
                </p>
                <div style="display:flex; gap:1rem; justify-content:center;">
                    <button onclick="renderProducts(${page})"
                        style="background:var(--primary-color); color:white; border:none;
                               padding:0.75rem 1.5rem; border-radius:8px; cursor:pointer;">
                        Retry
                    </button>
                    <button onclick="renderProducts(1)"
                        style="background:transparent; color:var(--text-secondary);
                               border:1px solid var(--border-color); padding:0.75rem 1.5rem;
                               border-radius:8px; cursor:pointer;">
                        Back to First Page
                    </button>
                </div>
            </div>`;
    }
}

// ── Load next page ─────────────────────────────────────────
window.loadMore = () => renderProducts(currentPage + 1);

// ── Build a single product card DOM element ────────────────
function buildCard(product) {
    let mediaHTML = '';
    const imgSrc = product.image || product.image_url || (product.image_urls && product.image_urls[0]) || '';
    if (imgSrc) {
        mediaHTML = `<img src="${imgSrc}"
                          loading="lazy"
                          style="width:100%;height:100%;object-fit:cover;"
                          onerror="this.style.display='none';this.parentNode.innerHTML='\ud83d\udce6';">`;
    } else {
        mediaHTML = product.icon || '\ud83d\udce6';
    }

    const sellerName = product.seller_name ||
        (product.seller_id ? product.seller_id.split('@')[0].toUpperCase() : 'SELLER');
    const cartMeta = encodeCartMeta(product);
    const encodedProduct = window.FairCartCustomer?.encodeProduct
        ? window.FairCartCustomer.encodeProduct(product)
        : encodeURIComponent(JSON.stringify(product));
    const isSaved = window.FairCartCustomer?.isSaved?.(product) || false;
    const safeProductName = escapeInlineString(product.name);
    const productPrice = Number(product.price) || 0;

    const impressions = product.impressions || 0;
    const clicks = product.clicks || 0;
    const userRole = (getCurrentUser() || {}).role || 'guest';
    const isSpecialUser = userRole === 'seller' || userRole === 'admin';

    const fairMeta = fairExposureMeta(product);
    let badges = '';
    if (impressions < 20) badges += `<span class="badge" style="background:#fef9c3; color:#a16207; border:1px solid #fef3c7;">New</span>`;
    if (impressions < 60) badges += `<span class="badge" style="background:rgba(108,99,255,0.08);color:#6c63ff;border:1px solid rgba(108,99,255,0.18);">${fairMeta.label}</span>`;

    // Fairness Boost badge - ONLY visible to Seller or Admin
    if (isSpecialUser && (product.final_score > 0.5 || impressions < 50)) {
        badges += `<span class="badge badge-boosted">🚀 Boosted</span>`;
    }

    if (clicks > 10) badges += `<span class="badge" style="background:#dcfce7; color:#15803d;">⭐ Popular</span>`;

    if (isSpecialUser && product.fraud_flag) {
        badges += `<span class="badge" style="background:#fee2e2; color:#ef4444; border:1px solid #fecaca;">⚠ Fraud Risk</span>`;
    }

    if (product.on_sale) badges += `<span class="badge" style="background:rgba(34,197,94,0.15);color:#22c55e;border:1px solid #22c55e;">SALE</span>`;

    const priceHtml = product.on_sale && product.original_price
        ? `<div class="product-price" style="color:#22c55e;">
               ${formatPrice(product.price)}
               <span style="color:#9ca3af;text-decoration:line-through;font-size:0.85rem;margin-left:0.4rem;">
                   ${formatPrice(product.original_price)}
               </span>
           </div>`
        : `<div class="product-price">${formatPrice(product.price)}</div>`;

    const card = document.createElement('div');
    card.className = 'product-card';
    card.innerHTML = `
        <div class="product-image-placeholder" style="cursor:pointer;"
             onclick="goToProduct('${product._id}')">
            ${mediaHTML}
        </div>
        <div class="product-info">
            <div class="product-name" style="cursor:pointer;"
                 onclick="goToProduct('${product._id}')">${htmlEscape(product.name)}</div>
            ${priceHtml}
            <div class="seller-info">
                <span>Sold by:</span>
                <span class="seller-name">${htmlEscape(sellerName)}</span>
            </div>
            <div class="badges-container">
                ${badges}
                <span class="badge" title="${htmlEscape(fairMeta.reason)}" style="background:rgba(34,197,94,0.15);color:#15803d;border:1px solid rgba(34,197,94,0.2);">
                    Fair Score ${fairMeta.score}
                </span>
            </div>
        </div>
        <div class="product-card-actions">
            <button class="btn-cart"
                onclick="addToCart('${safeProductName}', ${productPrice}, JSON.parse(decodeURIComponent('${cartMeta}')))">
                Add to Cart
            </button>
            <button class="btn-save ${isSaved ? 'is-saved' : ''}" type="button"
                onclick="FairCartCustomer.toggleSavedFromEncoded('${encodedProduct}', event)">
                ${isSaved ? 'Saved' : 'Save'}
            </button>
        </div>
    `;
    return card;
}

// ── Navigate to product detail page ───────────────────────
window.goToProduct = (productId) => {
    trackStat(productId, 'clicks');
    window.location.href = `product.html?id=${productId}`;
};
window.trackClickAndRedirect = window.goToProduct;

// ── Batch impression tracking — 1 POST for the whole page ──
function batchTrackImpressions(ids) {
    if (!ids || ids.length === 0) return;

    const API_ORIGIN = APP_API_ORIGIN;

    // Store in localStorage as fallback if network fails
    const storeFallback = () => {
        try {
            const key = 'pending_impressions';
            const existing = JSON.parse(localStorage.getItem(key) || '[]');
            const newEntries = ids.map(id => ({ id, timestamp: Date.now() }));
            localStorage.setItem(key, JSON.stringify([...existing, ...newEntries].slice(-100))); // Keep last 100
        } catch (e) {
            // Silently fail
        }
    };

    fetch(`${API_ORIGIN}/api/product/batch-impression`, {
        method: 'POST',
        cache: 'no-store',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_ids: ids })  // Updated to match backend parameter name
    })
        .then(response => {
            if (!response.ok) {
                storeFallback();
            }
        })
        .catch(() => {
            storeFallback();
        });

    // Try to send any pending impressions from previous failures
    sendPendingImpressions();
}

// ── Send pending impressions from localStorage ─────────────
function sendPendingImpressions() {
    try {
        const key = 'pending_impressions';
        const pending = JSON.parse(localStorage.getItem(key) || '[]');
        if (pending.length === 0) return;

        const API_ORIGIN = APP_API_ORIGIN;
        const ids = pending.map(p => p.id);

        fetch(`${API_ORIGIN}/api/product/batch-impression`, {
            method: 'POST',
            cache: 'no-store',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_ids: ids })
        })
            .then(response => {
                if (response.ok) {
                    localStorage.removeItem(key);
                }
            })
            .catch(() => {
                // Keep in storage for next try
            });
    } catch (e) {
        // Silently fail
    }
}

// ── Single stat tracking (clicks) ─────────────────────────
function trackStat(productId, field) {
    const API_ORIGIN = APP_API_ORIGIN;

    fetch(`${API_ORIGIN}/api/product/increment`, {
        method: 'POST',
        cache: 'no-store',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: productId, field })
    })
        .catch(() => {
            // Store in localStorage as fallback for clicks
            try {
                const key = 'pending_clicks';
                const existing = JSON.parse(localStorage.getItem(key) || '[]');
                const newEntry = { id: productId, field, timestamp: Date.now() };
                localStorage.setItem(key, JSON.stringify([...existing, newEntry].slice(-50))); // Keep last 50
            } catch (e) {
                // Silently fail
            }
        });
}

// ── Skeleton loader cards (shows instantly, no layout shift) ─
function buildSkeletons(n) {
    const s = `
        <div class="product-card" style="opacity:0.4; pointer-events:none; animation: pulse 1.5s infinite;">
            <div class="product-image-placeholder" style="background:#1e293b;"></div>
            <div class="product-info">
                <div style="height:16px;background:#1e293b;border-radius:6px;margin-bottom:8px;"></div>
                <div style="height:14px;background:#1e293b;border-radius:6px;width:60%;"></div>
            </div>
        </div>`;
    return s.repeat(n);
}

function removePagination() {
    const old = document.getElementById('load-more-btn');
    if (old) old.remove();
}
