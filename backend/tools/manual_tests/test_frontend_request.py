import requests
import json

url = 'http://localhost:5000/api/product/products?page=1&limit=40&search='
try:
    r = requests.get(url)
    print('Status:', r.status_code)
    data = r.json()
    print('Total:', data.get('total'))
    print('Products length:', len(data.get('products', [])))
    if data['products']:
        print('First product name:', data['products'][0]['name'])
    else:
        print('No products in response')
except Exception as e:
    print('Error:', e)