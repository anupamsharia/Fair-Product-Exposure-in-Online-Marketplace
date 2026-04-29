from pathlib import Path
import sys

TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from path_helper import ensure_backend_on_path

ensure_backend_on_path()

from db import products_collection

distinct = products_collection.distinct('status')
print('Distinct statuses:', distinct)
print('Count per status:')
for s in distinct:
    cnt = products_collection.count_documents({'status': s})
    print(f'  {s}: {cnt}')
print('Products without status field:', products_collection.count_documents({'status': {'$exists': False}}))
print('Total products:', products_collection.count_documents({}))
