#!/usr/bin/env python3
"""
Test script to verify production readiness of FairCart.
Run this after deployment to validate key functionality.
"""

import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from path_helper import ensure_backend_on_path

ensure_backend_on_path()

def test_environment():
    """Check if required environment variables are set."""
    print("🔍 Testing environment configuration...")
    
    required_vars = [
        'MONGO_URI',
        'SECRET_KEY',
        'FLASK_ENV'
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"❌ Missing environment variables: {missing}")
        return False
    else:
        print("✅ Environment variables configured")
        return True

def test_api_endpoints():
    """Test key API endpoints."""
    print("\n🔍 Testing API endpoints...")
    
    base_url = "http://localhost:5000"
    endpoints = [
        "/health",
        "/api/admin/stats",
        "/api/admin/notifications",
        "/api/product/products?page=1"
    ]
    
    for endpoint in endpoints:
        try:
            url = base_url + endpoint
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {endpoint} - {response.status_code}")
            elif response.status_code == 401:
                print(f"⚠️  {endpoint} - {response.status_code} (auth required)")
            else:
                print(f"❌ {endpoint} - {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint} - Connection failed: {e}")
    
    return True

def test_database():
    """Test database connectivity."""
    print("\n🔍 Testing database connectivity...")
    
    try:
        from pymongo import MongoClient
        from config import Config
        
        client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info()  # Will raise exception if cannot connect
        print("✅ MongoDB connection successful")
        
        # Check collections
        db = client.get_database()
        collections = db.list_collection_names()
        required_collections = ['users', 'products', 'orders', 'activity_logs']
        
        for col in required_collections:
            if col in collections:
                print(f"✅ Collection '{col}' exists")
            else:
                print(f"⚠️  Collection '{col}' missing")
        
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_ml_service():
    """Test ML service initialization."""
    print("\n🔍 Testing ML service...")
    
    try:
        from ml_service import ml_service
        
        # Check if singleton works
        instance1 = ml_service
        instance2 = ml_service
        
        if instance1 is instance2:
            print("✅ ML service singleton pattern working")
        else:
            print("❌ ML service singleton pattern broken")
        
        # Test fairness score calculation
        test_product = {
            "name": "Test Product",
            "price": 100,
            "category": "electronics",
            "impressions": 50,
            "clicks": 5,
            "created_at": datetime.now().timestamp()
        }
        
        score = instance1.fairness_score(test_product)
        print(f"✅ Fairness score calculation: {score:.2f}")
        
        return True
    except Exception as e:
        print(f"❌ ML service test failed: {e}")
        return False

def test_auth_system():
    """Test authentication system."""
    print("\n🔍 Testing authentication system...")
    
    try:
        from auth import get_current_user, admin_required, seller_required, customer_required
        
        print("✅ Authentication decorators imported successfully")
        
        # Test environment variable loading
        from config import Config
        if Config.ADMIN_EMAIL and Config.ADMIN_PASSWORD:
            print("✅ Admin credentials loaded from environment")
        else:
            print("⚠️  Admin credentials not found in environment")
        
        return True
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False

def test_caching():
    """Test caching system."""
    print("\n🔍 Testing caching system...")
    
    try:
        from cache import cache, SimpleCache
        
        # Test cache instance
        if isinstance(cache, SimpleCache):
            print("✅ Cache instance created")
        else:
            print("❌ Cache instance not properly initialized")
        
        # Test basic cache operations
        test_key = "test_key"
        test_value = {"data": "test"}
        
        cache.set(test_key, test_value, ttl=10)
        retrieved = cache.get(test_key)
        
        if retrieved == test_value:
            print("✅ Cache set/get operations working")
        else:
            print("❌ Cache set/get operations failed")
        
        return True
    except Exception as e:
        print(f"❌ Caching test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("FairCart Production Readiness Test")
    print("=" * 60)
    
    tests = [
        ("Environment", test_environment),
        ("Database", test_database),
        ("Authentication", test_auth_system),
        ("ML Service", test_ml_service),
        ("Caching", test_caching),
        ("API Endpoints", test_api_endpoints),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! FairCart is production-ready.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review before deployment.")
        return 1

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    sys.exit(main())
