from pathlib import Path
import json
import random
import re
import sys
import time
from datetime import datetime
from urllib.request import Request, urlopen

TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from path_helper import ensure_backend_on_path

ensure_backend_on_path()

from db import activity_logs_collection, orders_collection, products_collection, users_collection
from product_scoring import apply_score_fields
from werkzeug.security import generate_password_hash

SOURCE_URL = "https://dummyjson.com/products?limit=0"
PASSWORD = "password123"
INR_RATE = 83

CATEGORY_MAP = {
    "furniture": "Home & Kitchen",
    "home-decoration": "Home & Kitchen",
    "kitchen-accessories": "Home & Kitchen",
    "laptops": "Electronics",
    "mobile-accessories": "Electronics",
    "smartphones": "Electronics",
    "tablets": "Electronics",
    "mens-shirts": "Fashion",
    "mens-shoes": "Fashion",
    "tops": "Fashion",
    "womens-dresses": "Fashion",
    "womens-shoes": "Fashion",
    "mens-watches": "Fashion",
    "sunglasses": "Fashion",
    "womens-bags": "Fashion",
    "womens-jewellery": "Fashion",
    "womens-watches": "Fashion",
}

FALLBACK_SHOPS = {
    "Home & Kitchen": "Urban Home Store",
    "Electronics": "Circuit House",
    "Fashion": "Street Loom",
}

FIRST_NAMES = [
    "Anup", "Rahul", "Priya", "Sara", "Karan", "Riya", "Amit", "Neha",
    "Arjun", "Diya", "Vikas", "Sneha", "Isha", "Kabir", "Meera", "Dev",
]
LAST_NAMES = [
    "Sharma", "Verma", "Kapoor", "Gupta", "Das", "Roy", "Sen", "Patel",
    "Nair", "Joshi", "Mehta", "Reddy", "Iyer", "Kumar", "Singh", "Bose",
]


def slugify(value):
    text = re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")
    return text or "seller"


def fetch_products():
    request = Request(SOURCE_URL, headers={"User-Agent": "FairCartSeed/1.0"})
    with urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    products = data.get("products") or []
    if not products:
        raise RuntimeError("No products returned by source catalog")
    return products


def broad_category(source_category):
    return CATEGORY_MAP.get(str(source_category or "").lower())


def seller_name_for(product):
    brand = (product.get("brand") or "").strip()
    if brand:
        return f"{brand} Store"
    return FALLBACK_SHOPS.get(broad_category(product.get("category")), "FairCart Select")


def image_list(product):
    images = []
    for value in [product.get("thumbnail"), *(product.get("images") or [])]:
        if isinstance(value, str) and value.strip() and value not in images:
            images.append(value.strip())
    return images


def price_in_inr(value):
    return max(99, int(round(float(value or 1) * INR_RATE)))


def stock_to_impressions(stock, index):
    if index % 5 == 0:
        return random.randint(0, 18)
    if index % 5 == 1:
        return random.randint(19, 90)
    return random.randint(120, 1800)


def build_sellers(source_products, password_hash):
    seller_names = sorted({seller_name_for(product) for product in source_products})
    sellers = []
    for index, name in enumerate(seller_names, 1):
        email = f"{slugify(name)}@faircart.demo"
        sellers.append({
            "name": name,
            "email": email,
            "password": password_hash,
            "role": "seller",
            "shop_name": name,
            "verified": True,
            "aadhaar_number": f"900000{index:06d}",
            "created_at": datetime.now(),
        })
    return sellers


def build_customers(password_hash, count=80):
    customers = []
    for index in range(1, count + 1):
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        customers.append({
            "name": name,
            "email": f"customer{index}@test.com",
            "password": password_hash,
            "role": "customer",
            "verified": True,
            "created_at": datetime.now(),
        })
    return customers


def build_products(source_products, sellers_by_name):
    now = int(time.time())
    products = []

    for index, source in enumerate(source_products):
        category = broad_category(source.get("category"))
        if not category:
            continue

        images = image_list(source)
        if not images:
            continue

        seller_name = seller_name_for(source)
        seller = sellers_by_name[seller_name]
        price = price_in_inr(source.get("price"))
        discount = float(source.get("discountPercentage") or 0)
        original_price = int(round(price / max(0.55, 1 - (discount / 100)))) if discount > 0 else price
        impressions = stock_to_impressions(source.get("stock"), index)
        ctr = random.uniform(0.03, 0.18)
        clicks = min(impressions, int(round(impressions * ctr)))
        title = str(source.get("title") or "Product").strip()
        description = str(source.get("description") or "").strip()
        source_category = str(source.get("category") or "").replace("-", " ").title()
        tags = [str(tag).strip() for tag in (source.get("tags") or []) if str(tag).strip()]
        tags.extend([source_category, category])

        product = {
            "name": title,
            "price": price,
            "original_price": original_price,
            "category": category,
            "source_category": source_category,
            "description": description,
            "seller_id": seller["email"],
            "seller_name": seller["shop_name"],
            "brand": source.get("brand") or seller["shop_name"].replace(" Store", ""),
            "sku": source.get("sku") or f"REAL-{index + 1:04d}",
            "image_url": images[0],
            "image_urls": images[:5],
            "thumbnail": source.get("thumbnail") or images[0],
            "approved": True,
            "status": "approved",
            "fraud_flag": False,
            "on_sale": discount >= 8,
            "discount": int(round(discount)),
            "discount_label": f"{int(round(discount))}% OFF" if discount >= 8 else "",
            "rating": round(float(source.get("rating") or random.uniform(3.6, 4.9)), 1),
            "reviews_count": len(source.get("reviews") or []) or random.randint(12, 350),
            "stock": int(source.get("stock") or random.randint(8, 120)),
            "impressions": impressions,
            "clicks": clicks,
            "tags": list(dict.fromkeys(tags))[:12],
            "seo_keywords": list(dict.fromkeys([title.lower(), source_category.lower(), category.lower(), seller["shop_name"].lower()] + [t.lower() for t in tags]))[:16],
            "hidden_seo_keywords": list(dict.fromkeys([title.lower(), source_category.lower(), category.lower(), seller["shop_name"].lower()] + [t.lower() for t in tags]))[:16],
            "created_at": now - random.randint(0, 90 * 24 * 3600),
            "updated_at": now,
            "source": "dummyjson",
            "source_id": source.get("id"),
        }
        products.append(apply_score_fields(product))

    return products


def build_orders(inserted_products, customers, count=180):
    now = int(time.time())
    statuses = ["Pending", "Shipped", "Delivered", "Delivered", "Delivered", "Cancelled"]
    orders = []
    for _ in range(min(count, max(1, len(inserted_products) * 2))):
        product = random.choice(inserted_products)
        customer = random.choice(customers)
        quantity = random.randint(1, 3)
        created_ts = now - random.randint(0, 60 * 24 * 3600)
        orders.append({
            "product_id": str(product["_id"]),
            "product_name": product["name"],
            "price": product["price"],
            "quantity": quantity,
            "customer": customer["name"],
            "customer_email": customer["email"],
            "seller_id": product["seller_id"],
            "seller_name": product["seller_name"],
            "image_url": product.get("image_url", ""),
            "status": random.choice(statuses),
            "date": datetime.fromtimestamp(created_ts).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "created_at": created_ts,
        })
    return orders


def seed_real_market():
    random.seed(20260426)
    source_products = fetch_products()
    password_hash = generate_password_hash(PASSWORD)

    sellers = build_sellers(source_products, password_hash)
    sellers_by_name = {seller["shop_name"]: seller for seller in sellers}
    customers = build_customers(password_hash)
    products = build_products(source_products, sellers_by_name)

    print("--- Seeding realistic matched marketplace data ---")
    print(f"Source products fetched: {len(source_products)}")

    products_collection.delete_many({})
    orders_collection.delete_many({})
    activity_logs_collection.delete_many({})
    users_collection.delete_many({"role": {"$ne": "admin"}})

    users_collection.insert_many(sellers + customers, ordered=False)
    inserted = products_collection.insert_many(products, ordered=False)

    inserted_products = []
    for inserted_id, product in zip(inserted.inserted_ids, products):
        stored = dict(product)
        stored["_id"] = inserted_id
        inserted_products.append(stored)

    orders = build_orders(inserted_products, customers)
    if orders:
        orders_collection.insert_many(orders, ordered=False)

    now = int(time.time())
    activity_logs_collection.insert_one({
        "type": "SEED",
        "message": "Realistic matched product catalog seeded",
        "user_email": "System",
        "user_id": "System",
        "timestamp": now,
        "date": datetime.fromtimestamp(now).strftime("%Y-%m-%d %H:%M:%S"),
    })

    categories = {}
    for product in products:
        categories[product["category"]] = categories.get(product["category"], 0) + 1

    print("\n*** SUCCESS! ***")
    print(f"   Sellers  : {len(sellers)}")
    print(f"   Customers: {len(customers)}")
    print(f"   Products : {len(products)}")
    print(f"   Orders   : {len(orders)}")
    print("   Categories:")
    for category, count in sorted(categories.items()):
        print(f"     - {category}: {count}")
    print(f"   Demo password for sellers/customers: {PASSWORD}")
    print("   Example accounts:")
    print(f"     Customer: {customers[0]['email']}")
    print(f"     Seller  : {sellers[0]['email']}")


if __name__ == "__main__":
    seed_real_market()
