import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from path_helper import ensure_backend_on_path

ensure_backend_on_path()

try:
    from ml_service import ml_service
    print("[SUCCESS] ML Service Loaded Successfully\n")
except ImportError as e:
    print(f"[ERROR] Error importing ml_service: {e}")
    sys.exit(1)

def run_validation():
    print("="*60)
    print(" FAIRNESS SYSTEM VALIDATION REPORT ")
    print("="*60)

    # --- TEST CASE 1 & 2: NEW vs OLD ---
    new_product = {
        "name": "New Premium Headphones",
        "description": "High fidelity sound, noise cancelling, long battery life. Perfect for music enthusiasts.",
        "tags": ["audio", "wireless", "premium", "noise-cancelling", "tech"],
        "impressions": 5,
        "clicks": 1,
        "asin": "B0NEW"
    }

    old_popular = {
        "name": "Classic Sneakers",
        "description": "The original classic sneakers, durable and stylish.",
        "tags": ["shoes", "classic"],
        "impressions": 500,
        "clicks": 200,
        "asin": "B0OLD"
    }

    average_product = {
        "name": "Generic Cable",
        "description": "A cable that works.",
        "tags": ["cable"],
        "impressions": 100,
        "clicks": 5,
        "asin": "B0GEN"
    }

    score_new = ml_service.final_score(new_product)
    score_old = ml_service.final_score(old_popular)
    score_avg = ml_service.final_score(average_product)

    print(f"[CASE 1 & 2] Ranking Results:")
    print(f"1. {new_product['name']} (NEW) -> Score: {score_new}")
    print(f"2. {old_popular['name']} (POPULAR) -> Score: {score_old}")
    print(f"3. {average_product['name']} (AVG) -> Score: {score_avg}")
    
    if score_new > score_old:
        print("[PASS] SUCCESS: New product boosted above popular old product.")
    else:
        print("[FAIL] FAILURE: Old product still dominating.")

    # --- TEST CASE 3: FAIRNESS DECAY ---
    print("\n[CASE 3] Decay Analysis (Product 'Aging'):")
    decay_tracking = []
    for imp in [0, 10, 30, 60, 100, 500]:
        new_product['impressions'] = imp
        score = ml_service.final_score(new_product)
        decay_tracking.append((imp, score))
        print(f"   Impressions: {imp:3} | Score: {score}")

    if decay_tracking[0][1] > decay_tracking[-1][1]:
        print("[PASS] SUCCESS: Fairness boost decays correctly as impressions increase.")
    else:
        print("[FAIL] FAILURE: Boost is static.")

    # --- TEST CASE 4: BAD PRODUCT CHECK ---
    print("\n[CASE 4] Quality Penalty Check:")
    bad_product = {
        "name": "hph",
        "description": "small desc",
        "tags": [],
        "impressions": 0,
        "clicks": 0
    }
    score_bad = ml_service.final_score(bad_product)
    print(f"   Bad Product ('hph') Score: {score_bad}")
    if score_bad < score_new:
        print("[PASS] SUCCESS: Poor quality listing penalized despite being new.")
    else:
        print("[FAIL] FAILURE: Bad quality item ranked too high.")

    # --- TEST CASE 5: MIXED FEED SORTING ---
    print("\n[CASE 5] Mixed Feed Sorting Simulation (10 items):")
    feed = [
        {"name": "New Item A", "impressions": 2, "clicks": 0, "tags": ["a","b","c","d","e"]},
        {"name": "Popular Item B", "impressions": 1000, "clicks": 400, "tags": ["a"]},
        {"name": "Popular Item C", "impressions": 800, "clicks": 350, "tags": ["a"]},
        {"name": "Average Item D", "impressions": 100, "clicks": 2, "tags": ["a"]},
        {"name": "New Item E", "impressions": 1, "clicks": 0, "tags": ["a","b","c","d","e"]},
        {"name": "Spam Item F", "impressions": 0, "clicks": 0, "tags": []},
    ]
    
    for item in feed:
        item['score'] = ml_service.final_score(item)
    
    sorted_feed = sorted(feed, key=lambda x: x['score'], reverse=True)
    
    for i, item in enumerate(sorted_feed, 1):
        print(f"   {i}. {item['name']:15} | Score: {item['score']}")

    # --- TEST CASE 6: RECOMMENDATION SYSTEM ---
    print("\n[CASE 6] Recommendation Logic:")
    # Using a known ID from behavior dataset if available, else mock
    mock_id = 972683280 
    recos = ml_service.get_related_products(mock_id)
    print(f"   Recommendations for ID {mock_id}: {recos}")
    if recos:
        print("[PASS] SUCCESS: ML Model returned related products.")
    else:
        print("[WARN] WARNING: No recommendations returned (might be model coverage).")

    print("\n" + "="*60)
    print(" VALIDATION COMPLETE ")
    print("="*60)

if __name__ == "__main__":
    run_validation()
