document.addEventListener('DOMContentLoaded', () => {
    // ── CONFIGURATION ──────────────────────────────────────────────
    const API_BASE = window.location.port === "5000" ? window.location.origin : "http://localhost:5000";

    function getAdminToken() {
        try {
            const currentUser = JSON.parse(localStorage.getItem("currentUser") || "null");
            return localStorage.getItem("faircart_token") || currentUser?.token || "";
        } catch {
            return localStorage.getItem("faircart_token") || "";
        }
    }

    function escapeAdminHtml(value) {
        return String(value || "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // UI Elements
    const navLinks = document.querySelectorAll('.nav-link');
    const tabContents = document.querySelectorAll('.tab-content');
    const pageTitle = document.getElementById('page-title');

    // ── AUTHENTICATED FETCH HELPER ──────────────────────────────────
    async function authFetch(endpoint, options = {}) {
        const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;

        // Ensure credentials are included for session support
        options.credentials = 'include';
        options.cache = 'no-store';
        options.headers = {
            ...(options.headers || {})
        };

        const token = getAdminToken();
        if (token) {
            options.headers.Authorization = `Bearer ${token}`;
        }

        if (options.body && typeof options.body === 'object') {
            options.headers = {
                ...options.headers,
                'Content-Type': 'application/json'
            };
            options.body = JSON.stringify(options.body);
        }

        try {
            const res = await fetch(url, options);
            if (!res.ok) {
                if (res.status === 401) {
                    console.warn("Session expired. Redirecting to login...");
                    localStorage.removeItem("faircart_token");
                    localStorage.removeItem("currentUser");
                    window.location.href = "admin-login.html";
                }
                throw new Error(`API Error: ${res.status}`);
            }
            return await res.json();
        } catch (err) {
            console.error(`Fetch failed for ${url}:`, err);
            throw err;
        }
    }

    // ── GLOBAL ACTIONS ─────────────────────────────────────────────
    window.logout = async function () {
        try {
            await fetch(`${API_BASE}/api/auth/logout`, {
                method: 'POST',
                credentials: 'include',
                cache: 'no-store'
            });
        } finally {
            localStorage.removeItem("faircart_token");
            localStorage.removeItem("currentUser");
            alert("Logging out...");
            // Redirect to storefront login as requested in the workflow
            window.location.href = "../s-frontend/login.html";
        }
    };

    window.updateGlobalData = function () {
        loadDashboard();
        loadActivity();
        loadUsers();
        loadPendingSellers();
        loadPendingProducts();
        loadOrders();
    };

    // ── DATA LOADING ───────────────────────────────────────────────

    async function loadDashboard() {
        try {
            // Using /api/admin/stats which contains both summary and graph data
            const data = await authFetch("/api/admin/stats");

            // Update Summary Cards
            document.getElementById("users").innerText = data.total_users || 0;
            document.getElementById("orders").innerText = data.total_orders || 0;
            document.getElementById("pending").innerText = data.pending_products || 0;
            document.getElementById("fraud").innerText = data.fraud_flagged || 0;

            // Render Graph
            if (data.graph_data) {
                renderGrowthChart(data.graph_data);
            }

            console.log("Dashboard stats loaded");
        } catch (err) {
            console.error("Dashboard failed to load:", err);
        }
    }

    async function loadActivity() {
        try {
            const data = await authFetch("/api/admin/activity");
            const activityList = data.activities || [];
            const container = document.getElementById("activity");

            if (activityList.length === 0) {
                container.innerHTML = '<p class="text-secondary" style="padding: 1rem;">No recent activity</p>';
                return;
            }

            container.innerHTML = activityList.map(a => `
                <li class="activity-item">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                        <strong>${a.type || 'System Event'}</strong>
                        <small style="color:var(--text-secondary); font-size:0.7rem;">${new Date(a.timestamp * 1000).toLocaleTimeString()}</small>
                    </div>
                    <p style="font-size:0.85rem; margin-top:0.3rem; color:var(--text-secondary);">${a.message || ''}</p>
                </li>
            `).join("");
        } catch (err) {
            console.error("Activity failed to load:", err);
            document.getElementById("activity").innerHTML = '<p class="text-danger" style="padding: 1rem;">Failed to load activity</p>';
        }
    }

    // ── TAB LOADERS ────────────────────────────────────────────────

    async function loadUsers() {
        try {
            const data = await authFetch('/api/admin/all-users');
            const tbody = document.getElementById('user-table-body');

            tbody.innerHTML = (data.users || []).map(u => `
                <tr>
                    <td>${u.name || 'N/A'}</td>
                    <td>${u.email}</td>
                    <td><span class="badge">${(u.role || 'user').toUpperCase()}</span></td>
                    <td><span class="status status-${u.status || 'active'}">${(u.status || 'Active').toUpperCase()}</span></td>
                    <td style="display:flex; gap:0.5rem;">
                        <button class="btn btn-approve" onclick="updateUserStatus('${u.email}', '${u.status === 'blocked' ? 'active' : 'blocked'}')">
                            ${u.status === 'blocked' ? 'Unblock' : 'Block'}
                        </button>
                        <button class="btn" style="background:rgba(239, 68, 68, 0.1); color:#ef4444;" onclick="deleteUser('${u.email}')">Delete</button>
                    </td>
                </tr>
            `).join('');
        } catch (err) {
            console.error("Users failed to load:", err);
        }
    }

    async function loadPendingSellers() {
        try {
            const data = await authFetch('/api/admin/pending-sellers');
            const tbody = document.getElementById('seller-approval-body');

            if (!data.sellers || data.sellers.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;">No pending sellers</td></tr>';
                return;
            }

            tbody.innerHTML = data.sellers.map(s => `
                <tr>
                    <td>${s.email}</td>
                    <td>${s.shop_name || 'Personal Account'}</td>
                    <td><span class="text-secondary"><i class="fas fa-file-alt"></i> ID Proof Attached</span></td>
                    <td>
                        <button class="btn btn-approve" onclick="approveSeller('${s.email}')">Approve</button>
                    </td>
                </tr>
            `).join('');
        } catch (err) {
            console.error("Sellers failed to load:", err);
        }
    }

    async function loadPendingProducts() {
        try {
            const data = await authFetch('/api/admin/pending-products');
            const tbody = document.getElementById('product-approval-body');

            if (!data.products || data.products.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;">No pending products</td></tr>';
                return;
            }

            tbody.innerHTML = data.products.map(p => `
                <tr>
                    <td><img src="${p.image_url || (p.image_urls && p.image_urls[0]) || 'https://via.placeholder.com/50'}" width="40" style="border-radius:4px;"></td>
                    <td><strong>${p.name}</strong></td>
                    <td>${p.seller_id}</td>
                    <td><span class="badge" style="color:${p.fraud_flag ? '#ef4444' : '#22c55e'}">${p.fraud_flag ? 'RISK' : 'SAFE'}</span></td>
                    <td>${p.seo_score || 0}%</td>
                    <td><span class="status status-pending">Pending</span></td>
                    <td style="display:flex; gap:0.5rem;">
                        <button class="btn btn-approve" onclick="approveProduct('${p._id}')">Approve</button>
                        <button class="btn btn-reject" onclick="rejectProduct('${p._id}')">Reject</button>
                    </td>
                </tr>
            `).join('');
        } catch (err) {
            console.error("Products failed to load:", err);
        }
    }

    async function loadOrders() {
        try {
            const data = await authFetch('/api/order/orders');
            const tbody = document.getElementById('order-table-body');

            if (!data.orders || data.orders.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">No orders found</td></tr>';
                return;
            }

            tbody.innerHTML = data.orders.map(o => `
                <tr>
                    <td>#${o._id.slice(-6).toUpperCase()}</td>
                    <td>${o.product_name}</td>
                    <td>${o.customer}</td>
                    <td>₹${o.price}</td>
                    <td><span class="status status-${(o.status || 'pending').toLowerCase()}">${o.status}</span></td>
                    <td>
                        <select onchange="updateOrder(this, '${o._id}')" class="btn" style="background:var(--bg-card); color:var(--text-primary); border:1px solid var(--border);">
                            <option value="">Update</option>
                            <option value="Shipped">Shipped</option>
                            <option value="Delivered">Delivered</option>
                            <option value="Cancelled">Cancelled</option>
                        </select>
                    </td>
                </tr>
            `).join('');
        } catch (err) {
            console.error("Orders failed to load:", err);
        }
    }

    async function loadFairnessReport() {
        try {
            const data = await authFetch('/api/admin/fairness-report');
            const alertContainer = document.getElementById('monopoly-alert-container');

            if (data.monopoly_alerts && data.monopoly_alerts.length > 0) {
                alertContainer.innerHTML = `
                    <div class="alert alert-danger" style="margin-bottom: 2rem; border-left: 4px solid var(--danger);">
                        <i class="fas fa-exclamation-triangle"></i>
                        <span><strong>Monopoly Alert!</strong> Sellers [${escapeAdminHtml(data.monopoly_alerts.join(', '))}] have excessive visibility share.</span>
                    </div>
                `;
            } else {
                alertContainer.innerHTML = `
                    <div class="alert" style="margin-bottom: 2rem; border-left: 4px solid var(--success);">
                        <i class="fas fa-check-circle"></i>
                        <span><strong>Fairness Index:</strong> ${data.fairness_index || 0} | No seller is dominating current visibility.</span>
                    </div>
                `;
            }

            const tbody = document.getElementById('fairness-table-body');
            tbody.innerHTML = (data.products || []).map(p => `
                <tr>
                    <td><strong>${escapeAdminHtml(p.name)}</strong><br><small style="color:var(--text-secondary);">${escapeAdminHtml(p.seller_id || 'Unknown seller')}</small></td>
                    <td>${p.impressions || 0}</td>
                    <td>${p.clicks || 0}</td>
                    <td>${p.ctr || 0}</td>
                    <td>${p.vis_share || 0}%</td>
                    <td>
                        <span style="font-weight:600; color:var(--accent);">${p.score || 0}</span>
                        <small style="display:block; color:var(--text-secondary);">Fair ${p.fair_score || 0}</small>
                    </td>
                    <td><span class="badge">${escapeAdminHtml((p.exposure_bucket || 'normal').replace('_', ' ').toUpperCase())}</span></td>
                </tr>
            `).join('');
        } catch (err) {
            console.error("Fairness report failed:", err);
        }
    }

    async function loadAIReport() {
        try {
            const data = await authFetch('/api/admin/ai-performance');
            const tbody = document.getElementById('ai-log-body');

            // Update summary stats
            // Note: Update these if you add specific IDs to the AI cards in HTML

            if (data.logs && data.logs.length > 0) {
                tbody.innerHTML = data.logs.map(log => `
                    <tr>
                        <td>${log.name}</td>
                        <td>"${log.orig}"</td>
                        <td>"${log.opt}"</td>
                        <td><span style="color:var(--success)">${log.gain}</span></td>
                    </tr>
                `).join('');
            }
        } catch (err) {
            console.error("AI report failed:", err);
        }
    }

    // ── INTERACTIVE ACTIONS (Window Scoped) ─────────────────────────

    window.updateUserStatus = async (email, status) => {
        if (!confirm(`Are you sure you want to ${status} this user?`)) return;
        await authFetch('/api/admin/update-user-status', {
            method: 'POST',
            body: { email, status }
        });
        loadUsers();
    };

    window.deleteUser = async (email) => {
        if (!confirm("DANGER: Permanently delete this user?")) return;
        await authFetch('/api/admin/delete-user', {
            method: 'POST',
            body: { email }
        });
        loadUsers();
    };

    window.approveSeller = async (email) => {
        await authFetch('/api/admin/approve-seller', {
            method: 'POST',
            body: { email }
        });
        window.updateGlobalData();
    };

    window.approveProduct = async (id) => {
        await authFetch('/api/admin/approve-product', {
            method: 'POST',
            body: { id }
        });
        window.updateGlobalData();
    };

    window.rejectProduct = async (id) => {
        await authFetch('/api/admin/reject-product', {
            method: 'POST',
            body: { id }
        });
        window.updateGlobalData();
    };

    window.updateOrder = async (el, id) => {
        const status = el.value;
        if (!status) return;
        await authFetch('/api/order/update-status', {
            method: 'POST',
            body: { id, status }
        });
        loadOrders();
    };

    // ── CHART RENDERING ─────────────────────────────────────────────
    let growthChart = null;
    function renderGrowthChart(graphData) {
        const canvas = document.getElementById('growthChart');
        if (!canvas) return;

        const panel = canvas.parentElement;
        const emptyMsg = panel.querySelector('.chart-empty-state');
        if (emptyMsg) emptyMsg.remove();
        canvas.style.display = 'block';

        const hasData = graphData.users && graphData.users.some(v => v > 0) ||
            graphData.orders && graphData.orders.some(v => v > 0);

        if (!hasData) {
            canvas.style.display = 'none';
            const msg = document.createElement('div');
            msg.className = 'chart-empty-state';
            msg.style.cssText = 'height: 250px; display: flex; align-items: center; justify-content: center; color: var(--text-secondary); font-style: italic;';
            msg.innerText = 'No chart data available for this period';
            panel.appendChild(msg);
            return;
        }

        const ctx = canvas.getContext('2d');
        if (growthChart) growthChart.destroy();

        // Create Gradients
        const userGrad = ctx.createLinearGradient(0, 0, 0, 250);
        userGrad.addColorStop(0, 'rgba(56, 189, 248, 0.2)');
        userGrad.addColorStop(1, 'rgba(56, 189, 248, 0)');

        const orderGrad = ctx.createLinearGradient(0, 0, 0, 250);
        orderGrad.addColorStop(0, 'rgba(34, 197, 94, 0.2)');
        orderGrad.addColorStop(1, 'rgba(34, 197, 94, 0)');

        growthChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: graphData.labels,
                datasets: [
                    {
                        label: 'Users',
                        data: graphData.users,
                        borderColor: '#38bdf8',
                        backgroundColor: userGrad,
                        fill: true,
                        tension: 0.35,
                        borderWidth: 2,
                        pointRadius: 0,
                        pointHoverRadius: 6,
                        pointHoverBackgroundColor: '#38bdf8',
                        pointHoverBorderColor: '#fff',
                        pointHoverBorderWidth: 2
                    },
                    {
                        label: 'Orders',
                        data: graphData.orders,
                        borderColor: '#22c55e',
                        backgroundColor: orderGrad,
                        fill: true,
                        tension: 0.35,
                        borderWidth: 2,
                        pointRadius: 0,
                        pointHoverRadius: 6,
                        pointHoverBackgroundColor: '#22c55e',
                        pointHoverBorderColor: '#fff',
                        pointHoverBorderWidth: 2
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                layout: {
                    padding: { top: 10, bottom: 0, left: 10, right: 10 }
                },
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        align: 'end',
                        labels: {
                            color: '#94a3b8',
                            usePointStyle: true,
                            pointStyle: 'circle',
                            padding: 20,
                            font: { family: "'Inter', sans-serif", size: 12, weight: '500' }
                        }
                    },
                    tooltip: {
                        enabled: true,
                        backgroundColor: 'rgba(2, 6, 23, 0.95)',
                        titleColor: '#f8fafc',
                        bodyColor: '#94a3b8',
                        borderColor: 'rgba(255,255,255,0.1)',
                        borderWidth: 1,
                        padding: 12,
                        cornerRadius: 8,
                        displayColors: true,
                        usePointStyle: true,
                        callbacks: {
                            label: function (context) {
                                return ` ${context.dataset.label}: ${context.parsed.y}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255,255,255,0.03)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#64748b',
                            font: { size: 11 },
                            maxTicksLimit: 6,
                            padding: 10
                        }
                    },
                    x: {
                        grid: { display: false },
                        ticks: {
                            color: '#64748b',
                            font: { size: 11 },
                            maxTicksLimit: 7,
                            padding: 10
                        }
                    }
                }
            }
        });
    }

    // ── REAL‑TIME FEATURES ──────────────────────────────────────────

    let notificationInterval = null;
    let dashboardInterval = null;
    let lastNotificationCount = 0;

    async function loadNotifications() {
        try {
            const data = await authFetch('/api/admin/notifications');
            const totalPending = data.total_pending || 0;
            const notifDot = document.getElementById('notif-dot');
            const notifBtn = document.getElementById('notif-btn');

            // Update notification badge
            if (totalPending > 0) {
                notifDot.textContent = totalPending > 9 ? '9+' : totalPending;
                notifDot.style.display = 'flex';
                notifDot.style.backgroundColor = '#ef4444';
                notifDot.style.color = 'white';
                notifDot.style.borderRadius = '50%';
                notifDot.style.width = '20px';
                notifDot.style.height = '20px';
                notifDot.style.alignItems = 'center';
                notifDot.style.justifyContent = 'center';
                notifDot.style.fontSize = '0.7rem';
                notifDot.style.position = 'absolute';
                notifDot.style.top = '-5px';
                notifDot.style.right = '-5px';

                // Add pulse animation for new notifications
                if (totalPending > lastNotificationCount) {
                    notifDot.classList.add('pulse');
                    setTimeout(() => notifDot.classList.remove('pulse'), 1000);
                }
            } else {
                notifDot.style.display = 'none';
            }

            lastNotificationCount = totalPending;

            // Update notification dropdown if it exists
            updateNotificationDropdown(data);

            return data;
        } catch (err) {
            console.error("Notifications failed to load:", err);
            return null;
        }
    }

    function updateNotificationDropdown(data) {
        // Create or update notification dropdown
        let dropdown = document.getElementById('notification-dropdown');
        if (!dropdown) {
            dropdown = document.createElement('div');
            dropdown.id = 'notification-dropdown';
            dropdown.className = 'notification-dropdown';
            dropdown.style.cssText = `
                position: absolute;
                top: 50px;
                right: 0;
                background: var(--bg-card);
                border: 1px solid var(--border);
                border-radius: 8px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                width: 320px;
                max-height: 400px;
                overflow-y: auto;
                z-index: 1000;
                display: none;
                padding: 1rem;
            `;
            document.querySelector('.dropdown-wrapper').appendChild(dropdown);

            // Add click handler to notification button
            document.getElementById('notif-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
            });

            // Close dropdown when clicking outside
            document.addEventListener('click', (e) => {
                if (!dropdown.contains(e.target) && e.target.id !== 'notif-btn') {
                    dropdown.style.display = 'none';
                }
            });
        }

        if (!data) return;

        const items = [];

        // Add pending sellers
        if (data.pending_sellers > 0) {
            items.push(`
                <div class="notification-item" style="padding: 0.75rem; border-bottom: 1px solid var(--border);">
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                        <div style="background: rgba(59, 130, 246, 0.1); color: #3b82f6; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                            <i class="fas fa-store"></i>
                        </div>
                        <div>
                            <strong>${data.pending_sellers} pending seller${data.pending_sellers > 1 ? 's' : ''}</strong>
                            <p style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.25rem;">Need approval</p>
                        </div>
                    </div>
                </div>
            `);
        }

        // Add pending products
        if (data.pending_products > 0) {
            items.push(`
                <div class="notification-item" style="padding: 0.75rem; border-bottom: 1px solid var(--border);">
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                        <div style="background: rgba(34, 197, 94, 0.1); color: #22c55e; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                            <i class="fas fa-box"></i>
                        </div>
                        <div>
                            <strong>${data.pending_products} pending product${data.pending_products > 1 ? 's' : ''}</strong>
                            <p style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.25rem;">Awaiting review</p>
                        </div>
                    </div>
                </div>
            `);
        }

        // Add fraud alerts
        if (data.fraud_flagged > 0) {
            items.push(`
                <div class="notification-item" style="padding: 0.75rem; border-bottom: 1px solid var(--border);">
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                        <div style="background: rgba(239, 68, 68, 0.1); color: #ef4444; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                            <i class="fas fa-exclamation-triangle"></i>
                        </div>
                        <div>
                            <strong>${data.fraud_flagged} fraud alert${data.fraud_flagged > 1 ? 's' : ''}</strong>
                            <p style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.25rem;">Requires attention</p>
                        </div>
                    </div>
                </div>
            `);
        }

        // Add recent activities
        if (data.recent_activities && data.recent_activities.length > 0) {
            items.push(`
                <div style="padding: 0.75rem; border-bottom: 1px solid var(--border);">
                    <strong style="font-size: 0.9rem; color: var(--text-secondary);">Recent Activity</strong>
                </div>
            `);

            data.recent_activities.forEach(act => {
                const iconMap = {
                    'NEW_SELLER': 'fas fa-store',
                    'NEW_PRODUCT': 'fas fa-box',
                    'FRAUD_FLAG': 'fas fa-exclamation-triangle',
                    'ORDER_PLACED': 'fas fa-shopping-cart'
                };
                const icon = iconMap[act.type] || 'fas fa-bell';

                items.push(`
                    <div class="notification-item" style="padding: 0.75rem; border-bottom: 1px solid var(--border);">
                        <div style="display: flex; align-items: center; gap: 0.75rem;">
                            <div style="background: rgba(148, 163, 184, 0.1); color: #94a3b8; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                                <i class="${icon}"></i>
                            </div>
                            <div style="flex: 1;">
                                <p style="font-size: 0.85rem; margin: 0;">${act.message || 'System activity'}</p>
                                <small style="color: var(--text-secondary); font-size: 0.75rem;">
                                    ${new Date(act.timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </small>
                            </div>
                        </div>
                    </div>
                `);
            });
        }

        if (items.length === 0) {
            items.push(`
                <div style="padding: 2rem; text-align: center; color: var(--text-secondary);">
                    <i class="fas fa-bell-slash" style="font-size: 2rem; margin-bottom: 1rem;"></i>
                    <p>No notifications</p>
                </div>
            `);
        }

        dropdown.innerHTML = items.join('');
    }

    function startRealTimeUpdates() {
        // Load notifications immediately and every 20 seconds
        loadNotifications();
        if (notificationInterval) clearInterval(notificationInterval);
        notificationInterval = setInterval(loadNotifications, 20000);

        // Start dashboard auto-refresh (only when on dashboard tab)
        if (dashboardInterval) clearInterval(dashboardInterval);
        dashboardInterval = setInterval(() => {
            const activeTab = document.querySelector('.tab-content.active');
            if (activeTab && activeTab.id === 'tab-dashboard') {
                loadDashboard();
            }
        }, 30000); // Refresh dashboard every 30 seconds

        console.log("Real-time updates started");
    }

    function stopRealTimeUpdates() {
        if (notificationInterval) clearInterval(notificationInterval);
        if (dashboardInterval) clearInterval(dashboardInterval);
        notificationInterval = null;
        dashboardInterval = null;
    }

    // ── INITIALIZATION ──────────────────────────────────────────────
    function init() {
        // Initial data pull
        loadDashboard();
        loadActivity();

        // Tab switching logic
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const tabId = link.getAttribute('data-tab');

                // Update UI state
                navLinks.forEach(l => l.classList.remove('active'));
                link.classList.add('active');

                tabContents.forEach(tab => {
                    tab.classList.remove('active');
                    if (tab.id === `tab-${tabId}`) tab.classList.add('active');
                });

                pageTitle.innerText = link.getAttribute('data-title') || 'Dashboard Overview';

                // Specific tab loaders
                if (tabId === 'users') loadUsers();
                if (tabId === 'seller-approval') loadPendingSellers();
                if (tabId === 'product-approval') loadPendingProducts();
                if (tabId === 'orders') loadOrders();
                if (tabId === 'fairness') loadFairnessReport();
                if (tabId === 'ai-monitor') loadAIReport();

                // Restart real-time updates for appropriate tabs
                startRealTimeUpdates();
            });
        });

        // Polling loop for activity
        setInterval(loadActivity, 30000);

        // Start real-time updates
        startRealTimeUpdates();

        console.log("Admin Dashboard logic initialized.");
    }

    init();
});
