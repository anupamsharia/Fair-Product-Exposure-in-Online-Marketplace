/**
 * ============================================================
 *   FairCart — Central API Connector
 *   Backend: Flask on the same host, port 5000
 * ============================================================
 *
 *  Usage (import in any page):
 *    <script src="api.js"></script>
 *
 *  Every method returns the parsed JSON body on success,
 *  or throws an Error with the server's message on failure.
 * ============================================================
 */

function fairCartApiOrigin() {
  if (window.location.port === "5000") return "";
  const protocol = window.location.protocol === "https:" ? "https:" : "http:";
  const hostname = window.location.hostname || "localhost";
  return `${protocol}//${hostname}:5000`;
}

function fairCartAuthToken() {
  try {
    const user = JSON.parse(localStorage.getItem("currentUser") || localStorage.getItem("faircart_user") || "null");
    return localStorage.getItem("faircart_token") || user?.token || "";
  } catch {
    return localStorage.getItem("faircart_token") || "";
  }
}

const BASE_URL = `${fairCartApiOrigin()}/api`;

// ─── Internal helper ──────────────────────────────────────────────────────────

async function _request(method, path, body = null) {
  const opts = {
    method,
    credentials: "include",
    cache: "no-store",
    headers: { "Content-Type": "application/json" },
  };
  const token = fairCartAuthToken();
  if (token) opts.headers.Authorization = `Bearer ${token}`;
  if (body) opts.body = JSON.stringify(body);

  const res = await fetch(`${BASE_URL}${path}`, opts);
  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.message || `Request failed (${res.status})`);
  }
  return data;
}

const get  = (path)        => _request("GET",  path);
const post = (path, body)  => _request("POST", path, body);


// ─────────────────────────────────────────────────────────────────────────────
//  AUTH  —  /api/auth/*
// ─────────────────────────────────────────────────────────────────────────────

const Auth = {

  /**
   * Register a new user.
   * @param {{ name, email, password, role, shop_name?, aadhaar_number? }} data
   * @returns {{ message }}
   *
   * role = "customer" | "seller"
   * Sellers start as unverified and require Admin approval.
   */
  register(data) {
    return post("/auth/register", data);
  },

  /**
   * Log in an existing user.
   * @param {{ email, password }} data
   * @returns {{ message, user: { name, email, role, shop_name, verified } }}
   */
  login(data) {
    return post("/auth/login", data);
  },

  /**
   * Fetch profile by email (used to refresh session data).
   * @param {string} email
   * @returns {{ user: { name, email, role, shop_name, verified } }}
   */
  getMe(email) {
    return get("/auth/me");
  },
};


// ─────────────────────────────────────────────────────────────────────────────
//  PRODUCTS  —  /api/product/*
// ─────────────────────────────────────────────────────────────────────────────

const Product = {

  /**
   * Add a new product (Seller action).
   * @param {{ name, price, category?, description?, seller_id, icon?, discount?, stock?, created_at? }} data
   * @returns {{ message, product }}
   *
   * Products start with approved = false until an Admin approves them.
   */
  add(data) {
    return post("/product/add-product", data);
  },

  /**
   * Get all APPROVED products (Storefront).
   * Products are sorted by fair_score (relevance + fairness + diversity).
   * @returns {{ products: Product[] }}
   */
  getApproved() {
    return get("/product/products");
  },

  /**
   * Get ALL products for a seller's dashboard.
   * @param {string} [seller_id]  — omit to get every product (admin use)
   * @returns {{ products: Product[] }}
   */
  getAllBySeller(seller_id = null) {
    const qs = seller_id ? `?seller_id=${encodeURIComponent(seller_id)}` : "";
    return get(`/product/all-products${qs}`);
  },

  /**
   * Get a single product by MongoDB _id.
   * @param {string} id
   * @returns {{ product: Product }}
   */
  getSingle(id) {
    return get(`/product/single?id=${encodeURIComponent(id)}`);
  },

  /**
   * Increment impressions or clicks to power the fair exposure algorithm.
   * @param {string} id     — product _id
   * @param {'impressions'|'clicks'} field
   * @returns {{ message }}
   */
  incrementStat(id, field) {
    return post("/product/increment", { id, field });
  },
};


// ─────────────────────────────────────────────────────────────────────────────
//  ORDERS  —  /api/order/*
// ─────────────────────────────────────────────────────────────────────────────

const Order = {

  /**
   * Create a new order (Customer checkout action).
   * @param {{ product_name, price, customer?, customer_email?, seller_id?, date? }} data
   * @returns {{ message, order }}
   *
   * Order status defaults to "Pending".
   */
  create(data) {
    return post("/order/create-order", data);
  },

  /**
   * Get orders. Pass seller_id to scope to a single seller.
   * @param {string} [seller_id]
   * @returns {{ orders: Order[] }}
   */
  getAll(seller_id = null) {
    const qs = seller_id ? `?seller_id=${encodeURIComponent(seller_id)}` : "";
    return get(`/order/orders${qs}`);
  },

  /**
   * Update order status (Seller action).
   * @param {string} id       — order _id
   * @param {string} status   — e.g. "Processing", "Shipped", "Delivered"
   * @returns {{ message }}
   */
  updateStatus(id, status) {
    return post("/order/update-status", { id, status });
  },
};


// ─────────────────────────────────────────────────────────────────────────────
//  ADMIN  —  /api/admin/*
// ─────────────────────────────────────────────────────────────────────────────

const Admin = {

  /**
   * Get sellers waiting for verification.
   * @returns {{ sellers: User[] }}
   */
  getPendingSellers() {
    return get("/admin/pending-sellers");
  },

  /**
   * Approve a seller by email.
   * @param {string} email
   * @returns {{ message }}
   */
  approveSeller(email) {
    return post("/admin/approve-seller", { email });
  },

  /**
   * Get products waiting for admin approval.
   * @returns {{ products: Product[] }}
   */
  getPendingProducts() {
    return get("/admin/pending-products");
  },

  /**
   * Approve a product by _id.
   * @param {string} id
   * @returns {{ message }}
   */
  approveProduct(id) {
    return post("/admin/approve-product", { id });
  },

  /**
   * Get all users (passwords excluded).
   * @returns {{ users: User[] }}
   */
  getAllUsers() {
    return get("/admin/all-users");
  },

  /**
   * Get every product in the system (admin view, approved + pending).
   * @returns {{ products: Product[] }}
   */
  getAllProducts() {
    return get("/admin/all-products");
  },

  /**
   * Dashboard summary stats.
   * @returns {{ total_users, total_sellers, pending_sellers, total_products, pending_products, total_orders }}
   */
  getStats() {
    return get("/admin/stats");
  },
};


// ─────────────────────────────────────────────────────────────────────────────
//  Session helpers  (localStorage wrappers)
// ─────────────────────────────────────────────────────────────────────────────

const Session = {
  /** Save user object after login */
  save(user) {
    const token = user?.token || localStorage.getItem("faircart_token") || "";
    const storedUser = { ...user };
    if (token) {
      storedUser.token = token;
      localStorage.setItem("faircart_token", token);
    }
    localStorage.setItem("faircart_user", JSON.stringify(storedUser));
    localStorage.setItem("currentUser", JSON.stringify(storedUser));
  },

  /** Retrieve the logged-in user, or null */
  get() {
    try {
      return JSON.parse(localStorage.getItem("faircart_user"));
    } catch {
      return null;
    }
  },

  /** Clear session (logout) */
  clear() {
    localStorage.removeItem("faircart_user");
    localStorage.removeItem("currentUser");
    localStorage.removeItem("faircart_token");
  },

  /** Guard — redirects to login page if not logged in */
  require(redirectTo = "login.html") {
    if (!Session.get()) {
      window.location.href = redirectTo;
    }
    return Session.get();
  },

  /** Guard — redirects if role doesn't match */
  requireRole(role, redirectTo = "index.html") {
    const user = Session.require();
    if (user && user.role !== role) {
      window.location.href = redirectTo;
    }
    return user;
  },
};


// Export as globals (works without a bundler)
window.FairCartAPI = { Auth, Product, Order, Admin, Session };
