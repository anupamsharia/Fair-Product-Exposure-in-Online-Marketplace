from pathlib import Path
import sys

TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from path_helper import ensure_backend_on_path

ensure_backend_on_path()

from db import products_collection
import pprint

# Get first few products
for p in products_collection.find().limit(5):
    print('---')
    pprint.pprint({k: v for k, v in p.items() if k not in ['_id']})
    print('Status:', p.get('status'))
    print('Approved:', p.get('approved'))
