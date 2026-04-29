import requests
import json
from pathlib import Path
import sys

TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from path_helper import ensure_backend_on_path

ensure_backend_on_path()

from db import products_collection

def test_recommendations_detailed():
    # Find a product with ml_id
    product_with_ml = products_collection.find_one({"ml_id": {"$exists": True}}, {"_id": 1, "name": 1, "ml_id": 1})
    if not product_with_ml:
        print("No products with ml_id found!")
        return
    
    product_id = str(product_with_ml["_id"])
    product_name = product_with_ml["name"]
    ml_id = product_with_ml.get("ml_id")
    
    print(f"Testing recommendations for product: {product_name}")
    print(f"Product ID: {product_id}")
    print(f"ML ID: {ml_id}")
    
    # Test the recommendation endpoint
    try:
        response = requests.get(f"http://localhost:5000/api/ml/recommend?id={product_id}")
        if response.status_code == 200:
            data = response.json()
            recommendations = data.get("recommendations", [])
            print(f"\nAPI returned {len(recommendations)} recommendations")
            
            # Check each recommendation
            for i, rec in enumerate(recommendations, 1):
                has_ml_id = 'ml_id' in rec
                ml_id_val = rec.get('ml_id', 'N/A')
                print(f"  {i}. {rec.get('name')} - ml_id: {ml_id_val} {'(ML-based)' if has_ml_id else '(Category-based)'}")
            
            # Check what ML IDs the service returned
            print("\n--- Checking ML Service Output ---")
            from ml_service import ml_service
            ml_recommendations = ml_service.get_related_products(product_id)
            print(f"ML service returned IDs: {ml_recommendations}")
            
            # Check which of these exist in DB
            if ml_recommendations:
                matching = list(products_collection.find(
                    {"ml_id": {"$in": ml_recommendations}},
                    {"_id": 1, "name": 1, "ml_id": 1, "status": 1}
                ))
                print(f"\nProducts in DB matching ML IDs:")
                for p in matching:
                    print(f"  - {p['name']} (ml_id: {p.get('ml_id')}, status: {p.get('status')})")
                
                # Check why they might not be in API response
                print(f"\nChecking API query logic...")
                # The API query looks for: {"ml_id": {"$in": ml_recommendations}, "status": "approved"}
                approved_matching = [p for p in matching if p.get('status') == 'approved']
                print(f"Approved products: {len(approved_matching)}")
                
        else:
            print(f"Error: Status code {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error making request: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_recommendations_detailed()
