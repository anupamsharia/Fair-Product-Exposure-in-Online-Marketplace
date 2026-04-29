from pathlib import Path
import sys

TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from path_helper import ensure_backend_on_path

ensure_backend_on_path()

from db import products_collection

def main():
    count_with_ml = products_collection.count_documents({'ml_id': {'$exists': True}})
    count_with_asin = products_collection.count_documents({'asin': {'$exists': True}})
    
    print(f'Products with ml_id: {count_with_ml}')
    print(f'Products with asin: {count_with_asin}')
    
    if count_with_ml > 0:
        sample = products_collection.find_one({'ml_id': {'$exists': True}}, {'_id': 1, 'name': 1, 'ml_id': 1, 'asin': 1})
        print(f'Sample with ml_id: {sample}')
    
    # Check total products
    total = products_collection.count_documents({})
    print(f'Total products: {total}')

if __name__ == "__main__":
    main()
