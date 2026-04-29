from pathlib import Path
import sys
import datetime

TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from path_helper import ensure_backend_on_path

ensure_backend_on_path()

from db import products_collection

# Insert a test product with status pending
test_product = {
    "name": "Test Product",
    "price": 100,
    "category": "General",
    "description": "Test description",
    "seller_id": "test@example.com",
    "status": "pending",
    "fraud_flag": False,
    "created_at": str(int(datetime.datetime.now().timestamp()))
}
result = products_collection.insert_one(test_product)
print(f"Inserted product id: {result.inserted_id}")

# Count pending products
pending_count = products_collection.count_documents({"status": "pending"})
print(f"Pending products count: {pending_count}")

# Fetch pending products
pending = list(products_collection.find({"status": "pending"}))
for p in pending:
    print(p.get('name'), p.get('status'))
