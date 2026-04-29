import requests
import json

BASE = "http://localhost:5000"
session = requests.Session()

# 1. Login as admin
login_data = {"email": "admin@faircart.com", "password": "secure123"}
resp = session.post(BASE + "/admin-login", json=login_data)
print("Login status:", resp.status_code)
print("Login response:", resp.text)

# 2. Fetch admin-data (should work without auth? but let's try)
resp2 = session.get(BASE + "/admin-data")
print("\nAdmin-data status:", resp2.status_code)
print("Admin-data response:", resp2.text)

# 3. Fetch pending products (requires admin)
resp3 = session.get(BASE + "/api/admin/pending-products")
print("\nPending products status:", resp3.status_code)
print("Pending products response:", resp3.text[:500])

# 4. Fetch stats
resp4 = session.get(BASE + "/api/admin/stats")
print("\nStats status:", resp4.status_code)
print("Stats response:", resp4.text[:500])