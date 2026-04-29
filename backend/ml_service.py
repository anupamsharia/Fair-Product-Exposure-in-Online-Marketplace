import math
import os
import pickle
import time
from datetime import datetime

import pandas as pd


def _clamp(value, minimum=0.0, maximum=1.0):
    return max(minimum, min(maximum, value))


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value, default=0):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _created_timestamp(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.timestamp()
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
            except ValueError:
                return None
    return None

class MLService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MLService, cls).__new__(cls)
            cls._instance.behavior_matrix = None
            cls._instance.reviews_data = None
            cls._instance.load_models()
        return cls._instance

    def load_models(self):
        print("--- Loading ML Models into Memory ---")
        try:
            # Use absolute paths relative to this file's location
            base_dir = os.path.dirname(os.path.abspath(__file__))
            behavior_path = os.path.join(base_dir, 'Ml', 'behavior.pkl')
            reviews_path = os.path.join(base_dir, 'Ml', 'reviews.pkl')

            # Behavior Matrix (Recommendations)
            if os.path.exists(behavior_path):
                with open(behavior_path, 'rb') as f:
                    self.behavior_matrix = pickle.load(f)
                print(f"Loaded behavior matrix: {self.behavior_matrix.shape}")

            # Reviews Data (Sentiment/Quality)
            if os.path.exists(reviews_path):
                with open(reviews_path, 'rb') as f:
                    self.reviews_data = pickle.load(f)
                print(f"Loaded reviews data: {self.reviews_data.shape}")
        except Exception as e:
            print(f"Error loading ML models: {e}")

    def get_review_score(self, product_id):
        """Step 2: Get review score from ML data."""
        try:
            if self.reviews_data is not None and product_id in self.reviews_data.index:
                return float(self.reviews_data[product_id])
            return 0.0
        except:
            return 0.0

    def get_related_products(self, product_id, top_n=5):
        metadata = self.get_related_products_metadata(product_id, top_n=top_n)
        return metadata["related_ids"]

    def get_related_products_metadata(self, product_id, top_n=5):
        """Step 3: Recommendation system using behavior matrix."""
        metadata = {
            "related_ids": [],
            "mode": "category-fallback",
            "seed_id": None,
        }
        try:
            if self.behavior_matrix is None:
                metadata["mode"] = "behavior-unavailable"
                return metadata
            
            product = self._find_product_for_recommendation(product_id)
            if not product:
                metadata["mode"] = "product-not-found"
                return metadata

            ml_id = product.get("ml_id")
            if not ml_id:
                return metadata
            
            pid = int(str(ml_id))
            if pid not in self.behavior_matrix.index:
                return metadata
            
            similar = self.behavior_matrix.loc[pid]
            recommendations = similar.sort_values(ascending=False).iloc[1:top_n+1].index.tolist()
            metadata["related_ids"] = [str(rid) for rid in recommendations]
            metadata["mode"] = "ml-ranked"
            metadata["seed_id"] = str(pid)
            return metadata
        except Exception as e:
            print(f"Error in get_related_products: {e}")
            metadata["mode"] = "category-fallback"
            return metadata
    
    def _find_product_for_recommendation(self, product_id):
        """Find the product used as the recommendation seed."""
        try:
            from db import products_collection
            from bson.objectid import ObjectId
            
            product = products_collection.find_one({"_id": ObjectId(product_id)})
            if product:
                return product
        except:
            pass

        try:
            from db import products_collection
            return products_collection.find_one({"ml_id": str(product_id)})
        except:
            return None

    def exposure_bucket(self, product):
        impressions = _safe_int(product.get("impressions", 0))
        if impressions == 0:
            return "new"
        if impressions < 25:
            return "low_exposure"
        if impressions < 100:
            return "growing"
        return "established"

    def fairness_score(self, product, seller_products_count=1, total_seller_products=10):
        """
        Calculate an exposure fairness score with decay logic.
        
        Args:
            product: Product dictionary
            seller_products_count: Number of products from same seller on current page
            total_seller_products: Total products from this seller in system
        
        Returns:
            Fairness score between 0.0 and 1.0
        """
        impressions = _safe_int(product.get("impressions", 0))
        
        # Smooth decay: underexposed products receive discovery priority, but
        # the boost fades as real impressions arrive.
        exposure_gap = 1 / math.sqrt(impressions + 1)
        base_score = 0.2 + (0.8 * exposure_gap)
        
        # Seller diversity penalty: reduce score if same seller dominates
        seller_penalty = 0.0
        if seller_products_count > 2:
            # If more than 2 products from same seller on page, apply penalty
            seller_penalty = min(0.3, (seller_products_count - 2) * 0.1)
        
        # Time decay (if product has creation date)
        time_decay = 0.0
        created_time = _created_timestamp(product.get("created_at"))
        if created_time:
            age_days = (time.time() - created_time) / (24 * 3600)
            if age_days > 30:
                time_decay = min(0.18, (age_days - 30) * 0.008)
        
        # Calculate final fairness score
        fairness = base_score - seller_penalty - time_decay
        return round(_clamp(fairness, 0.08, 1.0), 3)

    def seo_score(self, product):
        """Step 5: SEO Quality metrics."""
        score = 0
        if len(product.get("name") or "") > 20:
            score += 0.2
        if len(product.get("description") or "") > 100:
            score += 0.3
        tags = product.get("tags") or []
        keywords = product.get("seo_keywords") or product.get("hidden_seo_keywords") or []
        if isinstance(keywords, str):
            keywords = [k.strip() for k in keywords.split(",") if k.strip()]
        if len(tags) >= 5 or len(keywords) >= 5:
            score += 0.2
        if product.get("image_url") or product.get("image_urls"):
            score += 0.1
        return round(min(score, 1.0), 3)

    def score_breakdown(self, product):
        """Return the public ranking components used by the marketplace."""
        impressions = _safe_int(product.get("impressions", 0))
        clicks = _safe_int(product.get("clicks", 0))
        ctr = _clamp(clicks / max(impressions, 1), 0.0, 1.0)
        review = _clamp(self.get_review_score(product.get("ml_id") or product.get("asin") or "") / 100)
        fairness = self.fairness_score(product)
        seo = self.seo_score(product)

        if impressions == 0:
            weights = {"fairness": 0.45, "seo": 0.35, "review": 0.20, "ctr": 0.0}
            score = (weights["fairness"] * fairness) + (weights["seo"] * seo) + (weights["review"] * review)
            if seo >= 0.35:
                score = max(score, 0.68)
            elif seo >= 0.20:
                score = max(score, 0.46)
            else:
                score = min(score, 0.34)
        elif impressions < 25:
            weights = {"fairness": 0.40, "seo": 0.20, "review": 0.15, "ctr": 0.25}
            score = (
                (weights["fairness"] * fairness)
                + (weights["seo"] * seo)
                + (weights["review"] * review)
                + (weights["ctr"] * ctr)
            )
            score = max(score, 0.52 if seo >= 0.25 else 0.38)
        elif impressions < 100:
            weights = {"fairness": 0.30, "seo": 0.15, "review": 0.15, "ctr": 0.40}
            score = (
                (weights["fairness"] * fairness)
                + (weights["seo"] * seo)
                + (weights["review"] * review)
                + (weights["ctr"] * ctr)
            )
        else:
            weights = {"fairness": 0.22, "seo": 0.13, "review": 0.20, "ctr": 0.45}
            score = (
                (weights["fairness"] * fairness)
                + (weights["seo"] * seo)
                + (weights["review"] * review)
                + (weights["ctr"] * ctr)
            )

        return {
            "final_score": round(_clamp(score), 3),
            "fairness_score": fairness,
            "seo_score": seo,
            "review_score": round(review, 3),
            "ctr": round(ctr, 3),
            "impressions": impressions,
            "clicks": clicks,
            "exposure_bucket": self.exposure_bucket(product),
            "weights": weights,
        }

    def final_score(self, product):
        """Step 6: Dynamic ranking formula."""
        return self.score_breakdown(product)["final_score"]

    def smart_search(self, query, products):
        """AI Smart Search implementation."""
        if not query: return products
        query = query.lower()
        results = []
        for p in products:
            score = 0
            if query in (p.get("name") or "").lower(): score += 2
            if query in (p.get("description") or "").lower(): score += 1
            if query in " ".join(p.get("tags") or []).lower(): score += 2
            keywords = p.get("seo_keywords") or p.get("hidden_seo_keywords") or []
            if isinstance(keywords, str):
                keywords = [k.strip() for k in keywords.split(",") if k.strip()]
            if query in " ".join(keywords).lower(): score += 2
            if score > 0: results.append((score, p))
        results.sort(key=lambda x: x[0], reverse=True)
        return [p[1] for p in results]

# Singleton instance
ml_service = MLService()
