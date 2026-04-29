from pymongo import MongoClient
from config import Config
import certifi

def _mongo_client_options():
    """Use TLS CA settings for Atlas/SRV connections without breaking local MongoDB."""
    uri = Config.MONGO_URI.lower()
    options = {"serverSelectionTimeoutMS": 5000}
    if uri.startswith("mongodb+srv://") or "tls=true" in uri or "ssl=true" in uri:
        options["tlsCAFile"] = certifi.where()
    return options


client = MongoClient(Config.MONGO_URI, **_mongo_client_options())
db = client.get_database("faircart")

# Expose collections
users_collection = db["users"]
products_collection = db["products"]
orders_collection = db["orders"]
activity_logs_collection = db["activity_logs"]

def log_activity(type, message, user_email="System"):
    """Save system events for the Admin Activity Feed."""
    import time
    activity_logs_collection.insert_one({
        "type": type,
        "message": message,
        "user_email": user_email,
        "user_id": user_email,
        "timestamp": int(time.time()),
        "date": time.strftime("%Y-%m-%d %H:%M:%S")
    })
