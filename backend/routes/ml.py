from flask import Blueprint, request, jsonify
from bson.objectid import ObjectId
from ml_service import ml_service
from db import products_collection
from product_queries import approved_product_query

ml_bp = Blueprint("ml", __name__)

RECOMMENDATION_PROJECTION = {
    "_id": 1,
    "name": 1,
    "price": 1,
    "category": 1,
    "image_url": 1,
    "image_urls": 1,
    "icon": 1,
    "ml_id": 1,
    "seller_id": 1,
    "seller_name": 1,
    "on_sale": 1,
    "original_price": 1,
    "created_at": 1,
}


def _serialize(product):
    product = dict(product)
    product["_id"] = str(product["_id"])
    urls = product.get("image_urls") or []
    if isinstance(urls, str):
        urls = [urls]
    product["image_urls"] = urls
    product["image_url"] = product.get("image_url") or (urls[0] if urls else "")
    return product


def _find_current_product(product_id):
    try:
        return products_collection.find_one({"_id": ObjectId(product_id)})
    except Exception:
        return products_collection.find_one({"ml_id": str(product_id)})


@ml_bp.route("/recommend", methods=["GET"])
def recommend():
    product_id = request.args.get("id") or request.args.get("product_id")
    try:
        limit = min(int(request.args.get("limit", 6)), 12)
    except (TypeError, ValueError):
        limit = 6
    if not product_id:
        return jsonify({"message": "Product ID is required"}), 400

    current_product = _find_current_product(product_id)
    if not current_product:
        return jsonify({"recommendations": []}), 200

    category = current_product.get("category")
    current_object_id = current_product.get("_id")
    filters = {"_id": {"$ne": current_object_id}}
    if category:
        filters["category"] = category

    category_products = list(
        products_collection.find(approved_product_query(filters), RECOMMENDATION_PROJECTION)
        .sort("created_at", -1)
        .limit(limit)
    )

    # ML can influence ordering only when it stays within the same category.
    recommendation_meta = ml_service.get_related_products_metadata(str(current_object_id))
    related_ml_ids = recommendation_meta["related_ids"]
    if related_ml_ids:
        ml_rank = {ml_id: idx for idx, ml_id in enumerate(related_ml_ids)}
        category_products.sort(key=lambda p: ml_rank.get(str(p.get("ml_id")), len(ml_rank)))

    recommendations = [_serialize(p) for p in category_products]
    return jsonify({
        "recommendations": recommendations,
        "recommendation_mode": recommendation_meta["mode"],
        "ml_seed_id": recommendation_meta["seed_id"],
    }), 200


@ml_bp.route("/sentiment", methods=["GET"])
def get_sentiment():
    asin = request.args.get("asin")
    if not asin:
        return jsonify({"message": "ASIN is required"}), 400

    score = ml_service.get_review_score(asin)
    return jsonify({"asin": asin, "score": score}), 200
