from pathlib import Path
import sys

TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from path_helper import ensure_backend_on_path

ensure_backend_on_path()

from db import products_collection

ml_ids_to_check = ['1002542', '5701408', '8801085', '11400662', '1003310']

print("Checking which ML IDs exist in database...")
products = list(products_collection.find(
    {'ml_id': {'$in': ml_ids_to_check}}, 
    {'_id': 1, 'name': 1, 'ml_id': 1, 'status': 1}
))

print(f"Found {len(products)} products matching ML IDs:")
for p in products:
    print(f"  - {p['name']}: ml_id={p.get('ml_id')}, status={p.get('status')}")

# Also check what products were returned by the API
print("\nChecking what products were in the API response...")
# The product IDs from the API response
api_product_ids = [
    '69dc1ad27e9f29a692e3792b',  # Mechanical RGB Gaming Keyboard
    '69dc1ad27e9f29a692e3792c',  # Ultra-Wide 4K Productivity Monitor  
    '69dc1ad27e9f29a692e3792d',  # USB-C Multi-Port Docking Hub
    '69dc1ad27e9f29a692e3792e',  # True Wireless Earbuds Elite
    '69dc1ad27e9f29a692e3792f',  # Smart 4K Android TV Box
]

from bson.objectid import ObjectId
api_products = list(products_collection.find(
    {'_id': {'$in': [ObjectId(pid) for pid in api_product_ids]}},
    {'_id': 1, 'name': 1, 'ml_id': 1, 'category': 1}
))

print(f"\nAPI response products:")
for p in api_products:
    print(f"  - {p['name']}: ml_id={p.get('ml_id', 'N/A')}, category={p.get('category')}")
