import pickle
from pathlib import Path
import sys

TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from path_helper import backend_path, ensure_backend_on_path

ensure_backend_on_path()

from db import products_collection

def main():
    # Load behavior matrix
    behavior_path = backend_path("Ml", "behavior.pkl")
    
    if not behavior_path.exists():
        print("Behavior.pkl not found!")
        return
    
    with behavior_path.open('rb') as f:
        behavior_matrix = pickle.load(f)
    
    # Get all ML IDs
    ml_ids = list(behavior_matrix.index)
    print(f"Total ML IDs available: {len(ml_ids)}")
    
    # Get all products (not just first 100)
    products = list(products_collection.find({}, {"_id": 1, "name": 1}).limit(500))
    print(f"Total products to update: {len(products)}")
    
    # Assign ML IDs to all products
    updated_count = 0
    for i, product in enumerate(products):
        if i < len(ml_ids):
            ml_id = str(ml_ids[i])
            asin = f"B{ml_id[:7].zfill(7)}"
            
            # Check if already has ml_id
            existing = products_collection.find_one({"_id": product["_id"], "ml_id": {"$exists": True}})
            if not existing:
                result = products_collection.update_one(
                    {"_id": product["_id"]},
                    {"$set": {"ml_id": ml_id, "asin": asin}}
                )
                if result.modified_count > 0:
                    updated_count += 1
    
    print(f"Updated {updated_count} products with ML IDs")
    
    # Verify
    count_with_ml = products_collection.count_documents({"ml_id": {"$exists": True}})
    print(f"Total products with ml_id: {count_with_ml}")
    
    # Check distribution
    print("\nSample ML IDs assigned:")
    samples = list(products_collection.find({"ml_id": {"$exists": True}}, {"_id": 1, "name": 1, "ml_id": 1}).limit(5))
    for sample in samples:
        print(f"  - {sample['name']}: ml_id={sample.get('ml_id')}")

if __name__ == "__main__":
    main()
