from pathlib import Path
import sys

TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from path_helper import ensure_backend_on_path

ensure_backend_on_path()

from db import products_collection

# Update products where status is None or missing and approved is True
result = products_collection.update_many(
    {"$or": [{"status": None}, {"status": {"$exists": False}}], "approved": True},
    {"$set": {"status": "approved"}}
)
print(f"Matched {result.matched_count} products, modified {result.modified_count}")

# Also update products where status is empty string?
result2 = products_collection.update_many(
    {"status": "", "approved": True},
    {"$set": {"status": "approved"}}
)
print(f"Empty string matched {result2.matched_count}, modified {result2.modified_count}")

# Verify counts
approved_count = products_collection.count_documents({"status": "approved"})
print(f"Total approved products now: {approved_count}")
