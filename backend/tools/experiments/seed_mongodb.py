"""
FairCart – Seed MongoDB from JSON files
"""
import json, os, sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from path_helper import backend_path, ensure_backend_on_path

ensure_backend_on_path()

from db import db

SEED_DIR = backend_path("seed_data")

def load(name):
    with (SEED_DIR / name).open(encoding="utf-8") as f:
        return json.load(f)

sellers   = load("sellers.json")
products  = load("products.json")
customers = load("customers.json")
orders    = load("orders.json")

def seed_collection(collection, name, data, id_field="_id"):
    existing_ids = set(str(d[id_field]) for d in collection.find({}, {id_field: 1}))
    to_insert = [d for d in data if str(d[id_field]) not in existing_ids]
    if to_insert:
        # Rename _id to avoid conflicts with MongoDB ObjectId
        for doc in to_insert:
            if "_id" in doc:
                doc["_id"] = doc["_id"]  # keep string _id
        collection.insert_many(to_insert)
        print(f"[SEEDED] {name}: inserted {len(to_insert)} new records")
    else:
        print(f"[SKIP]   {name}: all {len(data)} records already exist")

print("\n--- Seeding MongoDB ---")
seed_collection(db["users"],    "sellers",   sellers)
seed_collection(db["users"],    "customers", customers)
seed_collection(db["products"], "products",  products)
seed_collection(db["orders"],   "orders",    orders)

print("\n=== Seeding complete! ===")
print(f"  Users (sellers + customers) : {db['users'].count_documents({})}")
print(f"  Products                    : {db['products'].count_documents({})}")
print(f"  Orders                      : {db['orders'].count_documents({})}")
