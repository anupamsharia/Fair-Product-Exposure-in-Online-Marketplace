from flask import Blueprint, request, jsonify, session
from db import orders_collection, products_collection, log_activity, activity_logs_collection
from bson.objectid import ObjectId
from cache import cache
from product_queries import approved_product_query
import time

from auth import get_current_user, is_admin_session, seller_or_admin_required

order_bp = Blueprint("order", __name__)


def _serialize_order(order):
    order = dict(order)
    order["_id"] = str(order["_id"])
    return order


def _resolve_product(data):
    product_id = data.get("product_id")
    if product_id:
        try:
            product = products_collection.find_one({"_id": ObjectId(product_id)})
            if product:
                return product
        except Exception:
            pass

    product_name = data.get("product_name")
    seller_id = data.get("seller_id")
    if product_name and seller_id:
        return products_collection.find_one(approved_product_query({
            "name": product_name,
            "seller_id": seller_id,
        }))

    return None


@order_bp.route("/create-order", methods=["POST"])
def create_order():
    data = request.json or {}
    if not data.get("product_name") or not data.get("price"):
        return jsonify({"message": "Missing required fields"}), 400

    if session.get("user_role") in ["seller", "admin"]:
        return jsonify({"message": "Only customers can place orders"}), 403

    product = _resolve_product(data)
    seller_id = data.get("seller_id") or (product.get("seller_id") if product else "")
    product_id = data.get("product_id") or (str(product["_id"]) if product else "")
    image_url = data.get("image_url") or (product.get("image_url") if product else "")

    if not seller_id:
        return jsonify({"message": "Order must include a seller"}), 400

    order = {
        "product_id": product_id,
        "product_name": data.get("product_name"),
        "price": data.get("price"),
        "quantity": data.get("quantity", 1),
        "customer": data.get("customer", "Guest"),
        "customer_email": data.get("customer_email", ""),
        "seller_id": seller_id,
        "seller_name": product.get("seller_name", "") if product else data.get("seller_name", ""),
        "image_url": image_url,
        "status": "Pending",
        "date": data.get("date") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "created_at": int(time.time()),
    }

    result = orders_collection.insert_one(order)
    order["_id"] = result.inserted_id

    log_activity("ORDER_NEW", f"New order placed: {order['product_name']}", data.get("customer_email", "Guest"))
    log_activity("SELLER_ORDER", f"New order received: {order['product_name']} from {order['customer']}", seller_id)
    cache.clear()

    return jsonify({"message": "Order created successfully", "order": _serialize_order(order)}), 201


@order_bp.route("/orders", methods=["GET"])
@seller_or_admin_required
def get_orders():
    seller_id = request.args.get("seller_id")
    current_user = get_current_user()

    if not is_admin_session() and current_user and current_user.get("role") != "admin":
        current_email = current_user.get("email")
        if seller_id and seller_id != current_email:
            return jsonify({"message": "Unauthorized: You can only view your own orders"}), 403
        seller_id = current_email

    query = {"seller_id": seller_id} if seller_id else {}

    raw_orders = list(orders_collection.find(query).sort("created_at", -1))
    orders = [_serialize_order(o) for o in raw_orders]

    return jsonify({"orders": orders}), 200


@order_bp.route("/seller-notifications", methods=["GET"])
@seller_or_admin_required
def seller_notifications():
    """Get notifications for a specific seller."""
    seller_id = request.args.get("seller_id", "").strip()
    current_user = get_current_user()

    if not is_admin_session() and current_user and current_user.get("role") != "admin":
        current_email = current_user.get("email")
        if seller_id and seller_id != current_email:
            return jsonify({"message": "Unauthorized: You can only view your own notifications"}), 403
        seller_id = current_email

    if not seller_id:
        return jsonify({"message": "Seller ID is required"}), 400

    seller_activities = list(activity_logs_collection.find(
        {
            "$or": [{"user_id": seller_id}, {"user_email": seller_id}],
            "type": {"$in": ["SELLER_ORDER", "ORDER_STATUS", "PROD_APP", "PROD_REJ"]},
        }
    ).sort("timestamp", -1).limit(20))

    notifications = []
    for act in seller_activities:
        act["_id"] = str(act["_id"])
        notifications.append({
            "id": act["_id"],
            "type": act.get("type", ""),
            "message": act.get("message", ""),
            "timestamp": act.get("timestamp", ""),
            "read": act.get("read", False),
        })

    unread_count = sum(1 for n in notifications if not n.get("read", False))

    return jsonify({
        "notifications": notifications,
        "unread_count": unread_count,
        "total": len(notifications),
    }), 200


@order_bp.route("/update-status", methods=["POST"])
@seller_or_admin_required
def update_status():
    data = request.json or {}
    order_id = data.get("id")
    status = data.get("status")

    if order_id and status:
        try:
            order = orders_collection.find_one({"_id": ObjectId(order_id)})
        except Exception:
            return jsonify({"message": "Invalid Order ID"}), 400

        if not order:
            return jsonify({"message": "Order not found"}), 404

        current_user = get_current_user()
        if not is_admin_session() and current_user and current_user.get("role") != "admin":
            if order.get("seller_id") != current_user.get("email"):
                return jsonify({"message": "Unauthorized: You can only update your own orders"}), 403

        orders_collection.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {"status": status, "updated_at": int(time.time())}},
        )

        seller_id = order.get("seller_id", "")
        if seller_id:
            log_activity("ORDER_STATUS", f"Order status changed to {status}: {order.get('product_name', '')}", seller_id)

        customer_email = order.get("customer_email", "")
        if customer_email:
            log_activity("ORDER_UPDATE", f"Your order status changed to {status}: {order.get('product_name', '')}", customer_email)

        cache.clear()
        return jsonify({"message": "Order updated"}), 200
    return jsonify({"message": "Invalid request"}), 400


@order_bp.route("/my-orders", methods=["GET"])
def my_orders():
    """Return all orders for a specific customer by email."""
    email = request.args.get("email", "").strip()
    if not email:
        return jsonify({"message": "Email is required"}), 400

    raw_orders = list(orders_collection.find({"customer_email": email}).sort("created_at", -1))
    orders = [_serialize_order(o) for o in raw_orders]

    return jsonify({"orders": orders}), 200
