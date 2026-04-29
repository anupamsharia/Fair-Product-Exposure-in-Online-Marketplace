def approved_product_query(extra=None):
    """Match approved products from both current and legacy seed schemas."""
    base = {
        "$or": [
            {"status": "approved"},
            {"approved": True, "status": {"$exists": False}},
            {"approved": True, "status": None},
            {"approved": True, "status": ""},
        ]
    }
    if not extra:
        return base
    return {"$and": [base, extra]}
