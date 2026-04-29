/**
 * Cart functionality for FairCart customers.
 */

document.addEventListener("DOMContentLoaded", () => {
    if (typeof requireCustomer === "function") requireCustomer();
    updateCartCount();

    if (document.getElementById("cart-items-container")) {
        renderCart();
    }
});

const CART_API_ORIGIN = typeof getFairCartApiOrigin === "function"
    ? getFairCartApiOrigin()
    : (window.location.port === "5000" ? "" : `${window.location.protocol === "https:" ? "https:" : "http:"}//${window.location.hostname || "localhost"}:5000`);
const CART_ADMIN_URL = typeof getFairCartBackendUrl === "function"
    ? getFairCartBackendUrl("/admin")
    : `${CART_API_ORIGIN || window.location.origin}/admin`;

function readCart() {
    try {
        const cart = JSON.parse(localStorage.getItem("cart") || "[]");
        return Array.isArray(cart) ? cart : [];
    } catch {
        return [];
    }
}

function writeCart(cart) {
    localStorage.setItem("cart", JSON.stringify(cart));
    updateCartCount();
    window.FairCartCustomer?.updateCustomerBadges?.();
    if (typeof window.renderCustomerHub === "function") window.renderCustomerHub();
}

function escapeCartHtml(value) {
    if (window.FairCartCustomer?.escapeHtml) return window.FairCartCustomer.escapeHtml(value);
    return String(value || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function cartPrice(value) {
    if (window.FairCartCustomer?.formatPrice) return window.FairCartCustomer.formatPrice(value);
    return `Rs. ${Number(value || 0).toLocaleString("en-IN")}`;
}

window.addToCart = (name, price, meta = {}) => {
    const user = JSON.parse(localStorage.getItem("currentUser") || "null");

    if (!user) {
        alert("Please login to add items to your cart.");
        window.location.href = "login.html";
        return false;
    }

    if (user.role !== "customer") {
        alert("Only customer accounts can shop.");
        if (user.role === "seller") window.location.href = "seller-dashboard.html";
        else if (user.role === "admin") window.location.href = CART_ADMIN_URL;
        return false;
    }

    const cart = readCart();
    const itemMeta = typeof meta === "string" ? { seller_id: meta } : (meta || {});
    const sellerId = itemMeta.seller_id || "";
    const productId = itemMeta.product_id || "";
    const numericPrice = Number(price) || 0;

    const existingItem = cart.find(item => {
        if (productId && item.product_id) return item.product_id === productId;
        return item.name === name && (item.seller_id || "") === sellerId;
    });

    if (existingItem) {
        existingItem.quantity += 1;
        existingItem.seller_id = existingItem.seller_id || sellerId;
        existingItem.product_id = existingItem.product_id || productId;
        existingItem.image_url = existingItem.image_url || itemMeta.image_url || "";
    } else {
        cart.push({
            name,
            price: numericPrice,
            quantity: 1,
            seller_id: sellerId,
            product_id: productId,
            image_url: itemMeta.image_url || ""
        });
    }

    writeCart(cart);
    if (typeof showToast === "function") showToast(`${name} added to cart.`);
    return true;
};

window.updateCartCount = () => {
    const totalItems = readCart().reduce((sum, item) => sum + (Number(item.quantity) || 0), 0);

    const countEl = document.getElementById("cart-count");
    if (countEl) countEl.innerText = totalItems;

    const mobileCountEl = document.getElementById("cart-count-mobile");
    if (mobileCountEl) mobileCountEl.innerText = totalItems;
};

window.renderCart = () => {
    const cart = readCart();
    const container = document.getElementById("cart-items-container");
    const totalEl = document.getElementById("cart-total");
    if (!container || !totalEl) return;

    container.innerHTML = "";

    if (cart.length === 0) {
        container.innerHTML = `
            <div class="empty-state" style="text-align:center; padding:3rem;">
                <h3>Your cart is empty</h3>
                <p style="color:var(--fc-text-muted); margin:0.5rem 0 1.5rem;">Fair picks are waiting in the marketplace.</p>
                <a href="index.html" class="btn-primary" style="display:inline-block; text-decoration:none;">Browse Products</a>
            </div>`;
        totalEl.innerText = "Rs. 0";
        return;
    }

    let subtotal = 0;

    cart.forEach((item, index) => {
        const quantity = Number(item.quantity) || 1;
        const itemPrice = Number(item.price) || 0;
        const itemTotal = itemPrice * quantity;
        subtotal += itemTotal;

        const card = document.createElement("div");
        card.className = "cart-item-card";
        card.style.cssText = "display:grid; grid-template-columns:96px 1fr auto auto; gap:1rem; align-items:center; background:var(--fc-surface); border:1px solid var(--fc-border); padding:1.25rem; border-radius:16px; margin-bottom:1rem; backdrop-filter:blur(16px); color:var(--fc-text); box-shadow:var(--fc-shadow);";

        const productUrl = item.product_id ? `product.html?id=${encodeURIComponent(item.product_id)}` : "index.html";
        const imageHtml = item.image_url
            ? `<img src="${escapeCartHtml(item.image_url)}" alt="${escapeCartHtml(item.name)}" style="width:96px; height:96px; object-fit:cover; border-radius:12px;">`
            : `<div style="width:96px; height:96px; border-radius:12px; display:flex; align-items:center; justify-content:center; background:rgba(108,99,255,0.06); color:var(--fc-text-muted); font-weight:700;">Item</div>`;

        card.innerHTML = `
            <a href="${productUrl}" style="display:block; text-decoration:none;">${imageHtml}</a>
            <div class="item-info">
                <h3 style="font-size:1.05rem; font-weight:800; margin-bottom:0.35rem;">${escapeCartHtml(item.name)}</h3>
                <p style="color:var(--fc-primary); font-weight:800;">${cartPrice(itemPrice)}</p>
                ${item.seller_id ? `<p style="color:var(--fc-text-muted); font-size:0.8rem; margin-top:0.2rem;">Seller: ${escapeCartHtml(item.seller_id)}</p>` : ""}
                <a href="${productUrl}" style="display:inline-block; margin-top:0.55rem; color:var(--fc-primary); font-size:0.85rem; font-weight:700; text-decoration:none;">View Product</a>
            </div>

            <div class="quantity-controls" style="display:flex; align-items:center; gap:0.8rem; background:rgba(108,99,255,0.05); padding:0.5rem 0.75rem; border-radius:999px; justify-content:center;">
                <button onclick="changeQuantity(${index}, -1)" style="background:white; border:1px solid var(--fc-border); color:var(--fc-text); cursor:pointer; width:30px; height:30px; border-radius:50%; font-size:1rem;">-</button>
                <span style="font-weight:800; min-width:1.5rem; text-align:center;">${quantity}</span>
                <button onclick="changeQuantity(${index}, 1)" style="background:white; border:1px solid var(--fc-border); color:var(--fc-text); cursor:pointer; width:30px; height:30px; border-radius:50%; font-size:1rem;">+</button>
            </div>

            <div style="text-align:right;">
                <div class="item-total" style="font-size:1.1rem; font-weight:800; margin-bottom:0.6rem;">
                    ${cartPrice(itemTotal)}
                </div>
                <button class="btn-delete" style="background:rgba(220,38,38,0.06); color:#dc2626; border:1px solid rgba(220,38,38,0.18); padding:0.5rem 0.9rem; border-radius:999px; cursor:pointer; font-weight:700;" onclick="removeItem(${index})">Remove</button>
            </div>
        `;

        container.appendChild(card);
    });

    totalEl.innerText = cartPrice(subtotal);
};

window.changeQuantity = (index, delta) => {
    const cart = readCart();
    if (cart[index]) {
        cart[index].quantity = (Number(cart[index].quantity) || 1) + delta;
        if (cart[index].quantity <= 0) cart.splice(index, 1);
        writeCart(cart);
        renderCart();
    }
};

window.removeItem = (index) => {
    const cart = readCart();
    cart.splice(index, 1);
    writeCart(cart);
    renderCart();
};

window.checkoutCart = async () => {
    const cart = readCart();
    const currentUser = JSON.parse(localStorage.getItem("currentUser") || "null");

    if (!currentUser) {
        if (typeof showToast === "function") showToast("Please login to place your order.");
        setTimeout(() => {
            window.location.href = "login.html?redirect=cart.html";
        }, 1000);
        return;
    }

    if (currentUser.role !== "customer") {
        if (typeof showToast === "function") showToast("Only customer accounts can place orders.");
        if (currentUser.role === "seller") window.location.href = "seller-dashboard.html";
        else if (currentUser.role === "admin") window.location.href = CART_ADMIN_URL;
        return;
    }

    if (cart.length === 0) {
        if (typeof showToast === "function") showToast("Your cart is empty.");
        return;
    }

    const customerName = currentUser.name;
    const customerEmail = currentUser.email;

    try {
        for (const item of cart) {
            const res = await fetch(`${CART_API_ORIGIN}/api/order/create-order`, {
                method: "POST",
                cache: "no-store",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    product_name: item.name,
                    price: (Number(item.price) || 0) * (Number(item.quantity) || 1),
                    quantity: Number(item.quantity) || 1,
                    product_id: item.product_id || "",
                    image_url: item.image_url || "",
                    customer: customerName,
                    customer_email: customerEmail,
                    seller_id: item.seller_id || "",
                    date: new Date().toISOString()
                })
            });
            if (!res.ok) throw new Error(`Order create failed (${res.status})`);
        }

        writeCart([]);
        if (typeof showToast === "function") showToast(`Order placed for ${cart.length} item(s).`);
        renderCart();
        setTimeout(() => {
            window.location.href = "orders.html";
        }, 800);
    } catch (err) {
        console.error(err);
        alert("Checkout failed. Is the backend server running?");
    }
};
