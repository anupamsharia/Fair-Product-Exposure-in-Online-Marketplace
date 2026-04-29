"""
FairCart – Fair Exposure Marketplace
Realistic Dataset Generator
Outputs: sellers.json, products.json, customers.json, orders.json
"""
import json, random, uuid, os, sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
from datetime import datetime, timedelta

TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from path_helper import backend_path

OUTPUT_DIR = backend_path("seed_data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

random.seed(42)

# ─── HELPERS ───────────────────────────────────────────────────────────────────
def uid(): return str(uuid.uuid4())
def rand_date(days_back=365):
    return (datetime.utcnow() - timedelta(days=random.randint(0, days_back))).isoformat() + "Z"


# ────────────────────────────────────────────────────────────────────────────────
# 1. SELLERS
# ────────────────────────────────────────────────────────────────────────────────
SELLER_DATA = {
    "Fashion": [
        ("Amit Joshi",      "amit.joshi@threadcraft.in",   "ThreadCraft Studio"),
        ("Priya Mehta",     "priya.mehta@velvetlane.in",   "Velvet Lane"),
        ("Rohan Kapoor",    "rohan.kapoor@urbanweave.in",  "Urban Weave"),
        ("Sneha Reddy",     "sneha.reddy@ethnicbazaar.in", "Ethnic Bazaar"),
        ("Vikram Singh",    "vikram.singh@boldlooks.in",   "Bold Looks"),
    ],
    "Home & Kitchen": [
        ("Kavitha Nair",    "kavitha.nair@nestify.in",     "Nestify Home"),
        ("Suresh Iyer",     "suresh.iyer@cookcraft.in",    "CookCraft"),
        ("Deepa Pillai",    "deepa.pillai@homeglow.in",    "HomeGlow"),
        ("Rajesh Sharma",   "rajesh.sharma@kitchenpro.in", "Kitchen Pro India"),
        ("Anita Verma",     "anita.verma@decornest.in",    "Décor Nest"),
    ],
    "Accessories": [
        ("Meera Patel",     "meera.patel@glimcraft.in",    "GlimCraft"),
        ("Arjun Bansal",    "arjun.bansal@wristhaus.in",   "WristHaus"),
        ("Pooja Desai",     "pooja.desai@bagtales.in",     "BagTales"),
        ("Nikhil Gupta",    "nikhil.gupta@solemate.in",    "SoleMate"),
        ("Rekha Bose",      "rekha.bose@glamloop.in",      "GlamLoop"),
    ],
    "Electronics": [
        ("Kiran Rao",       "kiran.rao@techpulse.in",      "TechPulse"),
        ("Sanjay Mishra",   "sanjay.mishra@gadzoid.in",    "Gadzoid"),
        ("Lavanya Kumar",   "lavanya.kumar@voltedge.in",   "VoltEdge"),
        ("Arun Tiwari",     "arun.tiwari@pixelmart.in",    "PixelMart"),
        ("Harsha Reddy",    "harsha.reddy@circuitbay.in",  "CircuitBay"),
    ],
}

sellers = []
seller_by_cat = {}
for cat, entries in SELLER_DATA.items():
    cat_sellers = []
    for (name, email, shop) in entries:
        s = {
            "_id": uid(),
            "name": name,
            "email": email,
            "password": "hashed_placeholder",
            "role": "seller",
            "shop_name": shop,
            "category": cat,
            "joined": rand_date(730),
            "rating": round(random.uniform(3.5, 5.0), 1),
            "total_sales": random.randint(50, 2000),
        }
        sellers.append(s)
        cat_sellers.append(s)
    seller_by_cat[cat] = cat_sellers

print(f"[OK] Generated {len(sellers)} sellers")


# ────────────────────────────────────────────────────────────────────────────────
# 2. PRODUCTS (10–15 per seller ≈ 200–300 total)
# ────────────────────────────────────────────────────────────────────────────────

# Unsplash curated images per category (varied, no placeholders)
IMAGES = {
    "Fashion": [
        "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=600",
        "https://images.unsplash.com/photo-1542272604-787c3835535d?w=600",
        "https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?w=600",
        "https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=600",
        "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=600",
        "https://images.unsplash.com/photo-1529374255404-311a2a4f1fd9?w=600",
        "https://images.unsplash.com/photo-1560769629-975ec94e6a86?w=600",
        "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=600",
        "https://images.unsplash.com/photo-1551232864-3f0890e580d9?w=600",
        "https://images.unsplash.com/photo-1485462537746-965f33f7f6a7?w=600",
        "https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=600",
        "https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=600",
        "https://images.unsplash.com/photo-1562157873-818bc0726f68?w=600",
        "https://images.unsplash.com/photo-1543087903-1ac2364bde93?w=600",
        "https://images.unsplash.com/photo-1525507119028-ed4c629a60a3?w=600",
    ],
    "Home & Kitchen": [
        "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=600",
        "https://images.unsplash.com/photo-1585515320310-259814833e62?w=600",
        "https://images.unsplash.com/photo-1565538810643-b5bdb714032a?w=600",
        "https://images.unsplash.com/photo-1574269909862-7e1d70bb8078?w=600",
        "https://images.unsplash.com/photo-1538688525198-9b88f6f53126?w=600",
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600",
        "https://images.unsplash.com/photo-1616627451515-cbc80e5eca6a?w=600",
        "https://images.unsplash.com/photo-1581578021450-fbd19fad6e8a?w=600",
        "https://images.unsplash.com/photo-1556911220-bff31c812dba?w=600",
        "https://images.unsplash.com/photo-1600566753190-17f0bc4ecc5b?w=600",
        "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=600",
        "https://images.unsplash.com/photo-1484154218962-a197022b5858?w=600",
        "https://images.unsplash.com/photo-1583847268964-b28dc8f51f92?w=600",
        "https://images.unsplash.com/photo-1571175443880-49e1d25b2bc5?w=600",
        "https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?w=600",
    ],
    "Accessories": [
        "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600",
        "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600",
        "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=600",
        "https://images.unsplash.com/photo-1537832816519-689ad163238b?w=600",
        "https://images.unsplash.com/photo-1606760227091-3dd870d97f1d?w=600",
        "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=600",
        "https://images.unsplash.com/photo-1611085583191-a3b181a88401?w=600",
        "https://images.unsplash.com/photo-1590874103328-eac38a683ce7?w=600",
        "https://images.unsplash.com/photo-1491553895911-0055eca6402d?w=600",
        "https://images.unsplash.com/photo-1627123424574-724758594e93?w=600",
        "https://images.unsplash.com/photo-1586495777744-4e6232bf7074?w=600",
        "https://images.unsplash.com/photo-1516762689617-e1cffcef479d?w=600",
        "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=600",
        "https://images.unsplash.com/photo-1612423284934-2850a4ea6b0f?w=600",
        "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=600",
    ],
    "Electronics": [
        "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600",
        "https://images.unsplash.com/photo-1484704849700-f032a568e944?w=600",
        "https://images.unsplash.com/photo-1585386959984-a4155224a1ad?w=600",
        "https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=600",
        "https://images.unsplash.com/photo-1593642632559-0c6d3fc62b89?w=600",
        "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=600",
        "https://images.unsplash.com/photo-1583394838336-acd977736f90?w=600",
        "https://images.unsplash.com/photo-1524678714210-9917a6c619c2?w=600",
        "https://images.unsplash.com/photo-1563770660941-20978e870e26?w=600",
        "https://images.unsplash.com/photo-1550009158-9ebf69173e03?w=600",
        "https://images.unsplash.com/photo-1601784551446-20c9e07cdbdb?w=600",
        "https://images.unsplash.com/photo-1615655096345-61a53e899ab2?w=600",
        "https://images.unsplash.com/photo-1598986646512-9330bcc4c0dc?w=600",
        "https://images.unsplash.com/photo-1596566263687-ff31c812dba?w=600",
        "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=600",
    ],
}

PRODUCT_TEMPLATES = {
    "Fashion": [
        ("Men's Slim Fit Cotton Shirt", 499, 1299, ["cotton shirt", "slim fit", "men's shirt", "casual wear", "formal shirt", "breathable fabric", "office wear"],
         "A premium slim-fit cotton shirt crafted for the modern man. Featuring a tailored cut that flatters the body, this shirt is made from 100% breathable cotton fabric that keeps you cool throughout the day. Perfect for office meetings, casual outings, or semi-formal events. Available in multiple colours, the reinforced stitching ensures long-lasting durability. Easy to wash and iron, it retains its shape after repeated use. The button-down collar adds a polished touch, while the curved hem allows for both tucked and untucked styling."),
        ("Women's Floral Kurti", 399, 999, ["kurti", "women's wear", "floral print", "ethnic wear", "cotton kurti", "casual kurti", "summer wear"],
         "Celebrate your ethnic roots with this vibrant floral-print kurti. Crafted from soft, breathable fabric, it features an elegant all-over floral pattern that transitions seamlessly from day to night. The A-line silhouette is universally flattering, while the round neckline and three-quarter sleeves add a classic touch. Machine washable and colour-fast, this kurti pairs beautifully with churidar, leggings, or jeans."),
        ("Men's Slim Fit Denims", 799, 1799, ["denim jeans", "slim fit", "men's jeans", "blue jeans", "casual wear", "stretch fabric", "everyday wear"],
         "Redefine your casual wardrobe with these premium slim-fit denims. Made from a cotton-elastane blend, they offer the perfect balance of structure and stretch. The five-pocket design is as functional as it is stylish, and the fade-resistant dye ensures the colour stays vivid wash after wash. Whether you're heading to a weekend brunch or a casual office environment, these jeans deliver all-day comfort without compromising on style."),
        ("Women's Embroidered Salwar Suit", 1299, 2999, ["salwar suit", "embroidered", "ethnic wear", "women's suit", "festive wear", "Indian wear", "dupatta set"],
         "Make a stunning impression at every occasion with this hand-embroidered salwar suit set. The intricate threadwork on the kurta is complemented by a matching churidar and dupatta, creating an effortlessly cohesive look. Crafted from premium cotton-silk fabric, the ensemble is both comfortable and elegant. Ideal for festive occasions, family gatherings, or ceremonies, this suit set is a wardrobe staple for every Indian woman."),
        ("Men's Cotton Kurta Pyjama Set", 899, 1999, ["kurta pyjama", "cotton kurta", "men's ethnic wear", "traditional wear", "festive kurta", "block print", "casual kurta"],
         "Step into tradition with this beautifully crafted cotton kurta pyjama set. The straight-fit kurta features subtle block-print detailing along the collar and cuffs, making it apt for festive and formal occasions alike. Paired with a comfortable pyjama, the set ensures you look impeccable while feeling relaxed. The pure cotton fabric is soft against the skin and perfect for warm Indian climates."),
        ("Women's Wrap-Around Midi Skirt", 599, 1499, ["wrap skirt", "midi skirt", "women's skirt", "casual wear", "floral skirt", "boho style", "summer fashion"],
         "Effortlessly chic and endlessly versatile, this wrap-around midi skirt is a must-have for every woman's wardrobe. The adjustable wrap-front design ensures a perfect fit across sizes, while the lightweight fabric flows beautifully with every movement. Featuring a bold botanical print, it pairs perfectly with a simple cotton top or a structured blouse. Ideal for brunches, beach days, or casual evenings out."),
        ("Men's Formal Blazer", 2499, 5999, ["blazer", "formal blazer", "men's jacket", "office wear", "suit jacket", "wedding wear", "slim fit blazer"],
         "Command every room you walk into with this sharp, slim-fit formal blazer. Constructed from premium polyester-viscose blend fabric, this blazer drapes impeccably and retains its structure throughout the day. The single-button closure, notch lapel, and two flap pockets lend it a timeless silhouette. Suitable for job interviews, formal dinners, or festive occasions. Pair with tailored trousers for a boardroom-ready look."),
        ("Women's Anarkali Gown", 1599, 3499, ["anarkali gown", "women's gown", "ethnic gown", "party wear", "festive gown", "Indian gown", "flared gown"],
         "Turn heads at every celebration in this flowing anarkali gown. The heavily embellished yoke transitions into a graceful flared skirt, creating a dramatic silhouette that is both royal and contemporary. Made from high-quality georgette fabric, it is cool to wear and easy to move in. The gown comes with a matching dupatta and is ideal for weddings, engagement ceremonies, and festive events."),
        ("Unisex Printed Hoodie", 899, 1799, ["hoodie", "printed hoodie", "unisex hoodie", "winter wear", "casual hoodie", "sweatshirt", "streetwear"],
         "Stay warm and stylish with this versatile unisex hoodie. Crafted from a thick cotton-fleece blend, it offers superior insulation during cool evenings and winter months. The bold graphic print on the front adds a contemporary streetwear edge, while the adjustable drawstring hood and kangaroo pocket provide practical functionality. Machine washable and available in a wide size range, this hoodie is a winter wardrobe essential."),
        ("Women's High-Waist Yoga Pants", 699, 1599, ["yoga pants", "high waist", "women's leggings", "gym wear", "workout pants", "stretch fabric", "activewear"],
         "Elevate your fitness game with these high-waist yoga pants. Engineered from a four-way stretch fabric, they move with your body whether you're in a downward dog or a sprint. The wide waistband stays in place without digging in, and the moisture-wicking technology keeps you dry during intense workouts. The squat-proof material ensures full coverage, while the sleek design transitions effortlessly from the gym to the cafe."),
        ("Men's Cargo Shorts", 599, 1299, ["cargo shorts", "men's shorts", "casual shorts", "multi-pocket shorts", "summer wear", "outdoor wear", "cotton shorts"],
         "Built for adventure and everyday hustle alike, these men's cargo shorts combine practicality with style. Featuring six deep pockets — two side, two back, and two cargo — they offer ample storage for your essentials. The durable twill fabric is reinforced at the seams for extra longevity, while the adjustable waistband ensures a comfortable fit. Available in classic earthy tones that pair well with any casual top."),
        ("Women's Georgette Saree", 1999, 4999, ["saree", "georgette saree", "women's saree", "party wear saree", "embroidered saree", "Indian fashion", "designer saree"],
         "Drape yourself in elegance with this exquisite georgette saree. The lightweight, fluid fabric makes it easy to drape and comfortable to wear all day. The rich embroidered borders and pallu add a touch of opulence, making it perfect for weddings, festive occasions, or formal events. Includes an unstitched blouse piece so you can customise the fit to perfection."),
        ("Kids' Dungaree Set", 499, 999, ["kids dungaree", "children's wear", "dungaree set", "casual kids wear", "toddler wear", "cotton dungaree", "playsuit"],
         "Dress your little one in this adorable and practical dungaree set. Made from 100% soft cotton, it's gentle on sensitive skin and allows for full range of movement during play. The adjustable straps ensure a growing fit, while the front bib pocket adds a cute detail. Pair with a colourful t-shirt inside for a complete look. Easy to put on and take off, thanks to the snap buttons at the crotch."),
        ("Men's Leather Belt", 399, 899, ["leather belt", "men's belt", "formal belt", "casual belt", "genuine leather", "accessories", "waist belt"],
         "A wardrobe staple, this genuine leather belt is designed to last a lifetime. The full-grain leather strap is supple yet sturdy, and the polished metal buckle adds a sleek finishing touch. Available in black and tan, this belt pairs perfectly with formal trousers or casual denims. The single-prong buckle design makes it easy to adjust on the go. Width: 35mm. Sizes available from 28 to 44 inches."),
        ("Women's Palazzo Pants", 699, 1499, ["palazzo pants", "women's pants", "wide-leg pants", "ethnic wear", "casual pants", "summer fashion", "flowy pants"],
         "Experience ultimate comfort and style with these flowy palazzo pants. Cut from lightweight, breathable fabric, they feature a wide-leg silhouette that moves beautifully with every step. The elasticated waistband ensures a comfortable fit for all body types. Available in bold and subtle prints, these pants pair effortlessly with fitted crop tops, kurtis, or simple tees. A perfect choice for vacations, casual outings, or home wear."),
    ],
    "Home & Kitchen": [
        ("Non-Stick Frying Pan 28cm", 799, 1999, ["non-stick pan", "frying pan", "cooking pan", "28cm pan", "kitchen cookware", "induction compatible", "PFOA-free"],
         "Cook with confidence using this premium non-stick frying pan. The three-layer PFOA-free non-stick coating ensures food releases effortlessly, making cooking and cleaning a breeze. Compatible with all hob types including induction, the heavy-gauge aluminium base ensures even heat distribution, eliminating hot spots. The ergonomic, heat-resistant handle provides a secure and comfortable grip. Perfect for eggs, pancakes, vegetables, and more. Oven-safe up to 180°C."),
        ("Stainless Steel Pressure Cooker 5L", 1299, 2999, ["pressure cooker", "stainless steel pressure cooker", "5 litre cooker", "kitchen appliance", "cooking pot", "ISI marked", "induction cooker"],
         "Cook meals in a fraction of the time with this durable 5-litre stainless steel pressure cooker. Constructed from food-grade 304 stainless steel, it retains the natural flavours and nutrients of your food. The precision weight valve ensures consistent pressure control for safe, reliable cooking. Compatible with all heat sources including induction cooktops. Comes with two safety valves for added peace of mind. ISI marked and backed by a 5-year warranty."),
        ("Bamboo Cutting Board Set of 3", 599, 1299, ["cutting board", "bamboo board", "chopping board", "kitchen board", "eco-friendly", "knife-friendly", "food prep"],
         "Upgrade your food preparation with this eco-friendly set of three bamboo cutting boards. Available in three sizes — small, medium, and large — they cater to all your chopping needs. Bamboo is naturally antimicrobial and harder than most hardwoods, yet gentle on knife blades. Each board features juice grooves around the perimeter to catch liquids and prevent mess. Easy to clean and maintain, these boards are a sustainable and practical kitchen essential."),
        ("Ceramic Dinner Set 18 Pieces", 2499, 5999, ["dinner set", "ceramic dinner set", "crockery set", "dinner plates", "bowl set", "tableware", "dining set"],
         "Elevate your dining experience with this elegant 18-piece ceramic dinner set. Includes 6 dinner plates, 6 soup bowls, and 6 dessert plates, all featuring a classic white glaze with a subtle embossed border. Crafted from high-fired ceramic, each piece is chip-resistant and dishwasher-safe. The lead-free glaze ensures food safety, while the uniform sizing makes for an aesthetically pleasing table spread. A perfect gift for weddings, housewarmings, or anniversaries."),
        ("Electric Kettle 1.7L Stainless Steel", 999, 2499, ["electric kettle", "steel kettle", "1.7 litre kettle", "fast boiling kettle", "kitchen appliance", "BPA-free", "auto shutoff"],
         "Boil water in under 5 minutes with this powerful 1500W stainless steel electric kettle. The 1.7-litre capacity is ideal for families and office use. Features an automatic shutoff and boil-dry protection for complete safety. The 360° cordless base allows for easy pouring from any angle, while the concealed heating element prevents limescale buildup. The cool-touch exterior stays safe to handle even at full boil. BPA-free and easy to clean."),
        ("Spice Rack Organiser with 12 Jars", 799, 1799, ["spice rack", "spice organiser", "kitchen organiser", "spice jars", "masala rack", "countertop organiser", "magnetic spice rack"],
         "Keep your kitchen tidy and your spices within arm's reach with this stylish spice rack organiser. Includes 12 airtight glass jars with stainless steel lids, all neatly arranged on a rotating bamboo base. The compact lazy-susan design allows 360° access without fumbling through crowded cabinets. Labels are included for easy identification. The airtight seal preserves the freshness and potency of your spices for longer. Perfect for countertops, shelves, or inside cabinets."),
        ("Silicone Kitchen Tools Set of 5", 499, 1199, ["silicone spatula", "kitchen tools", "cooking utensils", "heat-resistant", "non-stick safe", "silicone set", "baking tools"],
         "Protect your non-stick cookware with this premium 5-piece silicone kitchen tools set. Includes a spatula, ladle, spoon, slotted turner, and pasta server — all made from food-grade silicone that is heat-resistant up to 230°C. The soft, flexible heads are gentle on non-stick surfaces, while the sturdy stainless steel handles provide a confident grip. Dishwasher safe and easy to clean, this set is a must-have for every modern kitchen."),
        ("Mixer Grinder 750W 3 Jars", 2999, 6999, ["mixer grinder", "750W mixer", "3 jar grinder", "kitchen appliance", "blender", "juicer mixer", "wet and dry grinder"],
         "Power through all your grinding, mixing, and blending tasks with this robust 750W mixer grinder. Comes with three stainless steel jars — a large liquidising jar, a medium multi-purpose jar, and a small chutney jar — each with leak-proof lids. The powerful motor handles both wet and dry ingredients with ease. Triple safety protection — thermal overload, auto-restart, and lid-locking mechanism — ensures safe operation. ISI certified and backed by 2-year motor warranty."),
        ("Wooden Wall Clock 30cm", 599, 1499, ["wall clock", "wooden clock", "home decor", "decorative clock", "living room clock", "silent sweep", "Nordic design"],
         "Add a touch of Scandinavian elegance to your home with this hand-crafted wooden wall clock. The 30cm dial features clean, minimalist numerals on a natural wood finish, complemented by sleek metal hands. The silent sweep mechanism ensures completely noise-free operation, making it perfect for bedrooms and study rooms. Requires a single AA battery (not included). Easy to hang with the pre-installed rear bracket. Available in walnut, oak, and mahogany finishes."),
        ("Soft Microfibre Sofa Cover", 899, 1999, ["sofa cover", "sofa protector", "microfibre sofa", "furniture cover", "stretchable cover", "3-seater cover", "pet-proof"],
         "Give your sofa a fresh new look with this premium microfibre sofa cover. Made from a stretchable, ultra-soft microfibre fabric, it fits most 3-seater sofas with dimensions between 180–230cm. The elastic base ensures the cover stays in place even with regular use. Waterproof and pet-hair resistant, it protects your furniture from spills, scratches, and everyday wear and tear. Machine washable and available in a range of elegant colours to match any interior."),
        ("Insulated Water Bottle 1L", 699, 1599, ["water bottle", "insulated bottle", "steel bottle", "1 litre bottle", "leak-proof bottle", "hot cold bottle", "gym bottle"],
         "Stay hydrated all day with this 1-litre double-walled vacuum-insulated water bottle. Crafted from 18/8 food-grade stainless steel, it keeps drinks cold for 24 hours and hot for 12 hours. The leak-proof lid and carry loop make it ideal for the gym, office, camping, or travel. The powder-coated exterior provides a comfortable grip and resists peeling or fading. BPA-free, eco-friendly, and a perfect alternative to single-use plastic bottles."),
        ("Non-Stick Tawa 30cm", 599, 1399, ["tawa", "non-stick tawa", "flat pan", "griddle pan", "roti tawa", "induction tawa", "dosa tawa"],
         "Make perfectly even rotis, dosas, and pancakes on this premium 30cm non-stick tawa. The PFOA-free multi-layer coating ensures food does not stick, allowing you to cook with minimal oil. Compatible with gas, electric, and induction cooktops, the heavy-gauge construction provides uniform heat distribution. The comfortable riveted handle stays cool during cooking. Easy to wipe clean after use. A kitchen staple for every Indian household."),
        ("Cotton Bedsheet Set King Size", 1299, 2999, ["bedsheet", "king size bedsheet", "cotton bedsheet", "3-piece bedsheet set", "flat sheet", "pillow covers", "1000 TC"],
         "Transform your bedroom into a luxurious retreat with this king-size cotton bedsheet set. Crafted from premium long-staple cotton with a 600 thread count, the silky-smooth fabric gets softer with every wash. The set includes one flat sheet (274x274cm) and two pillow covers. Featuring a subtle geometric pattern in soothing neutral tones, it coordinates effortlessly with any bedroom décor. Fade-resistant and machine washable for easy care."),
        ("Steel Storage Containers Set of 6", 799, 1799, ["storage containers", "steel containers", "kitchen containers", "airtight containers", "dabba set", "dry storage", "food containers"],
         "Organise your pantry in style with this set of six stainless steel storage containers. Each container comes with an airtight lid to keep ingredients fresh for longer. The set includes containers in three sizes — perfect for storing grains, pulses, snacks, and spices. The brushed-finish steel is hygienic, odour-free, and easy to clean. Stackable design maximises space efficiency. A practical and elegant addition to any modern kitchen."),
        ("Decorative Throw Pillow Set of 4", 999, 2499, ["throw pillow", "sofa cushion", "decorative pillow", "cushion cover", "home decor", "living room pillow", "velvet cushion"],
         "Inject personality into your living space with this set of four designer throw pillows. Each pillow measures 45x45cm and features a plush velvet cover in complementary tones — blush pink, sage green, terracotta, and ivory. The hidden zipper allows for easy removal and washing. Filled with premium hollow fibre that retains its shape after use. A quick and affordable way to refresh your sofa, bed, or reading nook."),
    ],
    "Accessories": [
        ("Stainless Steel Quartz Watch", 1999, 4999, ["quartz watch", "stainless steel watch", "men's watch", "analog watch", "waterproof watch", "minimalist watch", "wrist watch"],
         "Make a lasting impression with this precision-engineered stainless steel quartz watch. The Japanese quartz movement ensures accurate timekeeping with a battery life of over 3 years. The 40mm sunburst dial features luminous hands and minimalist hour markers for easy reading in any lighting condition. The solid steel case is water-resistant to 50 metres, making it suitable for everyday wear and light water activities. Secured with a stainless steel bracelet featuring a butterfly deployant clasp."),
        ("Leather Laptop Bag 15.6 inch", 1499, 3499, ["laptop bag", "leather bag", "15.6 inch bag", "office bag", "shoulder bag", "padded laptop bag", "business bag"],
         "Carry your tech in style with this premium full-grain leather laptop bag. Designed to fit laptops up to 15.6 inches, the padded interior compartment provides robust protection against bumps during your commute. Multiple organised pockets hold your charger, notebook, pens, and phone. The adjustable padded shoulder strap and top carry handle offer two versatile carrying options. Reinforced stitching and high-quality zippers ensure durability for daily use. Available in classic black and vintage brown."),
        ("Sterling Silver Pendant Necklace", 999, 2499, ["silver necklace", "pendant necklace", "sterling silver", "women's jewellery", "dainty necklace", "gift jewellery", "925 silver"],
         "Adorn yourself with the understated elegance of this 925 sterling silver pendant necklace. The delicate chain measures 45cm with a 5cm extension for a customisable fit. The pendant features a hand-polished geometric design that catches the light beautifully. Hypoallergenic and tarnish-resistant, it's suitable for sensitive skin and can be worn daily. Presented in a premium gift box, making it an ideal present for birthdays, anniversaries, or celebrations."),
        ("Canvas Tote Bag Large", 499, 1199, ["tote bag", "canvas bag", "shopping bag", "reusable bag", "large tote", "eco bag", "shoulder tote"],
         "Go green without compromising on style with this durable large canvas tote bag. Made from heavy-duty 12oz cotton canvas, it can comfortably hold up to 15kg of groceries, books, or gym essentials. The reinforced double-stitched handles ensure long-lasting strength. The roomy interior features an inner zip pocket for your valuables. A bold printed design on the front makes it a fashion statement as well as a practical everyday carry. Machine washable and eco-friendly."),
        ("Polarised Aviator Sunglasses", 799, 1999, ["sunglasses", "aviator sunglasses", "polarised glasses", "UV400 protection", "men's sunglasses", "women's sunglasses", "driving glasses"],
         "Shield your eyes in style with these classic polarised aviator sunglasses. The polarised lenses provide superior glare reduction — ideal for driving, outdoor sports, and beach days. With 100% UV400 protection, they block both UVA and UVB rays for complete eye safety. The lightweight metal frame is adjustable at the nose bridge for a personalised fit. Scratch-resistant lenses and a durable gunmetal frame ensure they stand the test of time. Comes with a hard carry case and cleaning cloth."),
        ("Beaded Charm Bracelet", 399, 999, ["charm bracelet", "beaded bracelet", "women's bracelet", "handmade bracelet", "boho jewellery", "gift bracelet", "gemstone bracelet"],
         "Celebrate your unique style with this handcrafted beaded charm bracelet. Strung with a mix of semi-precious gemstone beads — amethyst, lapis lazuli, and rose quartz — along with gold-plated charms, each bracelet is entirely one-of-a-kind. The elastic cord fits most wrist sizes and is easy to put on without a clasp. Lightweight, colourful, and versatile, it can be stacked with other bracelets for a layered look. Makes a thoughtful and unique gift."),
        ("Minimalist Leather Wallet", 699, 1799, ["leather wallet", "slim wallet", "bifold wallet", "men's wallet", "card holder", "RFID wallet", "genuine leather wallet"],
         "Streamline your everyday carry with this ultra-slim genuine leather wallet. The bifold design comfortably holds up to 8 cards and a generous cash compartment. Built-in RFID-blocking technology protects your credit and debit cards from unauthorised scanning. The full-grain leather ages beautifully with use, developing a unique patina over time. Slim enough to sit comfortably in a front pocket. A sophisticated accessory that makes a memorable gift for men."),
        ("Sports Gym Gloves", 399, 899, ["gym gloves", "workout gloves", "sports gloves", "weightlifting gloves", "grip gloves", "fitness accessories", "anti-slip gloves"],
         "Maximise your gym performance with these professional-grade sports gym gloves. The palm is reinforced with premium leather padding that absorbs impact during weightlifting and reduces callus formation. The breathable mesh back keeps your hands cool and sweat-free during intense sessions. The adjustable wrist strap provides added support and stability during heavy lifts. Available in sizes S to XL, these gloves are suitable for weightlifting, pull-ups, rowing, and general gym use."),
        ("Silk Scarf 90x90cm", 599, 1499, ["silk scarf", "women's scarf", "printed scarf", "square scarf", "neck scarf", "gift scarf", "luxury scarf"],
         "Add a splash of colour and sophistication to any outfit with this luxurious 90x90cm silk scarf. Inspired by Mughal-era art, the intricate print features rich jewel tones on an ivory background. Made from premium satin silk, the fabric is ultra-smooth and drapes elegantly. Wear it as a neck scarf, head wrap, or even tie it to your handbag for a chic accent. Hand wash gently for best care. Beautifully packaged, making it a superb gift for any occasion."),
        ("Anti-Theft Travel Backpack 30L", 1999, 4499, ["travel backpack", "anti-theft bag", "30L backpack", "USB charging backpack", "laptop backpack", "waterproof bag", "college bag"],
         "Travel smart and secure with this feature-packed 30-litre anti-theft backpack. The concealed back-zip main compartment keeps your belongings hidden from pickpockets. A dedicated padded sleeve fits laptops up to 15.6 inches, while multiple organiser pockets keep your gear tidy. The built-in USB charging port allows you to charge your devices on the move. Made from durable, water-resistant polyester, it's built for daily commuters, students, and frequent travellers alike."),
        ("Titanium Stud Earrings Set of 6", 499, 1299, ["stud earrings", "titanium earrings", "hypoallergenic earrings", "earring set", "women's earrings", "gift set", "piercing earrings"],
         "Refresh your earring collection with this elegant set of 6 titanium stud earrings. Crafted from hypoallergenic implant-grade titanium, they are safe for sensitive and newly-pierced ears. The set includes round, star, heart, moon, flower, and teardrop shapes — each with a secure butterfly backing to prevent accidental loss. The subtle gold and silver-toned finishes make them versatile for everyday wear. A thoughtful and practical gift for teenage girls and young women."),
        ("Running Cap with UV Protection", 349, 799, ["running cap", "sports cap", "UV protection cap", "sun hat", "gym cap", "moisture-wicking cap", "outdoor cap"],
         "Beat the sun on your morning runs with this lightweight UV-protection running cap. Constructed from moisture-wicking polyester, it rapidly draws sweat away from your skin, keeping you cool and dry. The UPF 50+ fabric blocks harmful ultraviolet rays to protect your face and scalp. An adjustable rear closure ensures a secure fit for all head sizes. The breathable mesh panels on the sides promote superior ventilation. Ideal for running, cycling, hiking, and golf."),
        ("Handmade Jute Tote Bag", 399, 899, ["jute bag", "handmade bag", "eco bag", "natural bag", "shopping bag", "reusable bag", "sustainable bag"],
         "Carry your essentials with conscience using this handmade jute tote bag. Woven by skilled artisans from natural jute fibres, this bag is entirely biodegradable and a sustainable alternative to plastic. The reinforced cotton lining inside prevents items from poking through, while the sturdy twin jute handles ensure comfortable carrying. A convenient zip closure on top secures your belongings. Spacious enough for groceries, books, or daily essentials. Each purchase supports rural artisans."),
        ("Ankle Strap Block Heels", 1299, 2999, ["block heels", "ankle strap heels", "women's heels", "party heels", "formal heels", "comfortable heels", "sandal heels"],
         "Step out in confidence with these elegant ankle-strap block heels. The 7cm block heel provides height without sacrificing stability, making them comfortable enough to wear all evening. The adjustable ankle strap with a gold-tone buckle ensures a secure and elegant fit. The cushioned insole reduces fatigue during prolonged wear. Crafted from faux leather with a glossy finish, these heels pair beautifully with dresses, jumpsuits, or tailored trousers. Available in black, nude, and wine red."),
        ("Fingerless Wool Gloves", 399, 899, ["fingerless gloves", "wool gloves", "winter gloves", "typing gloves", "touchscreen gloves", "knit gloves", "warm gloves"],
         "Keep your hands warm without sacrificing dexterity with these cosy fingerless wool gloves. Knitted from a blend of merino wool and acrylic, they provide excellent insulation against cold winds while allowing full finger movement for typing, texting, and outdoor activities. The touchscreen-compatible fingertip fabric means you can use your smartphone without taking them off. Ribbed cuffs ensure a snug, secure fit. Available in classic charcoal, navy, and burgundy. One size fits most adults."),
    ],
    "Electronics": [
        ("Wireless Bluetooth Earbuds TWS", 2499, 5999, ["wireless earbuds", "TWS earbuds", "bluetooth earbuds", "noise cancelling earbuds", "true wireless", "gaming earbuds", "earphones"],
         "Experience music in its purest form with these high-fidelity true wireless Bluetooth earbuds. Featuring the latest Bluetooth 5.3 technology, they deliver a stable connection up to 15 metres with zero dropouts. The custom-tuned 10mm dynamic drivers reproduce deep bass, clear mids, and crisp highs. Environmental Noise Cancellation (ENC) ensures crystal-clear calls in busy environments. Each earbud lasts 7 hours, with the charging case providing an additional 28 hours of playtime. IPX5 water-resistant."),
        ("4K Ultra HD Webcam 1080p", 1999, 4999, ["webcam", "4K webcam", "HD webcam", "laptop camera", "streaming camera", "work from home", "USB webcam"],
         "Elevate your video calls and live streams with this professional-grade 4K ultra HD webcam. Featuring a 1/2.8-inch Sony sensor and f/2.0 aperture, it delivers stunningly clear, colour-accurate video even in low-light conditions. The built-in dual omnidirectional microphones with noise-cancellation technology capture your voice crisply from up to 2 metres away. The universal clip fits monitors up to 50mm thick, and plug-and-play USB-A connectivity means zero driver installation. Compatible with all major conferencing platforms."),
        ("Mini Portable Bluetooth Speaker", 1299, 2999, ["bluetooth speaker", "portable speaker", "waterproof speaker", "outdoor speaker", "mini speaker", "TWS speaker", "bass speaker"],
         "Take your music anywhere with this rugged mini Bluetooth speaker. Despite its compact size, it delivers surprisingly powerful 360° sound with deep, punchy bass courtesy of its dual passive radiators. The IPX7 waterproof rating means it can be submerged in up to 1 metre of water for 30 minutes — perfect for pool parties and hiking trips. Pair two units wirelessly in True Wireless Stereo mode for an immersive stereo experience. Up to 12 hours of playtime on a single charge."),
        ("USB-C 65W GaN Fast Charger", 999, 2499, ["fast charger", "65W charger", "GaN charger", "USB-C charger", "laptop charger", "wall charger", "power adapter"],
         "Charge all your devices faster than ever with this compact 65W GaN (Gallium Nitride) fast charger. GaN technology allows for a charger that is 50% smaller than traditional silicon chargers while delivering more power. Features a single USB-C port with support for PD 3.0, QC 4.0+, and PPS protocols, making it compatible with laptops, smartphones, tablets, and earbuds. Built-in safeguards protect against overvoltage, over-current, over-temperature, and short circuits. Universal 100-240V input."),
        ("Smart LED Desk Lamp with USB", 899, 1999, ["desk lamp", "LED lamp", "smart lamp", "USB lamp", "study lamp", "eye-care lamp", "touch control lamp"],
         "Illuminate your workspace intelligently with this versatile LED desk lamp. Features five colour temperature modes (from warm 2700K to cool daylight 6500K) and seven brightness levels, giving you precise control over your lighting environment. The integrated USB-A charging port keeps your phone powered while you work. The memory function recalls your last settings on startup. The slim, adjustable neck bends 180° for targeted lighting. Eye-care technology minimises flicker and blue light to reduce eye strain during prolonged study or work sessions."),
        ("1080p Portable Projector", 8999, 14999, ["projector", "portable projector", "1080p projector", "mini projector", "home theatre projector", "WiFi projector", "smart projector"],
         "Transform any wall into a cinematic experience with this compact 1080p Full HD portable projector. Supports projection sizes from 40 to 200 inches at resolutions up to 1920x1080. Built-in 5W stereo speakers deliver impressive room-filling audio. Dual-band WiFi and screen-mirroring compatibility (AirPlay and Miracast) allow seamless wireless streaming from your smartphone or laptop. Built-in Android OS gives access to streaming apps. Keystone correction and autofocus ensure a sharp, undistorted image on any surface."),
        ("Mechanical Gaming Keyboard TKL", 3499, 7999, ["mechanical keyboard", "gaming keyboard", "TKL keyboard", "RGB keyboard", "tenkeyless", "tactile switches", "wired keyboard"],
         "Dominate every gaming session with this professional-grade tenkeyless mechanical gaming keyboard. Equipped with tactile blue switches, each keystroke provides satisfying tactile bump feedback and an audible click for precise, confident actuation. Per-key RGB backlighting with 20+ customisable lighting effects adds a dynamic aesthetic to your setup. The double-shot PBT keycaps are fade-resistant and more durable than standard ABS caps. A detachable USB-C braided cable ensures a clean, manageable desk setup. N-key rollover enables simultaneous key presses without ghosting."),
        ("Wireless Ergonomic Mouse", 1299, 2999, ["wireless mouse", "ergonomic mouse", "gaming mouse", "silent mouse", "laptop mouse", "2.4GHz mouse", "rechargeable mouse"],
         "Conquer long workdays with this ergonomic wireless mouse engineered to eliminate wrist fatigue. The sculpted vertical design places your hand in a natural handshake position, reducing strain on the wrist and forearm. The 2.4GHz wireless connection delivers a lag-free signal up to 10 metres. Adjustable DPI (400/800/1200/2400/4000) caters to different work and gaming needs. Six programmable buttons can be customised with your preferred shortcuts. Rechargeable via USB-C — a full charge provides up to 60 days of typical use."),
        ("Smart Power Strip 6-in-1 with USB", 1499, 3499, ["power strip", "smart power strip", "USB power strip", "surge protector", "extension board", "6 socket", "fast charging",],
         "Power your entire home office intelligently with this 6-outlet smart power strip. Features six universal AC outlets and four USB-A ports (5V/2.4A each) plus one USB-C PD port (18W) for fast charging all your devices simultaneously. Built-in surge protector guards connected devices against voltage spikes and electrical fluctuations. Individual LED power-status indicators on each outlet provide at-a-glance monitoring. The 1.8-metre braided cable reaches comfortably across your desk. Overload protection auto-cuts power if consumption exceeds safe levels."),
        ("Digital Noise-Cancelling Headphones", 4999, 9999, ["noise cancelling headphones", "ANC headphones", "wireless headphones", "over-ear headphones", "bluetooth headphones", "foldable headphones", "studio headphones"],
         "Immerse yourself completely in your music with these flagship active noise-cancelling headphones. The hybrid ANC system uses multiple microphones inside and outside the ear cups to eliminate up to 35dB of ambient noise. The 40mm neodymium drivers deliver rich, studio-quality sound with expansive soundstage. Wear Detection automatically pauses playback when you remove the headphones. Up to 30 hours of listening time with ANC enabled, or 50 hours with it off. The foldable design and premium carrying case make them ideal travel companions."),
        ("10000mAh Slim Power Bank", 1299, 2999, ["power bank", "10000mAh", "slim power bank", "fast charging power bank", "portable charger", "pocket charger", "USB-C power bank"],
         "Never run out of battery again with this ultra-slim 10000mAh power bank. Despite its compact form — just 15mm thin — it packs enough juice for approximately 2.5 full charges of a typical smartphone. Features a USB-C input and output (18W PD) along with two USB-A ports (22.5W total), enabling simultaneous charging of three devices. The LED indicator shows remaining charge at a glance. Safety certifications include CE, RoHS, and FCC. Airline compliant for carry-on baggage."),
        ("Smart WiFi Plug 16A 4-Pack", 1999, 4499, ["smart plug", "wifi plug", "smart home", "voice control plug", "Alexa plug", "Google home", "4 pack plug"],
         "Bring intelligence to every corner of your home with this 4-pack of smart WiFi plugs. Each plug supports 16A / 3840W load, suitable for controlling high-wattage appliances like air conditioners, geysers, and irons. Pair with the dedicated app to create schedules, set countdown timers, and monitor real-time energy consumption. Compatible with Alexa, Google Assistant, and IFTTT for hands-free voice control. No hub required — connects directly to your 2.4GHz WiFi network for instant setup."),
        ("USB 3.0 256GB Flash Drive", 799, 1799, ["pen drive", "USB flash drive", "256GB pen drive", "USB 3.0", "portable storage", "high speed USB", "data transfer"],
         "Store, transfer, and back up your files with blazing speed using this 256GB USB 3.0 flash drive. Read speeds up to 130MB/s and write speeds up to 60MB/s make transferring large files — full HD movies, high-resolution photos, and large documents — fast and efficient. The robust, compact metal casing is both shock-resistant and heat-resistant for long-term durability. The built-in keyring hole makes it easy to attach to your keys or bag. Compatible with Windows, Mac, Linux, and smart TVs."),
        ("Smart Home Security Camera 2K", 2999, 6999, ["security camera", "CCTV camera", "smart camera", "2K camera", "WiFi camera", "night vision camera", "indoor camera"],
         "Monitor your home with confidence using this crystal-clear 2K indoor security camera. The 4MP sensor captures sharp, detailed footage day and night, with colour night vision up to 10 metres. Two-way audio lets you speak and listen in real time through the companion app from anywhere in the world. AI-powered human detection sends instant push notifications only for relevant motion, eliminating false alerts. Local storage via Micro SD (up to 256GB) and optional cloud backups provide flexible recording options. Works with Alexa and Google Assistant."),
        ("Laptop Cooling Pad with LED", 799, 1799, ["laptop stand", "cooling pad", "laptop cooler", "USB cooling fan", "LED cooling pad", "gaming cooler", "anti-slip stand"],
         "Keep your laptop running at peak performance with this whisper-quiet laptop cooling pad. Five high-speed fans — one large central fan and four corner fans — create a powerful airflow that dramatically reduces laptop temperature during intensive tasks or gaming. Supports laptops from 12 to 17 inches. The adjustable tilt angles (15°, 20°, 25°) allow you to find the most ergonomic viewing position. Powered via USB, with an extra USB-A passthrough port so you don't lose a port. The LED lighting ring adds a subtle gaming aesthetic."),
    ],
}

products = []
cat_images_idx = {cat: 0 for cat in IMAGES}

for cat, cat_sellers in seller_by_cat.items():
    templates = PRODUCT_TEMPLATES[cat]
    imgs = IMAGES[cat]

    for seller in cat_sellers:
        count = random.randint(10, 15)
        used = set()
        for i in range(count):
            # pick a unique template
            t_idx = i % len(templates)
            (base_title, price_min, price_max, keywords, base_desc) = templates[t_idx]

            # add slight variation so titles aren't cloned
            variations = ["Premium", "Classic", "Elite", "Deluxe", "Pro", "Signature", "Essential", "Ultra", "Select", "Plus", "Gold", "Silver"]
            variant = random.choice(variations)
            title_variants = [
                base_title,
                f"{variant} {base_title}",
                f"{base_title} – {seller['shop_name']} Edition",
                f"{base_title} (Pack of {random.choice([1,2,3])})",
            ]
            title = title_variants[i % len(title_variants)]

            price = round(random.uniform(price_min, price_max * 0.7), -1)  # realistic discount
            original_price = round(price * random.uniform(1.1, 1.5), -1)

            # fairness distribution: 30% new, 50% normal, 20% high
            tier = random.choices(["new", "normal", "high"], weights=[30, 50, 20])[0]
            if tier == "new":
                impressions = random.randint(0, 50)
                ctr = random.uniform(0.02, 0.08)
            elif tier == "normal":
                impressions = random.randint(100, 500)
                ctr = random.uniform(0.05, 0.15)
            else:
                impressions = random.randint(500, 2000)
                ctr = random.uniform(0.1, 0.25)

            clicks = int(impressions * ctr)
            orders_cnt = int(clicks * random.uniform(0.05, 0.25))
            rating = round(random.uniform(3.2, 5.0), 1) if orders_cnt > 0 else round(random.uniform(0, 4.5), 1)
            rating_count = orders_cnt * random.randint(1, 3) if orders_cnt > 0 else 0

            img_idx = cat_images_idx[cat] % len(imgs)
            cat_images_idx[cat] += 1

            fair_score = round(
                0.3 * (1 - impressions / 2500) +
                0.3 * (price_min / price_max) +
                0.2 * (1 / (1 + orders_cnt)) +
                0.2 * random.uniform(0, 1),
                4
            )

            created_at = rand_date(365)
            p = {
                "_id": uid(),
                "name": title,
                "category": cat,
                "price": price,
                "original_price": original_price,
                "description": base_desc,
                "keywords": keywords,
                "image": imgs[img_idx],
                "seller_id": seller["_id"],
                "seller_name": seller["name"],
                "shop_name": seller["shop_name"],
                "impressions": impressions,
                "clicks": clicks,
                "orders": orders_cnt,
                "rating": rating,
                "rating_count": rating_count,
                "fair_score": fair_score,
                "tier": tier,
                "approved": True,
                "in_stock": random.choice([True, True, True, False]),
                "stock_qty": random.randint(0, 500),
                "created_at": created_at,
                "updated_at": created_at,
            }
            products.append(p)

print(f"[OK] Generated {len(products)} products")


# ────────────────────────────────────────────────────────────────────────────────
# 3. CUSTOMERS
# ────────────────────────────────────────────────────────────────────────────────
FIRST_NAMES = [
    "Aarav","Aditi","Akash","Anjali","Arjun","Bhavna","Chetan","Deepika",
    "Dhruv","Divya","Gaurav","Harshita","Ishaan","Jyoti","Kabir","Khushi",
    "Kiran","Komal","Lakshmi","Manish","Meera","Mohit","Natasha","Nisha",
    "Nitin","Pallavi","Piyush","Pooja","Pradeep","Priya","Rahul","Rajni",
    "Ramesh","Ritu","Rohit","Sakshi","Sandeep","Sangeetha","Saurabh","Seema",
    "Shilpa","Shreya","Siddharth","Simran","Sneha","Sunil","Tanvi","Tina",
    "Uday","Vandana","Varun","Veena","Vikram","Vineeta","Virat","Yamini",
    "Yash","Zara","Aditya","Ananya","Arnav","Asha","Avinash","Bharat",
    "Chandra","Diya","Eshan","Farida","Gayatri","Heena","Ila","Jagdish",
    "Kalpana","Lalit","Madhu","Naresh","Ojasvi","Pankaj","Qadir","Radha",
    "Sapna","Tarun","Umesh","Vijay","Waqar","Xenia","Younus","Zeenat",
    "Abhishek","Bhavesh","Chhaya","Devika","Ekta","Faisal","Girish",
]
LAST_NAMES = [
    "Sharma","Verma","Gupta","Singh","Joshi","Mehta","Patel","Reddy","Nair",
    "Kumar","Pillai","Iyer","Bose","Bansal","Kapoor","Mishra","Tiwari","Rao",
    "Agarwal","Desai","Chopra","Das","Saxena","Chauhan","Srivastava","Malhotra",
    "Pandey","Shah","Trivedi","Jain","Dubey","Bhatt","Kaur","Chaudhary",
    "Sinha","Rathore","Thakur","Menon","Krishnamurthy","Venkatesh",
]

customers = []
for i in range(random.randint(88, 100)):
    fn = random.choice(FIRST_NAMES)
    ln = random.choice(LAST_NAMES)
    num = random.randint(1, 999)
    cust = {
        "_id": uid(),
        "name": f"{fn} {ln}",
        "email": f"{fn.lower()}.{ln.lower()}{num}@gmail.com",
        "password": "hashed_placeholder",
        "role": "customer",
        "joined": rand_date(500),
        "city": random.choice(["Mumbai","Delhi","Bangalore","Chennai","Hyderabad","Pune","Kolkata","Ahmedabad","Jaipur","Surat"]),
    }
    customers.append(cust)

# deduplicate emails
seen_emails = set()
unique_customers = []
for c in customers:
    if c["email"] not in seen_emails:
        seen_emails.add(c["email"])
        unique_customers.append(c)
customers = unique_customers
print(f"[OK] Generated {len(customers)} customers")


# ────────────────────────────────────────────────────────────────────────────────
# 4. ORDERS
# ────────────────────────────────────────────────────────────────────────────────
# Only products with orders > 0
orderable_products = [p for p in products if p["orders"] > 0]

orders = []
STATUSES = ["pending", "delivered", "delivered", "delivered", "shipped", "cancelled"]

for p in orderable_products:
    num_orders = min(p["orders"], 8)  # cap per-product seeded orders
    for _ in range(num_orders):
        cust = random.choice(customers)
        qty = random.randint(1, 3)
        total = round(p["price"] * qty, 2)
        order_dt = rand_date(300)
        o = {
            "_id": uid(),
            "product_id": p["_id"],
            "product_name": p["name"],
            "seller_id": p["seller_id"],
            "seller_name": p["seller_name"],
            "shop_name": p["shop_name"],
            "customer_id": cust["_id"],
            "customer_name": cust["name"],
            "customer_email": cust["email"],
            "quantity": qty,
            "price_per_unit": p["price"],
            "total_price": total,
            "category": p["category"],
            "status": random.choice(STATUSES),
            "created_at": order_dt,
            "updated_at": order_dt,
            "address": f"{random.randint(1,999)}, {random.choice(['MG Road','Park Street','Anna Salai','FC Road','Brigade Road','Sector {}'.format(random.randint(1,50))])}, {cust.get('city','Mumbai')} - {random.randint(100000,999999)}",
        }
        orders.append(o)

print(f"[OK] Generated {len(orders)} orders")


# ────────────────────────────────────────────────────────────────────────────────
# 5. WRITE JSON FILES
# ────────────────────────────────────────────────────────────────────────────────
def save(name, data):
    path = os.path.join(OUTPUT_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    size_kb = os.path.getsize(path) / 1024
    print(f"[SAVED] {name} ({len(data)} records, {size_kb:.1f} KB)")

save("sellers.json",  sellers)
save("products.json", products)
save("customers.json", customers)
save("orders.json",   orders)


print("\n=== Dataset generation complete! ===")
print(f"   Output    -> {OUTPUT_DIR}")
print(f"   Sellers   : {len(sellers)}")
print(f"   Products  : {len(products)}")
print(f"   Customers : {len(customers)}")
print(f"   Orders    : {len(orders)}")
