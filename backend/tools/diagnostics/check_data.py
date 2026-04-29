import requests
import json

BASE = "http://localhost:5000"
s = requests.Session()
# login
s.post(BASE + "/admin-login", json={"email": "admin@faircart.com", "password": "secure123"})
# get pending products
resp = s.get(BASE + "/api/admin/pending-products")
data = resp.json()
print("Pending products count:", len(data.get('products', [])))
for p in data.get('products', []):
    print(p.get('name'), p.get('status'))

# get admin-data
resp2 = s.get(BASE + "/admin-data")
print("\nAdmin-data:", resp2.json())

# get stats
resp3 = s.get(BASE + "/api/admin/stats")
stats = resp3.json()
print("\nStats:", stats)