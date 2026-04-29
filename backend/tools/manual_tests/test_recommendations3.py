import requests
import json

# Test the API directly and print raw response
product_id = "69dc1ad27e9f29a692e3792a"
response = requests.get(f"http://localhost:5000/api/ml/recommend?id={product_id}")

print(f"Status: {response.status_code}")
print(f"Raw response text: {response.text[:500]}...")

if response.status_code == 200:
    data = response.json()
    print("\nParsed JSON:")
    print(json.dumps(data, indent=2)[:1000])
    
    # Also check what fields each recommendation has
    recommendations = data.get("recommendations", [])
    if recommendations:
        print(f"\nFirst recommendation keys: {list(recommendations[0].keys())}")
        print(f"First recommendation full: {recommendations[0]}")