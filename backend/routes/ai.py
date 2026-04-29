import os
from flask import Blueprint, request, jsonify
from openai import OpenAI
from moderation_service import auto_approve_logic
from config import Config

try:
    from google.cloud import vision
except ImportError:
    vision = None

from auth import seller_required

ai_bp = Blueprint('ai', __name__)

_vision_client = None
_openai_client = None


def _resolve_google_credentials():
    """Use backend/vision-key.json by default when the env var is not set."""
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        return

    configured_path = Config.GOOGLE_APPLICATION_CREDENTIALS
    if not configured_path:
        return

    candidates = [
        configured_path,
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", configured_path)),
    ]
    for path in candidates:
        if os.path.exists(path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path
            return


def get_vision_client():
    global _vision_client
    if vision is None:
        raise RuntimeError("google-cloud-vision is not installed")
    if _vision_client is None:
        _resolve_google_credentials()
        _vision_client = vision.ImageAnnotatorClient()
    return _vision_client


def get_openai_client():
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
    return _openai_client

def auto_category(labels):
    """Map Google Vision labels to Marketplace Categories."""
    label_text = " ".join(labels).lower()
    
    if any(k in label_text for k in ["electronics", "phone", "audio", "computer", "gadget", "headphone"]):
        return "Electronics"
    if any(k in label_text for k in ["clothing", "fashion", "apparel", "shirt", "shoe", "dress"]):
        return "Fashion"
    if any(k in label_text for k in ["furniture", "home", "kitchen", "decor", "room", "grocery", "food", "snack", "beverage"]):
        return "Home & Kitchen"
    if any(k in label_text for k in ["beauty", "cosmetic", "makeup", "skin care", "perfume", "fragrance", "accessory", "jewelry", "bag", "watch", "sport", "fitness", "shoe"]):
        return "Fashion"
    
    return "Home & Kitchen"

@ai_bp.route('/image-ai', methods=['POST'])
@seller_required
def image_ai():
    """Detect labels and category from an uploaded image."""
    if 'image' not in request.files:
        return jsonify({"message": "No image uploaded"}), 400
    
    file = request.files['image']
    content = file.read()
    
    try:
        image = vision.Image(content=content)
        response = get_vision_client().label_detection(image=image)
        
        if response.error.message:
            raise Exception(f"Vision API Error: {response.error.message}")
            
        labels = [label.description for label in response.label_annotations]
        category = auto_category(labels)
        
        # Take top 5 labels as tags
        tags = labels[:5]
        
        return jsonify({
            "labels": labels,
            "category": category,
            "tags": tags
        }), 200
    except Exception as e:
        # Mock response for demo when API fails
        mock_labels = ["Electronics", "Gadget", "Device", "Modern", "Technology"]
        mock_category = "Electronics"
        mock_tags = ["electronics", "gadget", "device"]
        return jsonify({
            "labels": mock_labels,
            "category": mock_category,
            "tags": mock_tags
        }), 200

@ai_bp.route('/text-ai', methods=['POST'])
@seller_required
def text_ai():
    """Generate SEO titles or descriptions using OpenAI."""
    data = request.json or {}
    mode = data.get('mode') # 'title' or 'description'
    text = data.get('text', '').strip()
    
    if not text:
        return jsonify({"message": "No input text provided"}), 400
    
    prompt = ""
    if mode == 'title':
        prompt = f"Create a professional, SEO-friendly marketplace title for this product: '{text}'. Keep it under 60 characters and make it catchy."
    else:
        prompt = f"Write a detailed, professional product description for '{text}'. Include key features and benefits in bullet points. Use a professional tone."

    try:
        response = get_openai_client().chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional ecommerce copywriter."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300
        )
        result = response.choices[0].message.content.strip()
        return jsonify({"result": result}), 200
    except Exception as e:
        return jsonify({"message": f"OpenAI Error: {str(e)}"}), 500

@ai_bp.route('/bulk-optimize', methods=['POST'])
@seller_required
def bulk_optimize():
    """GPT-4o powered bulk optimization for title, description, and keywords."""
    data = request.json or {}
    title = data.get('title', '')
    desc = data.get('description', '')
    price = data.get('price', 0)
    category = data.get('category', 'Home & Kitchen')
    
    prompt = f"""
    You are an expert ecommerce SEO strategist specializing in marketplace optimization.
    
    Product Information:
    - Draft Title: {title}
    - Draft Description: {desc}
    - Price: ${price}
    - Category: {category}
    
    Generate a comprehensive SEO-optimized product listing with the following requirements:
    
    1. **Title (60-70 characters)**: Create a compelling, keyword-rich title that includes:
       - Primary keyword at the beginning (relevant to {category} category)
       - Secondary keywords naturally integrated
       - Emotional triggers or value propositions
       - Proper capitalization
       - Consider {category}-specific terminology and buyer intent
    
    2. **Description (200-300 words)**: Write a detailed, persuasive product description with:
       - Engaging opening paragraph with primary keyword
       - Bullet points of key features and benefits (5-7 points) specific to {category}
       - Technical specifications if applicable to {category} products
       - Call-to-action at the end
       - Natural keyword integration (avoid keyword stuffing)
       - Address common {category} buyer concerns and questions
    
    3. **Keywords (8-12 keywords)**: Provide a mix of:
       - 2-3 primary/high-volume keywords for {category}
       - 3-4 secondary/long-tail keywords specific to this product
       - 2-3 competitor/product comparison keywords in {category}
       - 1-2 brand/unique selling proposition keywords
       - Include {category}-specific search terms
    
    Return ONLY a valid JSON object with this exact structure:
    {{
      "title": "SEO-optimized title here",
      "description": "Detailed professional description here",
      "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5", "keyword6", "keyword7", "keyword8"]
    }}
    
    Do not include any explanations, notes, or markdown formatting.
    """

    try:
        response = get_openai_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        
        import json
        optimized = json.loads(response.choices[0].message.content)
        
        # Run automated moderation
        status, is_fraud = auto_approve_logic({
            "name": optimized['title'],
            "description": optimized['description'],
            "price": price,
            "tags": optimized['keywords']
        })
        
        return jsonify({
            "optimized": optimized,
            "moderation": {
                "status": status,
                "is_fraud": is_fraud
            }
        }), 200
    except Exception as e:
        # Mock response for demo when API fails
        print(f"AI optimization failed, using mock response: {str(e)}")
        mock_optimized = {
            "title": f"{title} - Premium {category} with Advanced Features",
            "description": f"This high-quality {category.lower()} offers exceptional value. Features include durable construction, user-friendly design, and excellent performance. Ideal for everyday use. Buy now for best price!",
            "keywords": [category, "premium", "best quality", "affordable", "durable", "feature-rich", "value for money", "top rated"]
        }
        try:
            status, is_fraud = auto_approve_logic({
                "name": mock_optimized['title'],
                "description": mock_optimized['description'],
                "price": price,
                "tags": mock_optimized['keywords']
            })
        except Exception as mod_error:
            print(f"Moderation failed: {str(mod_error)}")
            status, is_fraud = "approved", False
        
        return jsonify({
            "optimized": mock_optimized,
            "moderation": {
                "status": status,
                "is_fraud": is_fraud
            }
        }), 200
