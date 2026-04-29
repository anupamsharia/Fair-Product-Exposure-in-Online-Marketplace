import requests
import json

resp = requests.get('http://localhost:5000/api/product/products?page=1&limit=40&search=')
print('Status:', resp.status_code)
data = resp.json()
print('Total:', data.get('total'))
print('Products count:', len(data.get('products', [])))
if data.get('products'):
    for p in data['products'][:3]:
        print(p.get('name'), p.get('status'), p.get('_id'))