/**
 * FairCart Seller Dashboard Logic (SaaS UI + MongoDB Backend)
 * Upgraded with REAL AI-Powered Product Creation System (Vision + OpenAI)
 */

let globalProducts = [];
let globalOrders = [];
const SELLER_API_ORIGIN = typeof getFairCartApiOrigin === "function"
    ? getFairCartApiOrigin()
    : (window.location.port === "5000" ? "" : `${window.location.protocol === "https:" ? "https:" : "http:"}//${window.location.hostname || "localhost"}:5000`);
let sellerRefreshTimer = null;
let sellerSessionRepairPromise = null;

function getStoredSeller() {
    try {
        return JSON.parse(localStorage.getItem('currentUser') || 'null');
    } catch (e) {
        localStorage.removeItem('currentUser');
        return null;
    }
}

function getSellerAuthToken() {
    try {
        const currentUser = getStoredSeller();
        return localStorage.getItem('faircart_token') || currentUser?.token || "";
    } catch (e) {
        return localStorage.getItem('faircart_token') || "";
    }
}

function sellerAuthHeaders(extraHeaders = {}) {
    const headers = { ...extraHeaders };
    const token = getSellerAuthToken();
    if (token) headers.Authorization = `Bearer ${token}`;
    return headers;
}

function saveSellerSession(user, token) {
    const storedUser = { ...user };
    if (token) {
        storedUser.token = token;
        localStorage.setItem("faircart_token", token);
    }
    localStorage.setItem("currentUser", JSON.stringify(storedUser));
    localStorage.setItem("faircart_user", JSON.stringify(storedUser));
}

function sellerApiOriginCandidates() {
    const protocol = window.location.protocol === "https:" ? "https:" : "http:";
    const candidates = [SELLER_API_ORIGIN];

    if (window.location.hostname === "127.0.0.1") {
        candidates.push(`${protocol}//localhost:5000`);
    } else if (window.location.hostname === "localhost") {
        candidates.push(`${protocol}//127.0.0.1:5000`);
    }

    return [...new Set(candidates)];
}

async function repairSellerSession() {
    if (getSellerAuthToken()) return true;

    const currentUser = getStoredSeller();
    if (!currentUser?.email || currentUser.role !== "seller") return false;

    for (const origin of sellerApiOriginCandidates()) {
        try {
            const res = await fetch(`${origin}/api/auth/me`, {
                cache: "no-store",
                credentials: "include",
                headers: sellerAuthHeaders()
            });
            const data = await res.json().catch(() => ({}));
            if (res.ok && data.user?.role === "seller" && data.token) {
                saveSellerSession(data.user, data.token);
                return true;
            }
        } catch (e) {
            // Try the next local backend host.
        }
    }

    for (const origin of sellerApiOriginCandidates()) {
        try {
            const res = await fetch(`${origin}/api/auth/local-restore`, {
                method: "POST",
                cache: "no-store",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: currentUser.email })
            });
            const data = await res.json().catch(() => ({}));
            if (res.ok && data.user?.role === "seller" && data.token) {
                saveSellerSession(data.user, data.token);
                return true;
            }
        } catch (e) {
            // Local restore is best-effort; the caller will redirect if it fails.
        }
    }

    return false;
}

async function ensureSellerSession() {
    if (getSellerAuthToken()) return true;
    if (!sellerSessionRepairPromise) {
        sellerSessionRepairPromise = repairSellerSession().finally(() => {
            sellerSessionRepairPromise = null;
        });
    }
    return sellerSessionRepairPromise;
}

function handleSellerAuthFailure() {
    if (sellerRefreshTimer) {
        clearInterval(sellerRefreshTimer);
        sellerRefreshTimer = null;
    }
    localStorage.removeItem("currentUser");
    localStorage.removeItem("faircart_user");
    localStorage.removeItem("faircart_token");
    renderDashboardError("Your seller session expired. Please log in again.");
    showToast("Please log in again to load your seller dashboard.");
    setTimeout(() => {
        window.location.href = "login.html";
    }, 1200);
}

document.addEventListener("DOMContentLoaded", () => {
    checkAuth();
    startSellerRealtimeUpdates();
    // Initialize live preview
    if (document.getElementById("view-add")) {
        updateLivePreview();
    }
});

function startSellerRealtimeUpdates() {
    if (sellerRefreshTimer) clearInterval(sellerRefreshTimer);
    sellerRefreshTimer = setInterval(() => {
        if (document.visibilityState === "visible") refreshDashboardData();
    }, 5000);

    document.addEventListener("visibilitychange", () => {
        if (document.visibilityState === "visible") refreshDashboardData();
    });
}

/**
 * Animate a numeric value from start to end
 */
function animateValue(id, start, end, duration) {
    const obj = document.getElementById(id);
    if (!obj) return;

    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        obj.innerHTML = Math.floor(progress * (end - start) + start);
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

function checkAuth() {
    if (typeof requireSeller === 'function') requireSeller();

    const currentUser = getStoredSeller();
    if (!currentUser) return;

    if (document.getElementById("shop-name-display"))
        document.getElementById("shop-name-display").innerText = currentUser.shop_name || currentUser.name;

    if (document.getElementById("seller-name-header"))
        document.getElementById("seller-name-header").innerText = currentUser.name;

    const verifyContainer = document.getElementById("verify-badge-container");
    if (verifyContainer) {
        if (currentUser.verified === false) {
            verifyContainer.innerHTML = `<span class="fc-badge badge-pending"><i class="fas fa-clock"></i> PENDING VERIFICATION</span>`;
            if (document.getElementById("pending-alert")) document.getElementById("pending-alert").style.display = 'flex';
            if (document.getElementById("add-btn")) document.getElementById("add-btn").disabled = true;
            if (document.getElementById("qa-add-btn")) document.getElementById("qa-add-btn").disabled = true;
        } else {
            verifyContainer.innerHTML = `<span class="fc-badge badge-verified"><i class="fas fa-check-circle"></i> VERIFIED SELLER</span>`;
            if (document.getElementById("pending-alert")) document.getElementById("pending-alert").style.display = 'none';
        }
    }

    refreshDashboardData();
}

window.switchView = (viewName) => {
    document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
    document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));

    const navId = `nav-item-${viewName}`;
    const viewId = `view-${viewName}`;

    if (document.getElementById(navId)) document.getElementById(navId).classList.add("active");
    if (document.getElementById(viewId)) document.getElementById(viewId).classList.add("active");

    const titles = {
        'dashboard': 'Dashboard',
        'add': 'Premium Product Creator',
        'products': 'My Products',
        'orders': 'Orders',
        'notifications': 'Notifications'
    };
    if (document.getElementById("page-title")) document.getElementById("page-title").innerText = titles[viewName] || 'Dashboard';

    if (viewName === 'add') updateLivePreview();
    if (window.innerWidth <= 768) closeSidebar();
};

window.openSidebar = () => {
    document.getElementById("sd-sidebar")?.classList.add("open");
    document.getElementById("sidebar-overlay")?.classList.add("open");
};

window.closeSidebar = () => {
    document.getElementById("sd-sidebar")?.classList.remove("open");
    document.getElementById("sidebar-overlay")?.classList.remove("open");
};

window.sellerLogout = (e) => {
    e.preventDefault();
    localStorage.removeItem("currentUser");
    localStorage.removeItem("faircart_user");
    localStorage.removeItem("faircart_token");
    window.location.href = "login.html";
};

async function refreshDashboardData() {
    const currentUser = getStoredSeller();
    if (!currentUser?.email) return;

    try {
        const hasSession = await ensureSellerSession();
        if (!hasSession) {
            handleSellerAuthFailure();
            return;
        }

        const sellerId = encodeURIComponent(currentUser.email);
        const requestOptions = { cache: 'no-store', credentials: 'include', headers: sellerAuthHeaders() };
        const [prodRes, ordRes] = await Promise.all([
            fetch(`${SELLER_API_ORIGIN}/api/product/all-products?seller_id=${sellerId}`, requestOptions),
            fetch(`${SELLER_API_ORIGIN}/api/order/orders?seller_id=${sellerId}`, requestOptions)
        ]);

        if (!prodRes.ok) throw new Error(`Products request failed (${prodRes.status})`);
        if (!ordRes.ok) throw new Error(`Orders request failed (${ordRes.status})`);

        const prodData = await prodRes.json();
        const ordData = await ordRes.json();

        globalProducts = prodData.products || [];
        globalOrders = ordData.orders || [];

        updateStats();
        window.filterProducts();
        window.filterOrders('All');
        generateNotifications();
    } catch (e) {
        console.error("Dashboard Sync Failed:", e);
        if (/\(401\)|Authentication required/i.test(e.message)) {
            handleSellerAuthFailure();
            return;
        }
        renderDashboardError("We couldn't load your seller data. Please check that the backend is running.");
        showToast("Seller dashboard data failed to load.");
    }
}

function renderDashboardError(message) {
    const productGrid = document.getElementById("products-grid");
    const orderList = document.getElementById("orders-list");
    const notifications = document.getElementById("notifications-list");
    const errorHtml = `<div class="empty-state" style="padding:3rem; text-align:center;"><h3>${message}</h3></div>`;

    if (productGrid) productGrid.innerHTML = errorHtml;
    if (orderList) orderList.innerHTML = errorHtml;
    if (notifications) notifications.innerHTML = errorHtml;
}

function updateStats() {
    const totalProducts = globalProducts.length;
    const totalOrders = globalOrders.length;
    const totalImpressions = globalProducts.reduce((sum, p) => sum + (p.impressions || 0), 0);
    const totalClicks = globalProducts.reduce((sum, p) => sum + (p.clicks || 0), 0);

    animateValue("stat-total", 0, totalProducts, 1000);
    animateValue("stat-orders", 0, totalOrders, 1000);
    animateValue("stat-impressions", 0, totalImpressions, 1200);
    animateValue("stat-clicks", 0, totalClicks, 1400);
}

// ─────────────────────────────────────────────────────────────────────────────
//  REAL AI CREATOR LOGIC (API DRIVEN)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Consolidated AI Optimization Flow
 */
window.optimizeListingWithAI = async () => {
    const title = document.getElementById("prod-name").value;
    const desc = document.getElementById("prod-desc").value;
    const price = document.getElementById("prod-price").value;
    const category = document.getElementById("prod-category").value;

    if (!title) {
        showToast("Please enter at least a product name!");
        return;
    }

    showToast("✨ AI is optimizing your listing with category-aware SEO...");
    const reviewBox = document.getElementById("ai-review-box");
    const reviewContent = document.getElementById("ai-review-content");

    try {
        const hasSession = await ensureSellerSession();
        if (!hasSession) {
            handleSellerAuthFailure();
            return;
        }

        const res = await fetch(`${SELLER_API_ORIGIN}/api/ai/bulk-optimize`, {
            method: 'POST',
            cache: 'no-store',
            credentials: 'include',
            headers: sellerAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({
                title,
                description: desc,
                price,
                category: category || "General"
            })
        });
        const data = await res.json().catch(() => ({}));

        if (!res.ok) {
            throw new Error(data.message || `AI request failed (${res.status})`);
        }

        if (data.optimized) {
            data.optimized.keywords = Array.isArray(data.optimized.keywords)
                ? data.optimized.keywords
                : String(data.optimized.keywords || "").split(",").map(v => v.trim()).filter(Boolean);
            data.moderation = data.moderation || { status: "approved", is_fraud: false };
            lastAIResult = data;
            reviewBox.style.display = "block";
            reviewContent.innerHTML = `
                <div style="margin-bottom: 0.8rem;"><strong>Optimized Title:</strong> ${data.optimized.title}</div>
                <div style="margin-bottom: 0.8rem;"><strong>Professional Description:</strong> ${data.optimized.description.substring(0, 150)}...</div>
                <div style="margin-bottom: 0.8rem;"><strong>SEO Keywords:</strong> ${data.optimized.keywords.join(", ")}</div>
                <div style="padding: 0.5rem; background: ${data.moderation.status === 'rejected' ? '#fee2e2' : '#f0fdf4'}; border-radius: 6px; border: 1px solid ${data.moderation.status === 'rejected' ? '#fecaca' : '#dcfce7'};">
                    <strong>Auto-Moderation:</strong> ${data.moderation.status.toUpperCase()} 
                    ${data.moderation.is_fraud ? '<span style="color:red; font-weight:800;">🚩 FRAUD ALERT</span>' : ''}
                </div>
            `;
            reviewBox.scrollIntoView({ behavior: 'smooth' });
        } else {
            throw new Error(data.message || "AI response was missing optimized listing data.");
        }
    } catch (err) {
        console.error("AI Optimization Failed:", err);
        if (/Authentication required|401/i.test(err.message)) {
            handleSellerAuthFailure();
            return;
        }
        showToast(`AI Optimization Failed: ${err.message}`);
        return;
        showToast("❌ AI Optimization Failed.");
    }
};

let lastAIResult = null;
window.acceptAIReview = () => {
    if (!lastAIResult) return;

    document.getElementById("prod-name").value = lastAIResult.optimized.title;
    document.getElementById("prod-desc").value = lastAIResult.optimized.description;
    document.getElementById("seo-keywords").value = lastAIResult.optimized.keywords.join(",");

    // Display Tags for user feedback
    const tagsContainer = document.getElementById("detected-tags-container");
    if (tagsContainer) {
        tagsContainer.innerHTML = lastAIResult.optimized.keywords.map(t => `<span class="ai-tag-sim" style="background:#6c63ff; color:white;">#${t}</span>`).join(" ");
        tagsContainer.parentElement.style.display = "block";
    }

    // Store moderation results for final submission
    window.lastModeration = lastAIResult.moderation;

    document.getElementById("ai-review-box").style.display = "none";
    showToast("✅ AI Suggestions Applied!");
    updateLivePreview();
};

/**
 * Enhanced Media Preview with Multiple Image Support
 * Improved with: file validation, remove buttons, drag-and-drop, progress indicators
 */
let uploadedFiles = []; // Track actual File objects for upload

// Function to remove an image from the uploadedFiles array
function removeImage(index) {
    if (index >= 0 && index < uploadedFiles.length) {
        uploadedFiles.splice(index, 1);
        renderImagePreviews();
        showToast(`Image removed (${uploadedFiles.length} remaining)`);
    }
}

// Function to reorder images (simple swap)
function moveImage(fromIndex, toIndex) {
    if (fromIndex >= 0 && fromIndex < uploadedFiles.length &&
        toIndex >= 0 && toIndex < uploadedFiles.length) {
        const [movedFile] = uploadedFiles.splice(fromIndex, 1);
        uploadedFiles.splice(toIndex, 0, movedFile);
        renderImagePreviews();
        showToast("Image order updated");
    }
}

// Render all image previews
function renderImagePreviews() {
    const previewContainer = document.getElementById("image-previews-container");
    if (!previewContainer) return;

    previewContainer.innerHTML = "";

    if (uploadedFiles.length === 0) {
        previewContainer.innerHTML = `
            <div style="width:100%; text-align:center; padding:1rem; color:var(--fc-text-muted); font-size:0.9rem;">
                No images selected. Click the upload area to add images.
            </div>
        `;
        return;
    }

    uploadedFiles.forEach((file, index) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const imgWrap = document.createElement("div");
            imgWrap.style.cssText = "position:relative; width:80px; height:80px; border-radius:8px; overflow:hidden; border:1px solid var(--fc-border); cursor:move;";
            imgWrap.setAttribute("draggable", "true");
            imgWrap.setAttribute("data-index", index);
            imgWrap.setAttribute("title", `Drag to reorder. ${file.name} (${(file.size / 1024 / 1024).toFixed(2)}MB)`);

            // Add drag event listeners for reordering
            imgWrap.addEventListener("dragstart", (ev) => {
                ev.dataTransfer.setData("text/plain", index.toString());
            });
            imgWrap.addEventListener("dragover", (ev) => ev.preventDefault());
            imgWrap.addEventListener("drop", (ev) => {
                ev.preventDefault();
                const fromIndex = parseInt(ev.dataTransfer.getData("text/plain"));
                const toIndex = index;
                if (fromIndex !== toIndex) {
                    moveImage(fromIndex, toIndex);
                }
            });

            imgWrap.innerHTML = `
                <img src="${e.target.result}" style="width:100%; height:100%; object-fit:cover;">
                <button onclick="removeImage(${index})" style="position:absolute; top:2px; right:2px; width:20px; height:20px; border-radius:50%; background:rgba(0,0,0,0.7); color:white; border:none; cursor:pointer; font-size:12px; display:flex; align-items:center; justify-content:center;">×</button>
                <div style="position:absolute; bottom:0; left:0; right:0; background:rgba(0,0,0,0.7); color:white; font-size:10px; padding:2px; text-align:center; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${file.name.substring(0, 10)}${file.name.length > 10 ? '...' : ''}</div>
            `;
            previewContainer.appendChild(imgWrap);
        };
        reader.readAsDataURL(file);
    });

    // Update the file input to reflect current files (for form reset)
    const fileInput = document.getElementById("prod-images");
    if (fileInput) {
        // Create a new DataTransfer to update files
        const dataTransfer = new DataTransfer();
        uploadedFiles.forEach(file => dataTransfer.items.add(file));
        fileInput.files = dataTransfer.files;
    }
}

window.handleMultipleMediaPreview = async (input) => {
    if (input.files && input.files.length > 0) {
        const previewContainer = document.getElementById("image-previews-container");
        if (!previewContainer) return;

        // Validate and limit to 5 images total
        const newFiles = Array.from(input.files);
        const validFiles = [];

        for (const file of newFiles) {
            // Validate file type
            if (!file.type.startsWith('image/')) {
                showToast(`⚠️ Skipped ${file.name}: Not an image file`);
                continue;
            }

            // Validate file size (max 5MB)
            if (file.size > 5 * 1024 * 1024) {
                showToast(`⚠️ Skipped ${file.name}: File too large (max 5MB)`);
                continue;
            }

            validFiles.push(file);
        }

        // Check total limit
        const totalFiles = uploadedFiles.length + validFiles.length;
        if (totalFiles > 5) {
            showToast(`⚠️ Maximum 5 images allowed. You already have ${uploadedFiles.length} images.`);
            // Take only enough to reach 5
            const slotsRemaining = 5 - uploadedFiles.length;
            if (slotsRemaining > 0) {
                uploadedFiles.push(...validFiles.slice(0, slotsRemaining));
                showToast(`Added ${slotsRemaining} image(s)`);
            }
        } else {
            uploadedFiles.push(...validFiles);
            showToast(`Added ${validFiles.length} image(s)`);
        }

        // Render previews
        renderImagePreviews();

        // Trigger AI Analysis on the first image if we have new images
        if (validFiles.length > 0) {
            analyzeImageForCategory(validFiles[0]);
        }

        updateLivePreview();
    }
};

async function analyzeImageForCategory(file) {
    showToast("AI Scanning item for category detection...");
    let formData = new FormData();
    formData.append("image", file);

    try {
        const res = await fetch(`${SELLER_API_ORIGIN}/api/ai/image-ai`, {
            method: 'POST',
            cache: 'no-store',
            credentials: 'include',
            headers: sellerAuthHeaders(),
            body: formData
        });
        const data = await res.json();

        if (data.category) {
            const catSelect = document.getElementById("prod-category");
            catSelect.value = data.category;

            const aiTag = document.getElementById("category-ai-label");
            if (aiTag) {
                aiTag.style.display = "inline-block";
                aiTag.innerText = `✨ AI Detected: ${data.category}`;
            }
            showToast("✅ AI Category Detected!");
            updateLivePreview();
        }
    } catch (err) {
        console.error("AI Image Analysis Failed:", err);
    }
}

window.handleMediaPreviewEnhanced = (input, type) => {
    if (type === 'video') {
        showToast("Video preview attached.");
    }
    updateLivePreview();
};

/**
 * Live Product Score Calculation
 */
function calculateQualityScore() {
    let score = 0;
    const name = document.getElementById("prod-name").value;
    const price = document.getElementById("prod-price").value;
    const desc = document.getElementById("prod-desc").value;
    const imgCount = uploadedFiles.length;
    const vid = document.getElementById("prod-video").files.length;

    if (name.length > 20) score += 20;
    else if (name.length > 5) score += 10;

    if (price && parseFloat(price) > 0) score += 15;

    if (desc.length > 100) score += 30;
    else if (desc.length > 20) score += 15;

    if (imgCount > 0) score += 25;
    if (imgCount > 2) score += 10; // Extra points for multiple images
    if (vid > 0) score += 10;

    const fillVal = document.getElementById("score-fill");
    const scoreVal = document.getElementById("score-val");
    const tip = document.getElementById("score-tip");

    if (fillVal && scoreVal) {
        fillVal.style.width = `${Math.min(score, 100)}%`;
        scoreVal.innerText = `${Math.min(score, 100)}%`;

        if (score < 40) tip.innerText = "⚠️ Low Quality: Add more details!";
        else if (score < 80) tip.innerText = "⚡ Good: Add more images/video to reach 100%!";
        else tip.innerText = "🚀 Elite Quality: Maximizing Exposure!";
    }

    return score;
}

/**
 * Real-time Storefront Preview
 */
window.updateLivePreview = () => {
    const container = document.getElementById("live-preview-container");
    if (!container) return;

    const name = document.getElementById("prod-name").value || "Product Name";
    const price = document.getElementById("prod-price").value || "0.00";
    const category = document.getElementById("prod-category").value;

    // Handle image preview (show the first one)
    let imgSrc = "https://via.placeholder.com/300x200?text=Upload+Images";
    if (uploadedFiles.length > 0) {
        imgSrc = URL.createObjectURL(uploadedFiles[0]);
    }

    container.innerHTML = `
        <div class="product-card-seller" style="pointer-events: none;">
            <div style="position: relative; height: 160px; background: rgba(0,0,0,0.03); border-radius: 12px; display: flex; align-items: center; justify-content: center; overflow: hidden;">
                <img src="${imgSrc}" style="width: 100%; height: 100%; object-fit: cover;">
                <div style="position: absolute; top: 8px; right: 8px;">
                    <span class="fc-badge badge-pending" style="font-size: 0.6rem; padding: 0.2rem 0.6rem;">PREVIEW</span>
                </div>
            </div>
            <div style="padding: 1rem 0;">
                <div style="margin-bottom: 0.5rem;"><span class="fairness-badge badge-boosted-item">🚀 Boosted for visibility</span></div>
                <h4 style="font-size: 1.1rem; font-weight: 700; margin-bottom: 0.2rem;">${name}</h4>
                <div style="font-weight: 800; color: var(--fc-primary); font-size: 1.2rem;">₹${price}</div>
                <div style="font-size: 0.8rem; color: var(--fc-text-muted); margin-top: 0.4rem;">Category: ${category}</div>
                
                <div class="pcs-stats">
                    <div class="stat-item"><i class="fas fa-eye"></i> 0</div>
                    <div class="stat-item"><i class="fas fa-mouse-pointer"></i> 0</div>
                    <div class="stat-item"><i class="fas fa-chart-line"></i> 0%</div>
                </div>
            </div>
        </div>
    `;

    calculateQualityScore();
}

// ─────────────────────────────────────────────────────────────────────────────
//  STANDARD DASHBOARD LOGIC
// ─────────────────────────────────────────────────────────────────────────────

function sellerEscapeHtml(value) {
    return String(value || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function sellerFormatPrice(value) {
    return `Rs. ${Number(value || 0).toLocaleString("en-IN")}`;
}

function sellerExposureLabel(product) {
    const impressions = Number(product.impressions || 0);
    const bucket = product.exposure_bucket || (
        impressions === 0 ? "new" :
        impressions < 25 ? "low_exposure" :
        impressions < 100 ? "growing" :
        "established"
    );
    const labels = {
        new: "New discovery",
        low_exposure: "Low-view boost",
        growing: "Balanced growth",
        established: "Quality ranked"
    };
    return labels[bucket] || "Fair ranked";
}

window.filterProducts = () => {
    const search = (document.getElementById("search-input")?.value || "").toLowerCase();
    const cat = document.getElementById("cat-filter")?.value || "All";

    let filtered = globalProducts.filter(p => {
        return (p.name || "").toLowerCase().includes(search);
    });
    if (cat !== "All") filtered = filtered.filter(p => p.category === cat);

    renderProducts(filtered);
};

function renderProducts(products) {
    const grid = document.getElementById("products-grid");
    if (!grid) return;

    grid.innerHTML = "";

    if (products.length === 0) {
        grid.innerHTML = `<div class="empty-state" style="grid-column: 1/-1; text-align: center; padding: 4rem;">
            <div class="es-icon" style="font-size: 3rem; margin-bottom:1rem;">🛒</div>
            <h3>No products listed yet</h3>
        </div>`;
        return;
    }

    products.forEach(product => {
        const impressions = product.impressions || 0;
        const clicks = product.clicks || 0;
        const ctr = impressions > 0 ? ((clicks / impressions) * 100).toFixed(1) : 0;
        const fairScore = Math.round(Number(product.final_score || 0) * 100);
        const fairLabel = sellerExposureLabel(product);

        let statusClass = "badge-pending";
        if (product.status === "approved") statusClass = "badge-verified";
        if (product.status === "rejected") statusClass = "badge-new-item";

        const image_url = (product.image_urls && product.image_urls.length > 0) ? product.image_urls[0] : (product.image_url || "");

        let statusBadge = `<span class="fc-badge ${statusClass}" style="font-size: 0.6rem; padding: 0.2rem 0.6rem;">${(product.status || 'PENDING').toUpperCase()}</span>`;
        if (product.fraud_flag) statusBadge += ` <span class="fc-badge" style="background:#fee2e2; color:#ef4444; font-size: 0.6rem; margin-left:5px;">FRAUD</span>`;

        grid.innerHTML += `
        <div class="product-card-seller">
            <div style="position: relative; height: 160px; background: rgba(0,0,0,0.03); border-radius: 12px; display: flex; align-items: center; justify-content: center; overflow: hidden;">
                ${image_url ? `<img src="${sellerEscapeHtml(image_url)}" style="width: 100%; height: 100%; object-fit: cover;">` : `<i class="fas fa-box" style="font-size: 3rem; color: var(--fc-border);"></i>`}
                <div style="position: absolute; top: 8px; right: 8px;">${statusBadge}</div>
            </div>
            <div style="padding: 1rem 0;">
                <h4 style="font-size: 1.1rem; font-weight: 700; margin-bottom: 0.2rem;">${sellerEscapeHtml(product.name)}</h4>
                <div style="font-weight: 800; color: var(--fc-primary); font-size: 1.2rem;">${sellerFormatPrice(product.price)}</div>
                <div style="font-size: 0.8rem; color: var(--fc-text-muted); margin-top: 0.4rem;">Category: ${sellerEscapeHtml(product.category)}</div>
                <div style="margin-top: 0.7rem;">
                    <span class="fairness-badge badge-boosted-item">${fairLabel} | Fair score ${Number.isFinite(fairScore) ? fairScore : 0}</span>
                </div>
                <div class="pcs-stats">
                    <div class="stat-item"><i class="fas fa-eye"></i> ${impressions}</div>
                    <div class="stat-item"><i class="fas fa-mouse-pointer"></i> ${clicks}</div>
                    <div class="stat-item"><i class="fas fa-chart-line"></i> ${ctr}%</div>
                </div>
            </div>
        </div>`;
    });
}

window.filterOrders = (status) => {
    document.querySelectorAll(".order-tab").forEach(t => t.classList.remove("active"));
    if (document.getElementById(`tab-${status}`)) document.getElementById(`tab-${status}`).classList.add("active");

    let filtered = globalOrders;
    if (status !== "All") filtered = globalOrders.filter(o => o.status === status);
    renderOrders(filtered);
};

function renderOrders(orders) {
    const container = document.getElementById("orders-list");
    if (!container) return;

    container.innerHTML = "";
    if (orders.length === 0) {
        container.innerHTML = `<div class="empty-state" style="text-align: center; padding: 3rem;"><h3>No orders found</h3></div>`;
        return;
    }

    orders.forEach(order => {
        let statusBadge = order.status === 'Pending' ? `<span class="fc-badge badge-pending">${order.status}</span>` : `<span class="fc-badge badge-verified">${order.status}</span>`;
        container.innerHTML += `
        <div class="order-row">
            <div>
                <div style="font-weight: 700;">${order.product_name}</div>
                <div style="font-size: 0.8rem; color: var(--fc-text-muted);">Customer: ${order.customer}</div>
            </div>
            <div style="text-align: right; display: flex; align-items: center; gap: 2rem;">
                <div style="font-weight: 800; color: var(--fc-primary);">₹${order.price}</div>
                ${statusBadge}
                <select onchange="updateOrderStatus('${order._id}', this.value)" style="padding: 0.4rem; border-radius: 6px; border: 1px solid var(--fc-border);">
                    <option value="Pending" ${order.status === 'Pending' ? 'selected' : ''}>Pending</option>
                    <option value="Shipped" ${order.status === 'Shipped' ? 'selected' : ''}>Shipped</option>
                    <option value="Delivered" ${order.status === 'Delivered' ? 'selected' : ''}>Delivered</option>
                </select>
            </div>
        </div>`;
    });
}

window.updateOrderStatus = async (orderId, newStatus) => {
    try {
        const res = await fetch(`${SELLER_API_ORIGIN}/api/order/update-status`, {
            method: 'POST',
            cache: 'no-store',
            credentials: 'include',
            headers: sellerAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ id: orderId, status: newStatus })
        });
        if (!res.ok) throw new Error(`Status update failed (${res.status})`);
        showToast(`Order status updated!`);
        refreshDashboardData();
    } catch (err) {
        showToast("Update failed");
    }
};

const CLOUDINARY_URL = "https://api.cloudinary.com/v1_1/demo/upload";
const UPLOAD_PRESET = "ml_default";

async function uploadImagesToServer(files) {
    if (!files || files.length === 0) return [];

    const formData = new FormData();
    files.forEach(file => formData.append("images", file));

    const res = await fetch(`${SELLER_API_ORIGIN}/api/product/upload-images`, {
        method: "POST",
        cache: "no-store",
        credentials: "include",
        headers: sellerAuthHeaders(),
        body: formData
    });
    const data = await res.json();

    if (!res.ok) {
        throw new Error(data.message || "Image upload failed");
    }

    return data.image_urls || [];
}

async function uploadFileToCloudinary(file, resourceType = "image") {
    if (!file) return null;

    // Use Cloudinary demo account for development
    const formData = new FormData();
    formData.append("file", file);
    formData.append("upload_preset", UPLOAD_PRESET);

    try {
        const res = await fetch(CLOUDINARY_URL.replace("image", resourceType), {
            method: "POST",
            body: formData
        });
        const data = await res.json();
        return data.secure_url || "https://res.cloudinary.com/demo/image/upload/sample.jpg";
    } catch (err) {
        console.warn("Cloudinary upload failed, using demo image:", err);
        return "https://res.cloudinary.com/demo/image/upload/sample.jpg";
    }
}

window.addProduct = async (event) => {
    event.preventDefault();

    if (calculateQualityScore() < 60) {
        showToast("Quality score too low. Optimize with AI and add more images.");
        return;
    }

    if (uploadedFiles.length === 0) {
        showToast("Please upload at least one product image before listing.");
        return;
    }

    const currentUser = getStoredSeller();
    if (!currentUser?.email) {
        showToast("Please log in as a seller again.");
        return;
    }
    const btnText = document.getElementById("btn-text");
    const btnLoader = document.getElementById("btn-loader");
    const addBtn = document.getElementById("add-btn");

    const vidFile = document.getElementById("prod-video").files[0];

    try {
        btnText.style.display = "none";
        btnLoader.style.display = "inline";
        addBtn.disabled = true;

        showToast("Uploading and listing your product...");

        // Upload all images to the FairCart backend so they remain visible after listing.
        const imageUrls = await uploadImagesToServer(uploadedFiles);
        const videoUrl = await uploadFileToCloudinary(vidFile, "video");

        const seoKeywords = document.getElementById("seo-keywords").value;

        const payload = {
            name: document.getElementById("prod-name").value,
            price: parseFloat(document.getElementById("prod-price").value),
            category: document.getElementById("prod-category").value,
            description: document.getElementById("prod-desc").value,
            image_urls: imageUrls.filter(u => u),
            image_url: imageUrls[0] || "", // legacy compatibility
            video_url: videoUrl || "",
            seller_id: currentUser.email,
            seo_keywords: seoKeywords,
            icon: "Box",
            quality_score: calculateQualityScore(),
            fraud_flag: window.lastModeration ? window.lastModeration.is_fraud : false,
            tags: seoKeywords.split(",").filter(v => v)
        };

        const res = await fetch(`${SELLER_API_ORIGIN}/api/product/add-product`, {
            method: 'POST',
            cache: 'no-store',
            credentials: 'include',
            headers: sellerAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            showToast("Product successfully listed.");
            document.getElementById("add-product-form").reset();
            uploadedFiles = [];
            if (document.getElementById("image-previews-container")) document.getElementById("image-previews-container").innerHTML = "";
            await refreshDashboardData();
            window.switchView('products');
        } else {
            const errorData = await res.json().catch(() => ({}));
            showToast(errorData.message || "Submission failed.");
        }
    } catch (err) {
        showToast(err.message || "Product listing failed.");
    } finally {
        btnText.style.display = "inline";
        btnLoader.style.display = "none";
        addBtn.disabled = false;
    }
};

function generateNotifications() {
    const list = document.getElementById("notifications-list");
    const navNotif = document.getElementById("nav-item-notifications");
    if (!list) return;

    let notifs = [];
    const pendingProducts = globalProducts.filter(p => p.status === 'pending');
    const newOrders = globalOrders.filter(o => o.status === 'Pending');

    if (newOrders.length > 0) {
        notifs.push({ title: "New Orders", text: `You have ${newOrders.length} new orders to process!`, icon: "💰" });
        if (navNotif) navNotif.innerHTML = `🔔 Notifications <span style="background:#ef4444; color:white; font-size:0.6rem; padding:1px 5px; border-radius:50%; margin-left:5px;">${newOrders.length}</span>`;
    } else if (navNotif) {
        navNotif.innerHTML = `🔔 Notifications`;
    }

    if (pendingProducts.length > 0) {
        notifs.push({ title: "Product Moderation", text: `${pendingProducts.length} items are pending manual review.`, icon: "⏳" });
    }

    if (notifs.length === 0) {
        list.innerHTML = `<div class="empty-state" style="padding:3rem;"><h3>All caught up!</h3><p>Check back later for new updates.</p></div>`;
        return;
    }

    list.innerHTML = notifs.map(n => `
        <div class="order-row" style="margin-bottom:1rem; cursor:default; transform:none;">
            <div style="font-size: 1.5rem;">${n.icon}</div>
            <div style="flex:1; margin-left:1.5rem;">
                <div style="font-weight: 700;">${n.title}</div>
                <div style="font-size: 0.85rem; color: var(--fc-text-muted);">${n.text}</div>
            </div>
        </div>
    `).join("");
}

function showToast(msg) {
    const toast = document.getElementById("fc-toast");
    if (!toast) return;
    toast.innerText = msg;
    toast.classList.add("toast-active");
    setTimeout(() => toast.classList.remove("toast-active"), 4000);
}
