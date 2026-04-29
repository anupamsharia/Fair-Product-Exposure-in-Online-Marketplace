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
    # Load behavior matrix to get available ML IDs
    behavior_path = backend_path("Ml", "behavior.pkl")
    
    if not behavior_path.exists():
        print("Behavior.pkl not found!")
        return
    
    with behavior_path.open('rb') as f:
        behavior_matrix = pickle.load(f)
    
    # Get all ML IDs from the behavior matrix
    ml_ids = list(behavior_matrix.index)
    print(f"Total ML IDs available: {len(ml_ids)}")
    print(f"Sample ML IDs: {ml_ids[:5]}")
    
    # Get all products without ml_id
    products = list(products_collection.find({"ml_id": {"$exists": False}}, {"_id": 1, "name": 1}).limit(100))
    print(f"Products without ml_id: {len(products)}")
    
    # Assign ML IDs to products
    updated_count = 0
    for i, product in enumerate(products):
        if i < len(ml_ids):
            ml_id = str(ml_ids[i])
            # Also create a simple ASIN for review scoring
            asin = f"B{ml_id[:7].zfill(7)}"
            
            result = products_collection.update_one(
                {"_id": product["_id"]},
                {"$set": {"ml_id": ml_id, "asin": asin}}
            )
            if result.modified_count > 0:
                updated_count += 1
    
    print(f"Updated {updated_count} products with ML IDs")
    
    # Verify
    count_with_ml = products_collection.count_documents({"ml_id": {"$exists": True}})
    print(f"Products with ml_id after update: {count_with_ml}")
    
    # Show some samples
    samples = list(products_collection.find({"ml_id": {"$exists": True}}, {"_id": 1, "name": 1, "ml_id": 1, "asin": 1}).limit(3))
    print("\nSample updated products:")
    for sample in samples:
        print(f"  - {sample['name']}: ml_id={sample.get('ml_id')}, asin={sample.get('asin')}")

if __name__ == "__main__":
    main()
