# FairCart Frontend

## Storefront (`s-frontend/`)

- `index.html` - customer marketplace home and product listing. The public `Become a Seller` CTA opens `seller.html`.
- `register.html` - customer/seller registration form. Use `register.html?role=seller` to open seller registration directly.
- `login.html` - shared login for customer, seller, and admin users.
- `seller.html` - seller marketing page.
- `seller-dashboard.html` - seller dashboard for products, orders, and AI listing tools.
- `seller-register.html` - legacy seller onboarding URL. It redirects to `seller.html` by default; use `seller-register.html?assistant=1` only for the optional AI-guided assistant.
- `cart.html` - customer cart and checkout.
- `orders.html` - customer order history.
- `product.html` - product detail page.

## Shared Storefront Scripts

- `auth.js` - login, register, logout, role guards, and account navigation.
- `api.js` - central API wrapper.
- `app.js` - marketplace product listing.
- `cart.js` - cart and checkout behavior.
- `orders.js` - customer orders page behavior.
- `customer.js` - customer saved items, recently viewed products, and shared customer helpers.
- `seller.js` - seller dashboard behavior.

## Customer Experience Features

- Logged-in customers see a customer desk on `index.html`.
- Customers can save products and return to them from the `Saved` navigation link.
- Product detail pages track recently viewed products.
- Customer home highlights fair picks from lower-exposure products.
- Orders support `View Product` and `Buy Again` actions.

## Admin (`admin-frontend/`)

- `admin-login.html` - admin login page.
- `admin.html` - admin dashboard shell.
- `admin.js` - admin dashboard data loading/actions.
- `admin.css` - admin dashboard styles.

## Main Navigation Rule

The public homepage `Become a Seller` CTA should open:

```text
s-frontend/seller.html
```

The seller landing page `Start Selling` CTA should open:

```text
s-frontend/register.html?role=seller
```

The legacy AI guided seller assistant remains available only at:

```text
s-frontend/seller-register.html?assistant=1
```
