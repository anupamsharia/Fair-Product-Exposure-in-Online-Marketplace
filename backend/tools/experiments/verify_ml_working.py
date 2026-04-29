import pickle
import pandas as pd
from pathlib import Path
import sys

TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from path_helper import backend_path

def test_ml_models():
    print("--- Testing ML Models Accessibility ---")
    
    # test reviews (sentiment/quality)
    try:
        with backend_path("Ml", "reviews.pkl").open('rb') as f:
            reviews = pickle.load(f)
        asin = reviews.index[0]
        score = reviews[asin]
        print(f"REVIEW MODEL: Successfully retrieved score for {asin}: {score:.2f}")
    except Exception as e:
        print(f"REVIEW MODEL ERROR: {e}")

    # test behavior (recommendation matrix)
    try:
        with backend_path("Ml", "behavior.pkl").open('rb') as f:
            behavior = pickle.load(f)
        
        test_id = behavior.index[0]
        similar_items = behavior.loc[test_id].sort_values(ascending=False)[1:6] 
        print(f"BEHAVIOR MODEL: Successfully recommended {len(similar_items)} items for product {test_id}")
        print(f"   Similar IDs: {similar_items.index.tolist()}")
    except Exception as e:
        print(f"BEHAVIOR MODEL ERROR: {e}")

if __name__ == "__main__":
    test_ml_models()
