// orders.js - FairCart customer order history

const ORDERS_API_ORIGIN = typeof getFairCartApiOrigin === "function"
    ? getFairCartApiOrigin()
    : (typeof fairCartApiOrigin === "function"
        ? fairCartApiOrigin()
        : (window.location.port === "5000" ? "" : `${window.location.protocol === "https:" ? "https:" : "http:"}//${window.location.hostname || "localhost"}:5000`));
const ORDERS_ADMIN_URL = typeof getFairCartBackendUrl === "function"
    ? getFairCartBackendUrl("/admin")
    : `${ORDERS_API_ORIGIN || window.location.origin}/admin`;

document.addEventListener("DOMContentLoaded", async () => {
    const user = getCurrentUser();
    if (!user) {
        window.location.href = "login.html";
        return;
    }
    if (user.role !== "customer") {
        window.location.href = user.role === "seller" ? "seller-dashboard.html" : ORDERS_ADMIN_URL;
        return;
    }

    const container = document.getElementById("orders-container");
    const badge = document.getElementById("order-count-badge");

    try {
        const email = encodeURIComponent(user.email);
        const res = await fetch(`${ORDERS_API_ORIGIN}/api/order/my-orders?email=${email}`, {
            cache: "no-store",
            credentials: "include"
        });
        const data = await res.json();

        if (!res.ok) throw new Error(data.message || "Failed to fetch orders");

        const orders = data.orders || [];
        badge.textContent = `${orders.length} Order${orders.length !== 1 ? "s" : ""}`;

        if (orders.length === 0) {
            container.innerHTML = emptyState();
            return;
        }

        orders.sort((a, b) => new Date(b.date || 0) - new Date(a.date || 0));
        container.innerHTML = orders.map(renderOrderCard).join("");
    } catch (err) {
        console.error("Orders fetch error:", err);
        badge.textContent = "Error";
        container.innerHTML = `
            <div class="error-banner">
                Could not load orders - ${escHtml(err.message)}
            </div>
            ${emptyState(true)}
        `;
    }
});

function renderOrderCard(order) {
    const statusKey = (order.status || "Pending").toLowerCase();
    const formattedDate = order.date ? formatDate(order.date) : "N/A";
    const quantity = Number(order.quantity) || 1;
    const unitPrice = quantity > 0 ? (Number(order.price) || 0) / quantity : Number(order.price) || 0;
    const price = formatPrice(order.price);
    const encodedOrder = encodeURIComponent(JSON.stringify(order));
    const productLink = order.product_id ? `product.html?id=${encodeURIComponent(order.product_id)}` : "index.html";

    return `
    <div class="order-card status-${statusKey}">
        <div class="order-icon">${categoryIcon(order.product_name || "")}</div>

        <div class="order-details">
            <div class="order-product-name">${escHtml(order.product_name || "Unknown Product")}</div>
            <div class="order-meta">
                <span>${formattedDate}</span>
                ${order._id ? `<span>#${order._id.slice(-6).toUpperCase()}</span>` : ""}
                ${order.customer ? `<span>${escHtml(order.customer)}</span>` : ""}
                <span>${quantity} item${quantity !== 1 ? "s" : ""} at ${formatPrice(unitPrice)}</span>
            </div>
            <div class="order-actions">
                ${order.product_id ? `<a class="order-action-btn" href="${productLink}">View Product</a>` : ""}
                <button class="order-action-btn" type="button" onclick="buyAgainFromOrder('${encodedOrder}')">Buy Again</button>
            </div>
        </div>

        <div class="order-right">
            <div class="order-price">${price}</div>
            <span class="status-pill ${statusKey}">${escHtml(order.status || "Pending")}</span>
        </div>

        <div class="order-tracker">
            ${renderTracker(order.status)}
        </div>
    </div>`;
}

window.buyAgainFromOrder = (encodedOrder) => {
    try {
        const order = JSON.parse(decodeURIComponent(encodedOrder));
        const quantity = Number(order.quantity) || 1;
        const unitPrice = quantity > 0 ? (Number(order.price) || 0) / quantity : Number(order.price) || 0;
        const added = addToCart(order.product_name || "Product", unitPrice, {
            seller_id: order.seller_id || "",
            product_id: order.product_id || "",
            image_url: order.image_url || ""
        });
        if (added) window.location.href = "cart.html";
    } catch (err) {
        console.error("Buy again failed:", err);
    }
};

function renderTracker(status) {
    const steps = ["Pending", "Shipped", "Delivered"];
    const statusText = (status || "Pending").toLowerCase();
    const idx = steps.findIndex(step => step.toLowerCase() === statusText);
    const cancelled = statusText === "cancelled";

    if (cancelled) {
        return `<div style="color:#f87171;font-size:0.85rem;width:100%;text-align:center;">
            This order was cancelled.
        </div>`;
    }

    return steps.map((step, i) => {
        const done = i <= idx;
        return `
        <div class="tracker-step ${done ? "done" : ""}">
            <div class="tracker-dot">${done ? "OK" : i + 1}</div>
            <div class="tracker-label">${step}</div>
        </div>`;
    }).join("");
}

function categoryIcon(name) {
    const n = name.toLowerCase();
    if (/phone|mobile|samsung|iphone/i.test(n)) return "Mobile";
    if (/laptop|computer|mac|pc/i.test(n)) return "Tech";
    if (/shirt|dress|cloth|fashion|shoes/i.test(n)) return "Wear";
    if (/book|novel|guide/i.test(n)) return "Book";
    if (/headphone|earphone|audio/i.test(n)) return "Audio";
    if (/watch|clock/i.test(n)) return "Time";
    if (/bag|purse/i.test(n)) return "Bag";
    if (/kitchen|cook|utensil/i.test(n)) return "Home";
    if (/camera/i.test(n)) return "Cam";
    if (/game|console/i.test(n)) return "Game";
    return "Box";
}

function formatDate(dateStr) {
    try {
        return new Date(dateStr).toLocaleDateString("en-IN", {
            day: "2-digit",
            month: "short",
            year: "numeric"
        });
    } catch {
        return dateStr;
    }
}

function formatPrice(value) {
    if (window.FairCartCustomer?.formatPrice) return window.FairCartCustomer.formatPrice(value);
    return `Rs. ${Number(value || 0).toLocaleString("en-IN")}`;
}

function escHtml(str) {
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function emptyState(isError = false) {
    return `
    <div class="empty-orders">
        <span class="empty-icon">${isError ? "!" : "Cart"}</span>
        <h3>${isError ? "Connection issue" : "No orders yet"}</h3>
        <p>${isError
            ? "Make sure the backend is running on port 5000."
            : "Start shopping and your order tracking will appear here."}</p>
        <a href="index.html" class="btn-primary" style="display:inline-block;padding:0.9rem 2rem;text-decoration:none;border-radius:25px;">
            Browse Products
        </a>
    </div>`;
}
