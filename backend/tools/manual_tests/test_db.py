from pathlib import Path
import sys

from pymongo import MongoClient

TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from path_helper import ensure_backend_on_path

ensure_backend_on_path()

from config import Config

try:
    client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=5000, tls=True, tlsAllowInvalidCertificates=True)
    db = client.get_database("faircart")
    print(f"Successfully connected to database: {db.name}")
except Exception as e:
    print(f"Failed to connect: {e}")
