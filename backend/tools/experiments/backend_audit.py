import requests
import sys

def check_backend_health():
    base_url = "http://localhost:5000"
    print(f"--- FairCart Backend Health Audit ---")
    print(f"Target: {base_url}\n")
    
    # 1. Basic Connectivity
    try:
        res = requests.get(base_url)
        print(f"[Core] Home Endpoint: {'OK' if res.status_code == 200 else 'FAIL'} ({res.status_code})")
    except Exception as e:
        print(f"[Core] Home Endpoint: CRITICAL FAILURE (Backend may be down) - {e}")
        return

    # 2. Product API
    try:
        res = requests.get(f"{base_url}/api/product/products")
        data = res.json()
        count = len(data.get('products', []))
        print(f"[API] Product List: {'OK' if res.status_code == 200 else 'FAIL'} ({count} items found)")
    except Exception as e:
        print(f"[API] Product List: FAIL - {e}")

    # 3. ML API (Recommend)
    try:
        # Using a known ml_id from our seeded data
        res = requests.get(f"{base_url}/api/ml/recommend?id=1002524")
        data = res.json()
        recos = len(data.get('recommendations', []))
        print(f"[ML] Recommendation Engine: {'OK' if res.status_code == 200 else 'FAIL'} ({recos} recommendations returned)")
    except Exception as e:
        print(f"[ML] Recommendation Engine: FAIL - {e}")

    # 4. ML API (Sentiment)
    try:
        res = requests.get(f"{base_url}/api/ml/sentiment?asin=B007JFMH8M")
        data = res.json()
        score = data.get('score', 0)
        print(f"[ML] Sentiment Engine: {'OK' if res.status_code == 200 and score > 0 else 'FAIL'} (Score: {score})")
    except Exception as e:
        print(f"[ML] Sentiment Engine: FAIL - {e}")

    # 5. Database Connection (via endpoint that touches DB)
    try:
        res = requests.get(f"{base_url}/api/product/single?id=invalid_id")
        # if we reach here and it doesn't timeout, DB is likely connected
        print(f"[DB] MongoDB Connectivity: PROBABLE OK")
    except Exception as e:
        print(f"[DB] MongoDB Connectivity: FAIL - {e}")

if __name__ == "__main__":
    check_backend_health()
