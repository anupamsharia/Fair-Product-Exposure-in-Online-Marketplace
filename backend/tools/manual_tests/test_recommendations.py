import requests
import json
from pathlib import Path
import sys

TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from path_helper import ensure_backend_on_path

ensure_backend_on_path()

def test_recommendations():
    # First, get a product ID that has an ml_id
    from db import products_collection
    
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
            print(f"\nSuccess! Got {len(recommendations)} recommendations:")
            for i, rec in enumerate(recommendations[:5], 1):
                print(f"  {i}. {rec.get('name')} (Price: ${rec.get('price')})")
            
            # Check if any have ml_id
            ml_based = [r for r in recommendations if r.get('ml_id')]
            print(f"\nML-based recommendations: {len(ml_based)}")
            category_based = len(recommendations) - len(ml_based)
            print(f"Category-based fallback: {category_based}")
        else:
            print(f"Error: Status code {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error making request: {e}")
    
    # Also test the ML service directly
    print("\n--- Testing ML Service Directly ---")
    from ml_service import ml_service
    
    # Test get_related_products
    ml_recommendations = ml_service.get_related_products(product_id)
    print(f"ML service returned {len(ml_recommendations)} ML IDs: {ml_recommendations}")
    
    # Test if these ML IDs exist in our database
    if ml_recommendations:
        from bson.objectid import ObjectId
        matching_products = list(products_collection.find(
            {"ml_id": {"$in": ml_recommendations}},
            {"_id": 1, "name": 1, "ml_id": 1}
        ))
        print(f"Found {len(matching_products)} products matching those ML IDs:")
        for p in matching_products:
            print(f"  - {p['name']} (ml_id: {p.get('ml_id')})")

if __name__ == "__main__":
    test_recommendations()
