// auth.js - FairCart auth, role guards, and navigation

function getFairCartApiOrigin() {
    if (window.location.port === "5000") return "";
    const protocol = window.location.protocol === "https:" ? "https:" : "http:";
    const hostname = window.location.hostname || "localhost";
    return `${protocol}//${hostname}:5000`;
}

function getFairCartBackendUrl(path = "") {
    return `${getFairCartApiOrigin() || window.location.origin}${path}`;
}

const AUTH_API_ORIGIN = getFairCartApiOrigin();

function getCurrentUser() {
    try {
        const raw = localStorage.getItem('currentUser') || localStorage.getItem('faircart_user') || 'null';
        const user = JSON.parse(raw);
        const token = localStorage.getItem('faircart_token') || user?.token || "";
        if (user && token && !user.token) {
            user.token = token;
            localStorage.setItem('currentUser', JSON.stringify(user));
            localStorage.setItem('faircart_user', JSON.stringify(user));
        }
        if (user && !localStorage.getItem('currentUser')) {
            localStorage.setItem('currentUser', JSON.stringify(user));
        }
        return user;
    } catch (e) {
        return null;
    }
}

function getAuthToken() {
    try {
        const user = JSON.parse(localStorage.getItem('currentUser') || localStorage.getItem('faircart_user') || 'null');
        return localStorage.getItem('faircart_token') || user?.token || "";
    } catch (e) {
        return localStorage.getItem('faircart_token') || "";
    }
}

function buildAuthHeaders(extraHeaders = {}) {
    const headers = { ...extraHeaders };
    const token = getAuthToken();
    if (token) headers.Authorization = `Bearer ${token}`;
    return headers;
}

function saveCurrentUser(user, token = null) {
    const authToken = token || user?.token || "";
    const storedUser = { ...user };
    if (authToken) {
        storedUser.token = authToken;
        localStorage.setItem('faircart_token', authToken);
    }
    localStorage.setItem('currentUser', JSON.stringify(storedUser));
    localStorage.setItem('faircart_user', JSON.stringify(storedUser));
}

function redirectBasedOnRole(role) {
    if (role === 'admin') window.location.href = getFairCartBackendUrl('/admin');
    else if (role === 'seller') window.location.href = 'seller-dashboard.html';
    else window.location.href = 'index.html';
}

function requireCustomer() {
    const user = getCurrentUser();
    if (user?.role === 'seller') window.location.href = 'seller-dashboard.html';
    if (user?.role === 'admin') window.location.href = getFairCartBackendUrl('/admin');
}

function requireCustomerLogin() {
    const user = getCurrentUser();
    if (!user) {
        window.location.href = 'login.html';
        return null;
    }
    requireCustomer();
    return user;
}

function requireSeller() {
    const user = getCurrentUser();
    if (!user) window.location.href = 'login.html';
    else if (user.role === 'customer') window.location.href = 'index.html';
    else if (user.role === 'admin') window.location.href = getFairCartBackendUrl('/admin');
    else if (user.role !== 'seller') window.location.href = 'login.html';
}

function requireAdmin() {
    const user = getCurrentUser();
    if (!user || user.role !== 'admin') {
        window.location.href = getFairCartBackendUrl('/admin-login.html');
    }
}

function checkUser() {
    const navLinks = document.getElementById('nav-links');
    const mobileNavLinks = document.getElementById('mobile-nav-links');
    const shouldPopulateNav = navLinks && navLinks.hasAttribute('data-auth-nav');
    const shouldPopulateMobileNav = mobileNavLinks && mobileNavLinks.hasAttribute('data-auth-nav');

    if (!shouldPopulateNav && !shouldPopulateMobileNav) return;

    const user = getCurrentUser();

    if (user) {
        const displayRole = (user.role || 'customer').charAt(0).toUpperCase() + (user.role || 'customer').slice(1);
        const initials = (user.name || displayRole).charAt(0).toUpperCase();
        const firstName = user.name ? user.name.split(' ')[0] : displayRole;

        let roleActionLink = '';
        let shoppingLinks = '';
        let menuItems = '';
        let mobileRoleLinks = '';

        if (user.role === 'customer') {
            shoppingLinks = `
                <a href="index.html#saved-products" class="saved-icon">Saved (<span id="saved-count">0</span>)</a>
                <a href="cart.html" class="cart-icon">&#128722; Cart (<span id="cart-count">0</span>)</a>`;
            menuItems = `
                <a href="orders.html" class="dropdown-item" id="dd-my-orders"><span class="dd-icon">&#128230;</span> My Orders</a>
                <a href="index.html#saved-products" class="dropdown-item" id="dd-saved"><span class="dd-icon">&#9734;</span> Saved Items</a>`;
            mobileRoleLinks = `
                <a href="index.html#saved-products" class="saved-icon">&#9734; Saved (<span id="saved-count-mobile">0</span>)</a>
                <a href="cart.html" class="cart-icon">&#128722; Cart (<span id="cart-count-mobile">0</span>)</a>
                <a href="orders.html" class="dropdown-item" id="mobile-dd-my-orders">&#128230; My Orders</a>`;
        } else if (user.role === 'seller') {
            roleActionLink = `<a href="seller-dashboard.html" style="color: var(--primary-color);">Seller Dashboard</a>`;
            menuItems = `<a href="seller-dashboard.html" class="dropdown-item" id="dd-seller-dash"><span class="dd-icon">&#127970;</span> Seller Dashboard</a>`;
            mobileRoleLinks = roleActionLink;
        } else if (user.role === 'admin') {
            const adminUrl = getFairCartBackendUrl('/admin');
            roleActionLink = `<a href="${adminUrl}" style="color: var(--primary-color);">Admin Panel</a>`;
            menuItems = `<a href="${adminUrl}" class="dropdown-item" id="dd-admin-dash"><span class="dd-icon">&#9881;&#65039;</span> Admin Panel</a>`;
            mobileRoleLinks = roleActionLink;
        }

        const desktopNavHTML = `
            <a href="index.html">Marketplace</a>
            ${roleActionLink}
            ${shoppingLinks}
            <div class="profile-dropdown" id="profile-dd-wrap">
                <button class="profile-btn" id="profile-dd-btn" aria-haspopup="true" aria-expanded="false">
                    <span class="profile-avatar">${initials}</span>
                    ${firstName}
                    <span class="dd-chevron">&#9662;</span>
                </button>
                <div class="dropdown-content" id="profile-dd-menu" role="menu">
                    <div class="dd-header">
                        <div class="dd-avatar-large">${initials}</div>
                        <div>
                            <div class="dd-name">${user.name || displayRole}</div>
                            <div class="dd-email">${user.email || ''}</div>
                            <span class="dd-role-badge">${displayRole}</span>
                        </div>
                    </div>
                    <div class="dd-divider"></div>
                    ${menuItems}
                    <div class="dd-divider"></div>
                    <a href="#" class="dropdown-item dd-logout" id="dd-logout" onclick="logout(event)">
                        <span class="dd-icon">&#128682;</span> Logout
                    </a>
                </div>
            </div>
        `;

        const mobileNavHTML = `
            <a href="index.html">Marketplace</a>
            ${mobileRoleLinks}
            <a href="#" class="dropdown-item dd-logout" id="mobile-dd-logout" onclick="logout(event)">&#128682; Logout</a>
        `;

        if (shouldPopulateNav) navLinks.innerHTML = desktopNavHTML;
        if (shouldPopulateMobileNav) mobileNavLinks.innerHTML = mobileNavHTML;
    } else {
        const desktopNavHTML = `
            <a href="index.html">Marketplace</a>
            <a href="cart.html" class="cart-icon">&#128722; Cart (<span id="cart-count">0</span>)</a>
            <div class="profile-dropdown" id="profile-dd-wrap">
                <button class="profile-btn" id="profile-dd-btn" aria-haspopup="true" aria-expanded="false">
                    &#128100; Account
                    <span class="dd-chevron">&#9662;</span>
                </button>
                <div class="dropdown-content" id="profile-dd-menu" role="menu">
                    <a href="login.html" class="dropdown-item" id="dd-login"><span class="dd-icon">&#128273;</span> Login</a>
                    <a href="register.html" class="dropdown-item" id="dd-register"><span class="dd-icon">&#10024;</span> Register</a>
                </div>
            </div>
        `;

        const mobileNavHTML = `
            <a href="index.html">Marketplace</a>
            <a href="cart.html" class="cart-icon">&#128722; Cart (<span id="cart-count-mobile">0</span>)</a>
            <a href="login.html" class="dropdown-item" id="mobile-dd-login">&#128273; Login</a>
            <a href="register.html" class="dropdown-item" id="mobile-dd-register">&#10024; Register</a>
        `;

        if (shouldPopulateNav) navLinks.innerHTML = desktopNavHTML;
        if (shouldPopulateMobileNav) mobileNavLinks.innerHTML = mobileNavHTML;
    }

    initDropdown();
}

function initDropdown() {
    const btn = document.getElementById('profile-dd-btn');
    const menu = document.getElementById('profile-dd-menu');
    if (!btn || !menu) return;

    btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = menu.classList.contains('dd-open');
        closeAllDropdowns();
        if (!isOpen) {
            menu.classList.add('dd-open');
            btn.setAttribute('aria-expanded', 'true');
            btn.classList.add('dd-active');
        }
    });

    document.addEventListener('click', () => closeAllDropdowns(), { once: false });
    menu.addEventListener('click', (e) => e.stopPropagation());
}

function closeAllDropdowns() {
    document.querySelectorAll('.dropdown-content.dd-open').forEach(m => m.classList.remove('dd-open'));
    document.querySelectorAll('#profile-dd-btn').forEach(b => {
        b.setAttribute('aria-expanded', 'false');
        b.classList.remove('dd-active');
    });
}

async function login(event) {
    if (event) event.preventDefault();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;

    if (!email || !password) {
        alert("Please enter email and password");
        return;
    }

    try {
        const res = await fetch(`${AUTH_API_ORIGIN}/api/auth/login`, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();

        if (res.ok) {
            saveCurrentUser(data.user, data.token);
            if (data.user.role === 'admin') localStorage.setItem('faircart_role', 'admin');
            redirectBasedOnRole(data.user.role);
        } else {
            alert("Login Failed: " + data.message);
        }
    } catch (err) {
        alert("Backend might be down. Start the Flask server on port 5000.");
        console.error(err);
    }
}

async function register(event) {
    if (event) event.preventDefault();
    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const role = document.getElementById('role').value;

    if (!name || !email || !password || !role) {
        alert("All fields are required");
        return;
    }

    const payload = { name, email, password, role };

    if (role === 'seller') {
        const shop_name = document.getElementById('shop-name')?.value?.trim();
        const aadhaar_number = document.getElementById('aadhaar-number')?.value?.trim();
        if (!shop_name || !aadhaar_number) {
            alert("Please fill all Seller details");
            return;
        }
        payload.shop_name = shop_name;
        payload.aadhaar_number = aadhaar_number;
    }

    try {
        const res = await fetch(`${AUTH_API_ORIGIN}/api/auth/register`, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (res.ok) {
            alert("Registration successful! Please login.");
            window.location.href = 'login.html';
        } else {
            alert("Registration failed: " + data.message);
        }
    } catch (err) {
        alert("Backend might be down.");
        console.error(err);
    }
}

async function logout(event) {
    if (event) event.preventDefault();
    try {
        await fetch(`${AUTH_API_ORIGIN}/api/auth/logout`, {
            method: 'POST',
            credentials: 'include',
            headers: buildAuthHeaders()
        });
    } catch (e) {
        // Local logout still completes if the backend is unreachable.
    }
    localStorage.removeItem('currentUser');
    localStorage.removeItem('faircart_user');
    localStorage.removeItem('faircart_token');
    localStorage.removeItem('faircart_role');
    localStorage.removeItem('faircart_cart');
    localStorage.removeItem('cart');
    window.location.href = 'login.html';
}

function hideSellerButton() {
    const user = getCurrentUser();
    const heroSellerBtn = document.getElementById('hero-seller-btn');
    if (!heroSellerBtn) return;
    heroSellerBtn.style.display = user && user.role === 'customer' ? 'none' : 'inline-block';
}

document.addEventListener('DOMContentLoaded', () => {
    checkUser();
    hideSellerButton();

    const path = window.location.pathname;
    const user = getCurrentUser();
    if (user && (path.includes('login.html') || path.includes('register.html'))) {
        redirectBasedOnRole(user.role);
    }
});

window.showToast = (msg) => {
    let toast = document.getElementById("fc-toast");
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'fc-toast';
        toast.className = 'fc-toast';
        document.body.appendChild(toast);
    }
    toast.innerText = msg;
    toast.classList.add('toast-active');
    setTimeout(() => toast.classList.remove('toast-active'), 4000);
};
