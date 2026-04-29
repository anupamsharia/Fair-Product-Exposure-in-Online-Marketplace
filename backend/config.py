import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/faircart")
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret_key_if_not_found")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@faircart.com")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "secure123")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "vision-key.json")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:8000,http://127.0.0.1:8000,"
        "http://localhost:8001,http://127.0.0.1:8001,"
        "http://localhost:5000,http://127.0.0.1:5000"
    ).split(",")
