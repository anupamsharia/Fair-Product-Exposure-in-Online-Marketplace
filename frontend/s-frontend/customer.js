// customer.js - FairCart customer saved items and recent discovery helpers

(function () {
    const SAVED_KEY = "faircart_saved_products";
    const RECENT_KEY = "faircart_recent_products";
    const MAX_RECENT = 8;
    const MAX_SAVED = 60;

    function readList(key) {
        try {
            const value = JSON.parse(localStorage.getItem(key) || "[]");
            return Array.isArray(value) ? value : [];
        } catch {
            return [];
        }
    }

    function writeList(key, value) {
        localStorage.setItem(key, JSON.stringify(value));
    }

    function productId(product) {
        return String(product?._id || product?.id || product?.product_id || product?.name || "");
    }

    function normalizeProduct(product) {
        const imageUrls = Array.isArray(product?.image_urls) ? product.image_urls : [];
        return {
            _id: productId(product),
            name: product?.name || product?.product_name || "Product",
            price: Number(product?.price) || 0,
            category: product?.category || "",
            seller_id: product?.seller_id || "",
            seller_name: product?.seller_name || "",
            image_url: product?.image_url || product?.image || imageUrls[0] || "",
            image_urls: imageUrls,
            icon: product?.icon || "",
            impressions: Number(product?.impressions) || 0,
            clicks: Number(product?.clicks) || 0,
            saved_at: Date.now()
        };
    }

    function encodeProduct(product) {
        return encodeURIComponent(JSON.stringify(normalizeProduct(product)));
    }

    function decodeProduct(encoded) {
        try {
            return normalizeProduct(JSON.parse(decodeURIComponent(encoded)));
        } catch {
            return null;
        }
    }

    function escapeHtml(value) {
        return String(value || "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function formatPrice(value) {
        return `Rs. ${Number(value || 0).toLocaleString("en-IN")}`;
    }

    function getSaved() {
        return readList(SAVED_KEY);
    }

    function getRecent() {
        return readList(RECENT_KEY);
    }

    function isSaved(productOrId) {
        const id = typeof productOrId === "string" ? productOrId : productId(productOrId);
        return Boolean(id) && getSaved().some(item => productId(item) === id);
    }

    function saveProduct(product) {
        const normalized = normalizeProduct(product);
        if (!normalized._id) return false;

        const next = [
            normalized,
            ...getSaved().filter(item => productId(item) !== normalized._id)
        ].slice(0, MAX_SAVED);
        writeList(SAVED_KEY, next);
        updateCustomerBadges();
        return true;
    }

    function removeSaved(productOrId) {
        const id = typeof productOrId === "string" ? productOrId : productId(productOrId);
        if (!id) return false;
        writeList(SAVED_KEY, getSaved().filter(item => productId(item) !== id));
        updateCustomerBadges();
        return true;
    }

    function toggleSaved(product) {
        const normalized = normalizeProduct(product);
        const saved = isSaved(normalized._id);
        if (saved) {
            removeSaved(normalized._id);
            notify("Removed from saved items.");
            renderCustomerCollections();
            if (typeof window.renderCustomerHub === "function") window.renderCustomerHub();
            return false;
        }

        saveProduct(normalized);
        notify("Saved for later.");
        renderCustomerCollections();
        if (typeof window.renderCustomerHub === "function") window.renderCustomerHub();
        return true;
    }

    function toggleSavedFromEncoded(encoded, event) {
        if (event) event.stopPropagation();
        const product = decodeProduct(encoded);
        if (!product) return false;
        const saved = toggleSaved(product);
        const button = event?.currentTarget;
        if (button) {
            button.classList.toggle("is-saved", saved);
            button.textContent = saved ? "Saved" : "Save";
        }
        return saved;
    }

    function trackRecentlyViewed(product) {
        const normalized = normalizeProduct(product);
        if (!normalized._id) return;
        const next = [
            { ...normalized, viewed_at: Date.now() },
            ...getRecent().filter(item => productId(item) !== normalized._id)
        ].slice(0, MAX_RECENT);
        writeList(RECENT_KEY, next);
        updateCustomerBadges();
    }

    function notify(message) {
        if (typeof showToast === "function") {
            showToast(message);
        }
    }

    function updateCustomerBadges() {
        const savedCount = getSaved().length;
        const savedEls = [
            document.getElementById("saved-count"),
            document.getElementById("saved-count-mobile")
        ];
        savedEls.forEach(el => {
            if (el) el.textContent = savedCount;
        });
    }

    function productMiniCard(product) {
        const normalized = normalizeProduct(product);
        const imageHtml = normalized.image_url
            ? `<img src="${escapeHtml(normalized.image_url)}" alt="${escapeHtml(normalized.name)}" loading="lazy">`
            : `<span>${escapeHtml(normalized.icon || "Box")}</span>`;

        return `
            <article class="fc-mini-product" onclick="window.location.href='product.html?id=${encodeURIComponent(normalized._id)}'">
                <div class="fc-mini-image">${imageHtml}</div>
                <div class="fc-mini-body">
                    <strong title="${escapeHtml(normalized.name)}">${escapeHtml(normalized.name)}</strong>
                    <span>${formatPrice(normalized.price)}</span>
                </div>
            </article>
        `;
    }

    function renderRail(container, products, emptyText) {
        if (!container) return;
        const items = (products || []).filter(item => productId(item));
        container.innerHTML = items.length
            ? items.map(productMiniCard).join("")
            : `<div class="fc-empty-inline">${escapeHtml(emptyText || "Nothing here yet.")}</div>`;
    }

    function renderCustomerCollections() {
        renderRail(
            document.getElementById("saved-products-row"),
            getSaved(),
            "Saved products will appear here."
        );
        renderRail(
            document.getElementById("recently-viewed-row"),
            getRecent(),
            "Products you view will appear here."
        );
    }

    window.FairCartCustomer = {
        decodeProduct,
        encodeProduct,
        escapeHtml,
        formatPrice,
        getSaved,
        getRecent,
        isSaved,
        normalizeProduct,
        productId,
        renderCustomerCollections,
        renderRail,
        saveProduct,
        removeSaved,
        toggleSaved,
        toggleSavedFromEncoded,
        trackRecentlyViewed,
        updateCustomerBadges
    };

    document.addEventListener("DOMContentLoaded", () => {
        setTimeout(() => {
            updateCustomerBadges();
            renderCustomerCollections();
        }, 0);
    });
})();
