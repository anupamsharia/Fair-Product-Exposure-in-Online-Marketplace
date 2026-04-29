import os

def fraud_check(product):
    """Evaluate product for common fraud/spam patterns."""
    score = 0
    
    # Title too short
    if len(product.get("name", "")) < 5:
        score += 1
        
    # Price is zero or negative
    if float(product.get("price", 0)) <= 0:
        score += 2
        
    # Description is too thin
    if len(product.get("description", "")) < 20:
        score += 1
        
    # Missing media
    if not product.get("image_url") and not product.get("image_urls"):
        score += 2
        
    # Flag high risk
    if score >= 3:
        return "fraud", score
    
    return "safe", score

def auto_approve_logic(product):
    """Determine initial status: approved, rejected, or pending."""
    fraud_status, fraud_score = fraud_check(product)
    
    if fraud_status == "fraud":
        return "rejected", True
    
    # Check for metadata quality: keywords and detailed description
    has_keywords = len(product.get("tags", [])) >= 5
    has_description = len(product.get("description", "")) > 100
    
    # AI-optimized products with good SEO should be auto-approved
    if has_keywords and has_description:
        return "approved", False
    
    # Additional checks for product quality
    title = product.get("name", "")
    price = float(product.get("price", 0))
    
    # Check for reasonable product data
    has_valid_title = len(title) >= 10 and len(title) <= 100
    has_valid_price = 0 < price <= 10000  # Reasonable price range
    
    if has_valid_title and has_valid_price:
        # If basic checks pass but missing SEO, mark as pending for review
        return "pending", False
    
    # Default to pending if not meeting basic criteria
    return "pending", False
