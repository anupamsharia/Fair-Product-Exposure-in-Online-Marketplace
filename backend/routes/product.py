from flask import Blueprint, request, jsonify
from db import products_collection, users_collection, log_activity
from bson.objectid import ObjectId
from ml_service import ml_service
from cache import cache, BatchProcessor, invalidate_product_cache
from product_queries import approved_product_query
from product_scoring import (
    apply_score_fields,
    product_scores_outdated,
    refresh_product_scores,
    refresh_product_scores_bulk,
    score_fields_for_product,
)
from werkzeug.utils import secure_filename
from datetime import datetime
import json
import os
import time
import uuid

from auth import get_current_user, is_admin_session, seller_or_admin_required, seller_required

product_bp = Blueprint("product", __name__)

LIST_PROJECTION = {
    "name": 1,
    "price": 1,
    "original_price": 1,
    "category": 1,
    "seller_id": 1,
    "seller_name": 1,
    "image_url": 1,
    "image_urls": 1,
    "icon": 1,
    "impressions": 1,
    "clicks": 1,
    "fair_score": 1,
    "final_score": 1,
    "score_components": 1,
    "exposure_bucket": 1,
    "on_sale": 1,
    "discount_label": 1,
    "rating": 1,
    "reviews_count": 1,
    "approved": 1,
    "status": 1,
    "fraud_flag": 1,
    "tags": 1,
    "created_at": 1,
    "discount": 1,
    "score_version": 1,
}

SEARCH_PROJECTION = {
    **LIST_PROJECTION,
    "description": 1,
    "seo_keywords": 1,
    "hidden_seo_keywords": 1,
}

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_UPLOAD_IMAGES = 5
MAX_FAIR_RANK_CANDIDATES = 2000


def _now_ts():
    return int(time.time())


def _to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_keywords(value):
    if value is None:
        return []
    if isinstance(value, str):
        value = value.replace(";", ",")
        parts = value.split(",")
    elif isinstance(value, (list, tuple, set)):
        parts = value
    else:
        parts = [value]

    keywords = []
    seen = set()
    for item in parts:
        text = str(item).strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        keywords.append(text)
    return keywords[:20]


def _normalize_image_urls(data):
    raw_urls = data.get("image_urls") or []
    if isinstance(raw_urls, str):
        try:
            parsed = json.loads(raw_urls)
            raw_urls = parsed if isinstance(parsed, list) else [raw_urls]
        except Exception:
            raw_urls = [raw_urls]

    urls = []
    for url in raw_urls:
        text = str(url).strip()
        if text and text not in urls:
            urls.append(text)

    legacy_url = str(data.get("image_url") or data.get("image") or "").strip()
    if legacy_url and legacy_url not in urls:
        urls.insert(0, legacy_url)

    return urls[:MAX_UPLOAD_IMAGES]


def _serialize_product(product, include_private=False):
    product = dict(product)
    product["_id"] = str(product["_id"])
    image_urls = _normalize_image_urls(product)
    product["image_urls"] = image_urls
    product["image_url"] = product.get("image_url") or (image_urls[0] if image_urls else "")

    if not include_private:
        product.pop("seo_keywords", None)
        product.pop("hidden_seo_keywords", None)

    return product


def _allowed_image(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def _created_sort_value(product):
    value = product.get("created_at", 0)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
            except ValueError:
                return 0
    return 0


def _seller_key(product):
    return str(product.get("seller_id") or product.get("seller_name") or "unknown").lower()


def _score_sort_value(product):
    try:
        return float(product.get("final_score", 0) or 0)
    except (TypeError, ValueError):
        return 0


def _fair_exposure_reason(product):
    bucket = product.get("exposure_bucket")
    impressions = _to_int(product.get("impressions", 0), 0)
    if bucket == "new" or impressions == 0:
        return "New product discovery boost"
    if bucket == "low_exposure" or impressions < 25:
        return "Low-view product discovery boost"
    if bucket == "growing" or impressions < 100:
        return "Growing product balanced with engagement"
    return "Established product ranked by engagement and quality"


def _fair_rank_products(products):
    """
    Re-rank already relevant products so one seller cannot crowd the page.
    The base final_score still matters, but repeated sellers receive a small
    page-level penalty and underexposed products get a small tie-break boost.
    """
    remaining = list(products)
    remaining.sort(key=lambda p: (_score_sort_value(p), _created_sort_value(p)), reverse=True)

    ranked = []
    seller_counts = {}
    last_seller = None

    while remaining:
        best_index = 0
        best_value = float("-inf")

        for index, product in enumerate(remaining):
            seller = _seller_key(product)
            seller_count = seller_counts.get(seller, 0)
            fair_score = float(product.get("fair_score", 0) or 0)
            base_score = _score_sort_value(product)

            diversity_penalty = min(0.30, seller_count * 0.075)
            consecutive_penalty = 0.12 if seller == last_seller else 0
            low_exposure_bonus = min(0.08, fair_score * 0.08)
            recency_bonus = min(0.03, _created_sort_value(product) / max(time.time(), 1) * 0.03)

            adjusted = base_score + low_exposure_bonus + recency_bonus - diversity_penalty - consecutive_penalty
            if adjusted > best_value:
                best_value = adjusted
                best_index = index

        selected = remaining.pop(best_index)
        seller = _seller_key(selected)
        selected["fair_exposure_reason"] = _fair_exposure_reason(selected)
        selected["seller_page_position"] = seller_counts.get(seller, 0) + 1
        ranked.append(selected)
        seller_counts[seller] = seller_counts.get(seller, 0) + 1
        last_seller = seller

    return ranked


def _candidate_limit(page, limit):
    return min(MAX_FAIR_RANK_CANDIDATES, max(120, (page * limit) + (limit * 3)))


def _score_and_public(product):
    if product_scores_outdated(product):
        product = apply_score_fields(product)
    product["fair_exposure_reason"] = _fair_exposure_reason(product)
    return _serialize_product(product)


@product_bp.route("/upload-images", methods=["POST"])
@seller_required
def upload_images():
    """Persist seller product images locally and return public URLs."""
    files = request.files.getlist("images") or request.files.getlist("image")
    if not files:
        return jsonify({"message": "No images uploaded"}), 400

    upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads", "products"))
    os.makedirs(upload_dir, exist_ok=True)

    image_urls = []
    skipped = []
    for file in files[:MAX_UPLOAD_IMAGES]:
        original_name = secure_filename(file.filename or "")
        if not original_name or not _allowed_image(original_name):
            skipped.append(file.filename or "unnamed")
            continue

        ext = original_name.rsplit(".", 1)[1].lower()
        stored_name = f"{uuid.uuid4().hex}.{ext}"
        file.save(os.path.join(upload_dir, stored_name))
        image_urls.append(f"{request.host_url.rstrip('/')}/uploads/products/{stored_name}")

    if not image_urls:
        return jsonify({"message": "No valid image files uploaded", "skipped": skipped}), 400

    return jsonify({
        "image_url": image_urls[0],
        "image_urls": image_urls,
        "skipped": skipped,
    }), 201


@product_bp.route("/add-product", methods=["POST"])
@seller_required
def add_product():
    data = request.json or {}
    if not data.get("name") or not data.get("price"):
        return jsonify({"message": "Missing required fields"}), 400

    current_user = get_current_user()
    if not current_user:
        return jsonify({"message": "Authentication required"}), 401
    if current_user.get("verified") is False:
        return jsonify({"message": "Seller account must be approved before adding products"}), 403

    seller_id = str(data.get("seller_id") or "").strip()
    if not seller_id:
        return jsonify({"message": "Seller ID is required"}), 400
    if seller_id != current_user.get("email"):
        return jsonify({"message": "Seller ID does not match the authenticated seller"}), 403

    seller = users_collection.find_one({"email": seller_id})
    if seller and seller.get("role") != "seller":
        return jsonify({"message": "Only seller accounts can add products"}), 403

    try:
        price = float(data.get("price"))
    except (TypeError, ValueError):
        return jsonify({"message": "Price must be a valid number"}), 400

    image_urls = _normalize_image_urls(data)
    seo_keywords = _normalize_keywords(
        data.get("seo_keywords")
        or data.get("hidden_seo_keywords")
        or data.get("keywords")
        or data.get("tags")
    )
    visible_tags = _normalize_keywords(data.get("tags") or seo_keywords)
    seller_name = data.get("seller_name") or (
        seller.get("shop_name") or seller.get("name") if seller else seller_id.split("@")[0]
    )
    now = _now_ts()

    product = {
        "name": str(data.get("name")).strip(),
        "price": price,
        "category": data.get("category", "General"),
        "description": data.get("description", ""),
        "seller_id": seller_id,
        "seller_name": seller_name,
        "icon": data.get("icon", "\U0001f4e6"),
        "image_url": image_urls[0] if image_urls else "",
        "image_urls": image_urls,
        "video_url": data.get("video_url", ""),
        "seo_keywords": seo_keywords,
        "hidden_seo_keywords": seo_keywords,
        "impressions": _to_int(data.get("impressions", 0)),
        "clicks": _to_int(data.get("clicks", 0)),
        "approved": True,
        "status": "approved",
        "fraud_flag": bool(data.get("fraud_flag", False)),
        "tags": visible_tags,
        "discount": _to_int(data.get("discount", 0)),
        "stock": _to_int(data.get("stock", 10)),
        "created_at": now,
        "updated_at": now,
    }
    product = apply_score_fields(product)

    result = products_collection.insert_one(product)
    product["_id"] = result.inserted_id
    log_activity("PRODUCT_ADD", f"New product listed: {product['name']}", product["seller_id"])
    cache.clear()

    return jsonify({"message": "Product added successfully", "product": _serialize_product(product)}), 201


@product_bp.route("/update-product", methods=["PUT"])
@seller_required
def update_product():
    """Update product details (price, stock, etc.) - for sellers."""
    data = request.json or {}
    product_id = data.get("id")
    seller_id = data.get("seller_id")

    if not product_id or not seller_id:
        return jsonify({"message": "Product ID and seller ID required"}), 400

    try:
        product = products_collection.find_one({"_id": ObjectId(product_id)})
    except Exception:
        return jsonify({"message": "Invalid Product ID"}), 400

    if not product:
        return jsonify({"message": "Product not found"}), 404

    current_user = get_current_user()
    if not current_user:
        return jsonify({"message": "Authentication required"}), 401

    if seller_id != current_user.get("email"):
        return jsonify({"message": "Seller ID does not match the authenticated seller"}), 403

    if product.get("seller_id") != current_user.get("email"):
        return jsonify({"message": "Unauthorized: You can only update your own products"}), 403

    update_fields = {}
    allowed_fields = [
        "name",
        "price",
        "category",
        "description",
        "stock",
        "discount",
        "image_url",
        "image_urls",
        "video_url",
        "tags",
        "seo_keywords",
        "hidden_seo_keywords",
    ]

    for field in allowed_fields:
        if field in data:
            update_fields[field] = data[field]

    if "image_url" in update_fields or "image_urls" in update_fields:
        image_urls = _normalize_image_urls({**product, **data})
        update_fields["image_urls"] = image_urls
        update_fields["image_url"] = image_urls[0] if image_urls else ""

    if "seo_keywords" in update_fields or "hidden_seo_keywords" in update_fields:
        keywords = _normalize_keywords(data.get("seo_keywords") or data.get("hidden_seo_keywords"))
        update_fields["seo_keywords"] = keywords
        update_fields["hidden_seo_keywords"] = keywords
        update_fields["tags"] = _normalize_keywords(data.get("tags") or keywords)

    if "tags" in update_fields:
        update_fields["tags"] = _normalize_keywords(update_fields["tags"])

    if "price" in update_fields:
        try:
            update_fields["price"] = float(update_fields["price"])
        except (TypeError, ValueError):
            return jsonify({"message": "Price must be a valid number"}), 400

    if "stock" in update_fields:
        update_fields["stock"] = _to_int(update_fields["stock"], product.get("stock", 10))
    if "discount" in update_fields:
        update_fields["discount"] = _to_int(update_fields["discount"], product.get("discount", 0))

    if not update_fields:
        return jsonify({"message": "No valid fields to update"}), 400

    update_fields["updated_at"] = _now_ts()
    update_fields.update(score_fields_for_product({**product, **update_fields}))

    result = products_collection.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": update_fields},
    )

    if result.modified_count > 0:
        log_activity("PRODUCT_UPDATE", f"Product updated: {product.get('name')}", seller_id)
        invalidate_product_cache()
        cache.delete(f"ml:score:{product_id}")
        return jsonify({"message": "Product updated successfully"}), 200

    return jsonify({"message": "No changes made"}), 200


@product_bp.route("/by-category", methods=["GET"])
def get_by_category():
    """Fetch similar products by category, excluding a specific product id."""
    category = request.args.get("category")
    exclude_id = request.args.get("exclude")
    limit = min(_to_int(request.args.get("limit", 6), 6), 24)

    filters = {}
    if category:
        filters["category"] = category
    if exclude_id:
        try:
            filters["_id"] = {"$ne": ObjectId(exclude_id)}
        except Exception:
            pass
    query = approved_product_query(filters)

    raw_products = list(
        products_collection.find(query, LIST_PROJECTION)
        .sort([("final_score", -1), ("created_at", -1)])
        .limit(max(limit * 4, 48))
    )
    products = [_score_and_public(p) for p in raw_products]
    products = _fair_rank_products(products)[:limit]

    return jsonify({"products": products}), 200


@product_bp.route("/products", methods=["GET"])
def get_products():
    """Paginated product listing ordered by stored ranking fields."""
    page = max(1, _to_int(request.args.get("page", 1), 1))
    limit = min(_to_int(request.args.get("limit", 40), 40), 100)
    category = request.args.get("category", "")
    skip = (page - 1) * limit

    filters = {}
    if category and category != "All":
        filters["category"] = category

    query = approved_product_query(filters)
    total = products_collection.count_documents(query)
    raw_products = list(
        products_collection.find(query, SEARCH_PROJECTION)
        .sort([("final_score", -1), ("created_at", -1)])
        .limit(_candidate_limit(page, limit))
    )
    ranked_products = _fair_rank_products([_score_and_public(p) for p in raw_products])
    paginated = ranked_products[skip:skip + limit]

    return jsonify({"products": paginated, "total": total, "page": page, "limit": limit}), 200


@product_bp.route("/search", methods=["GET"])
def search_products():
    """Smart relevancy search API. Hidden SEO keywords are searchable but not returned."""
    query_str = request.args.get("q", "").strip()
    if not query_str:
        return get_products()

    candidates = list(products_collection.find(approved_product_query(), SEARCH_PROJECTION))
    for p in candidates:
        p["_id"] = str(p["_id"])
        p["image_urls"] = _normalize_image_urls(p)
        p["image_url"] = p.get("image_url") or (p["image_urls"][0] if p["image_urls"] else "")

    results = ml_service.smart_search(query_str, candidates)
    sanitized = []
    for product in results:
        if product_scores_outdated(product):
            product = apply_score_fields(product)
        sanitized.append(_serialize_product(product))
    sanitized = _fair_rank_products(sanitized)

    return jsonify({"products": sanitized, "total": len(sanitized)}), 200


@product_bp.route("/all-products", methods=["GET"])
@seller_or_admin_required
def get_all_products():
    seller_id = request.args.get("seller_id")
    current_user = get_current_user()

    if not is_admin_session() and current_user and current_user.get("role") != "admin":
        current_email = current_user.get("email")
        if seller_id and seller_id != current_email:
            return jsonify({"message": "Unauthorized: You can only view your own products"}), 403
        seller_id = current_email

    query = {"seller_id": seller_id} if seller_id else {}
    raw_products = list(products_collection.find(query))
    products = [_serialize_product(p, include_private=True) for p in raw_products]
    products.sort(key=_created_sort_value, reverse=True)

    return jsonify({"products": products}), 200


@product_bp.route("/single", methods=["GET"])
def get_single_product():
    prod_id = request.args.get("id")
    if not prod_id:
        return jsonify({"message": "Product ID required"}), 400

    try:
        product = products_collection.find_one({"_id": ObjectId(prod_id)})
        if not product:
            return jsonify({"message": "Product not found"}), 404
        if product_scores_outdated(product):
            fields = refresh_product_scores(product=product)
            if fields:
                product.update(fields)

        return jsonify({"product": _score_and_public(product)}), 200
    except Exception:
        return jsonify({"message": "Invalid Product ID"}), 400


@product_bp.route("/increment", methods=["POST"])
def increment_stat():
    data = request.json or {}
    prod_id = data.get("id")
    field = data.get("field")

    if prod_id and field in ["impressions", "clicks"]:
        try:
            oid = ObjectId(prod_id)
        except Exception:
            return jsonify({"message": "Invalid Product ID"}), 400

        products_collection.update_one({"_id": oid}, {"$inc": {field: 1}})
        refresh_product_scores(product_id=oid)
        cache.delete(f"ml:score:{prod_id}")
        invalidate_product_cache()
        return jsonify({"message": "Incremented"}), 200
    return jsonify({"message": "Invalid request"}), 400


@product_bp.route("/batch-impression", methods=["POST"])
def batch_impression():
    """Batch update impressions for multiple products."""
    data = request.json or {}
    product_ids = data.get("product_ids", [])

    if not product_ids:
        return jsonify({"message": "No product IDs provided"}), 400

    BatchProcessor.batch_update_impressions(product_ids)
    refresh_product_scores_bulk(product_ids=product_ids)
    for prod_id in product_ids:
        cache.delete(f"ml:score:{prod_id}")

    invalidate_product_cache()
    return jsonify({"message": f"Batch impressions updated for {len(product_ids)} products"}), 200
