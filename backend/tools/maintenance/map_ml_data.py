from pathlib import Path
import sys

TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from path_helper import ensure_backend_on_path

ensure_backend_on_path()

from db import products_collection, db
import random

def seed_ml_products():
    print("--- Seeding ML-Compatible Products ---")
    
    # 1. Clear existing products to avoid duplicates during testing
    # products_collection.delete_many({}) 

    # 2. Define products that match the behavior.pkl and reviews.pkl IDs
    ml_products = [
        {
            "name": "FairCart Ultra High-Speed HDMI Cable",
            "price": 899,
            "category": "Electronics",
            "description": "Premium 4K HDMI cable with gold-plated connectors for low latency and high reliability.",
            "image_url": "https://images.unsplash.com/photo-1591488320449-011701bb6704?auto=format&fit=crop&q=80&w=800",
            "asin": "B007JFMH8M", # Reviews score: 52.12
            "ml_id": "1002524",
            "seller_id": "seller@test.com",
            "approved": True,
            "status": "approved",
            "impressions": 150,
            "clicks": 25,
            "fair_score": 98
        },
        {
            "name": "FairCart Wireless Optical Mouse",
            "price": 1299,
            "category": "Electronics",
            "description": "Ergonomic wireless mouse with precision tracking and long battery life.",
            "ml_id": "1002542", # Recommended for 1002524
            "seller_id": "seller@test.com",
            "approved": True,
            "status": "approved",
            "impressions": 80,
            "clicks": 10
        },
        {
            "name": "FairCart Mechanical Gaming Keyboard",
            "price": 4500,
            "category": "Electronics",
            "description": "Backlit mechanical keyboard with tactile switches for the ultimate gaming experience.",
            "ml_id": "5701408", # Recommended for 1002524
            "seller_id": "seller@test.com",
            "approved": True,
            "status": "approved",
            "impressions": 200,
            "clicks": 45
        },
        {
            "name": "FairCart Noise Cancelling Headphones",
            "price": 7999,
            "category": "Electronics",
            "description": "Immersive sound quality with active noise cancellation technology.",
            "ml_id": "8801085", # Recommended for 1002524
            "seller_id": "seller@test.com",
            "approved": True,
            "status": "approved",
            "impressions": 310,
            "clicks": 60
        }
    ]

    for prod in ml_products:
        # Check if already exists to avoid spamming
        if not products_collection.find_one({"name": prod["name"]}):
            products_collection.insert_one(prod)
            print(f"Added: {prod['name']}")
    
    print("Seeding complete.")

if __name__ == "__main__":
    seed_ml_products()
