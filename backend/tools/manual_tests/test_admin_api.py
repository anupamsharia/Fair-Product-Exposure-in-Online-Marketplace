import requests
import json

base = "http://localhost:5000"
# First, login as admin (if required)
# The admin routes are protected with @admin_required which checks session.
# We can simulate by setting a session cookie? Let's just call the endpoint directly.
# The admin_required decorator likely checks session['admin'] == True.
# We can bypass by using the same session as the running Flask app? Hard.
# Let's try to call the endpoint without auth and see if we get 401.
# If we get 401, that's the issue: admin not logged in.

resp = requests.get(base + "/api/admin/pending-products", cookies={'session': '...'})
print("Status:", resp.status_code)
print("Headers:", resp.headers)
print("Body:", resp.text[:500])

# Also test /admin-data endpoint
resp2 = requests.get(base + "/admin-data")
print("\n/admin-data status:", resp2.status_code)
print("Body:", resp2.text)