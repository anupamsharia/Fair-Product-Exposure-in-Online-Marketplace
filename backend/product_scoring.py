import time
from typing import Iterable, Optional

from bson.objectid import ObjectId
from pymongo import UpdateOne

from db import products_collection
from ml_service import ml_service

SCORE_VERSION = 3

SCORE_PROJECTION = {
    "_id": 1,
    "name": 1,
    "description": 1,
    "tags": 1,
    "seo_keywords": 1,
    "hidden_seo_keywords": 1,
    "image_url": 1,
    "image_urls": 1,
    "impressions": 1,
    "clicks": 1,
    "ml_id": 1,
    "asin": 1,
    "created_at": 1,
    "fair_score": 1,
    "final_score": 1,
    "score_components": 1,
    "exposure_bucket": 1,
    "score_version": 1,
}


def _now_ts():
    return int(time.time())


def score_fields_for_product(product):
    breakdown = ml_service.score_breakdown(product)
    return {
        "fair_score": breakdown["fairness_score"],
        "final_score": breakdown["final_score"],
        "score_components": {
            "ctr": breakdown["ctr"],
            "seo": breakdown["seo_score"],
            "review": breakdown["review_score"],
            "fairness": breakdown["fairness_score"],
            "weights": breakdown["weights"],
        },
        "exposure_bucket": breakdown["exposure_bucket"],
        "score_version": SCORE_VERSION,
        "score_updated_at": _now_ts(),
    }


def product_scores_outdated(product):
    return (
        product.get("score_version") != SCORE_VERSION
        or not isinstance(product.get("fair_score"), (int, float))
        or not isinstance(product.get("final_score"), (int, float))
        or not product.get("exposure_bucket")
        or not isinstance(product.get("score_components"), dict)
    )


def apply_score_fields(product):
    enriched = dict(product)
    enriched.update(score_fields_for_product(enriched))
    return enriched


def refresh_product_scores(product_id=None, product=None):
    if product is None:
        if not product_id:
            return None
        try:
            lookup_id = ObjectId(str(product_id))
        except Exception:
            return None
        product = products_collection.find_one({"_id": lookup_id}, SCORE_PROJECTION)
        if not product:
            return None
        product_id = lookup_id
    else:
        product_id = product.get("_id", product_id)

    if not product_id:
        return None

    fields = score_fields_for_product(product)
    products_collection.update_one({"_id": product_id}, {"$set": fields})
    return fields


def refresh_product_scores_bulk(product_ids: Optional[Iterable[str]] = None, query=None, missing_only=False, limit=None):
    filters = dict(query or {})

    if product_ids:
        object_ids = []
        for product_id in product_ids:
            try:
                object_ids.append(ObjectId(str(product_id)))
            except Exception:
                continue
        if not object_ids:
            return 0
        filters["_id"] = {"$in": object_ids}

    if missing_only:
        outdated_query = {
            "$or": [
                {"score_version": {"$ne": SCORE_VERSION}},
                {"score_version": {"$exists": False}},
                {"fair_score": {"$exists": False}},
                {"final_score": {"$exists": False}},
            ]
        }
        if filters:
            filters = {"$and": [filters, outdated_query]}
        else:
            filters = outdated_query

    cursor = products_collection.find(filters, SCORE_PROJECTION)
    if limit:
        cursor = cursor.limit(limit)

    bulk_ops = []
    updated_count = 0
    for product in cursor:
        fields = score_fields_for_product(product)
        bulk_ops.append(UpdateOne({"_id": product["_id"]}, {"$set": fields}))
        updated_count += 1

    if bulk_ops:
        products_collection.bulk_write(bulk_ops, ordered=False)

    return updated_count
