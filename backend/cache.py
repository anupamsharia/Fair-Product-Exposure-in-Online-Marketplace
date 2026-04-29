"""
Caching module for FairCart performance improvements.
Provides in-memory caching for product listings, ML scores, and other frequently accessed data.
"""
import time
from functools import lru_cache
from typing import Any, Dict, List, Optional
import threading
from bson.objectid import ObjectId
from pymongo import UpdateOne

class SimpleCache:
    """Thread-safe in-memory cache with TTL support."""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._default_ttl = 300  # 5 minutes default TTL
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            if entry['expires_at'] < time.time():
                del self._cache[key]
                return None
            
            return entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        with self._lock:
            self._cache[key] = {
                'value': value,
                'expires_at': time.time() + (ttl or self._default_ttl)
            }
    
    def delete(self, key: str) -> None:
        """Delete key from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
    
    def get_or_set(self, key: str, factory, ttl: Optional[int] = None) -> Any:
        """Get cached value or compute and set if not present."""
        value = self.get(key)
        if value is None:
            value = factory()
            self.set(key, value, ttl)
        return value

# Global cache instance
cache = SimpleCache()

# Cache keys
PRODUCTS_CACHE_KEY = "products:all"
PRODUCTS_BY_CATEGORY_CACHE_KEY = "products:category:{category}"
ML_SCORE_CACHE_KEY = "ml:score:{product_id}"
SEARCH_CACHE_KEY = "search:{query}"

def invalidate_product_cache():
    """Invalidate all product-related caches."""
    cache.delete(PRODUCTS_CACHE_KEY)
    # Also delete all category/list/search-specific caches.
    keys_to_delete = [
        k for k in list(cache._cache.keys())
        if k.startswith("products:")
        or k.startswith("search:")
        or k.startswith("ml:score:")
    ]
    for key in keys_to_delete:
        cache.delete(key)

def cache_ml_score(product_id: str, score: float, ttl: int = 600) -> None:
    """Cache ML score for a product."""
    cache.set(ML_SCORE_CACHE_KEY.format(product_id=product_id), score, ttl)

def get_cached_ml_score(product_id: str) -> Optional[float]:
    """Get cached ML score for a product."""
    return cache.get(ML_SCORE_CACHE_KEY.format(product_id=product_id))

# LRU cache for ML service methods
@lru_cache(maxsize=1024)
def cached_final_score(product_dict: tuple) -> float:
    """
    LRU cache for final_score calculations.
    Takes a tuple representation of product dict for hashability.
    """
    from ml_service import ml_service
    # Convert tuple back to dict (simplified - in practice we'd pass key fields)
    # This is a simplified implementation - actual implementation would need
    # to extract key fields from the product
    return ml_service.final_score({})

# Batch operation utilities
class BatchProcessor:
    """Utility for batch database operations."""
    
    @staticmethod
    def batch_update_impressions(product_ids: List[str]) -> None:
        """Batch update impressions for multiple products."""
        from db import products_collection
        if not product_ids:
            return
        
        bulk_ops = []
        for product_id in product_ids:
            try:
                bulk_ops.append(UpdateOne({'_id': ObjectId(product_id)}, {'$inc': {'impressions': 1}}))
            except Exception:
                continue
        
        if bulk_ops:
            try:
                products_collection.bulk_write(bulk_ops, ordered=False)
            except Exception as e:
                print(f"Batch impression update failed: {e}")
    
    @staticmethod
    def batch_update_clicks(product_ids: List[str]) -> None:
        """Batch update clicks for multiple products."""
        from db import products_collection
        if not product_ids:
            return
        
        bulk_ops = []
        for product_id in product_ids:
            try:
                bulk_ops.append(UpdateOne({'_id': ObjectId(product_id)}, {'$inc': {'clicks': 1}}))
            except Exception:
                continue
        
        if bulk_ops:
            try:
                products_collection.bulk_write(bulk_ops, ordered=False)
            except Exception as e:
                print(f"Batch click update failed: {e}")
