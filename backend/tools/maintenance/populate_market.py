from pathlib import Path
import sys

TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from path_helper import ensure_backend_on_path

ensure_backend_on_path()

from db import activity_logs_collection, orders_collection, products_collection, users_collection
from product_scoring import apply_score_fields
from werkzeug.security import generate_password_hash
import random
import uuid
import time
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
#  500 UNIQUE PRODUCTS ACROSS 4 CATEGORIES  +  NEW SELLERS WITH 30 % OFF
# ─────────────────────────────────────────────────────────────────────────────

# ── Unsplash image pools (each one is a different product photo) ──────────────
IMG_ELECTRONICS = [
    "https://images.unsplash.com/photo-1511467687858-23d96c32e4ae?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1591488320449-011701bb6704?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1588702547923-7408822a11bb?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1546054454-aa26e2b734c7?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1585771724684-38269d6639fd?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1534802046520-4f27db7f3ae5?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1498049794561-7780e7231661?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1612444168284-dfad5b8d3527?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1600294037681-c80b4cb5b434?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1563203369-26f2e4a5ccf7?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1574944985070-8f3ebc6b79d2?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1596741964756-dd9f0a4dd68c?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1484704849700-f032a568e944?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1605236453806-6ff36851218e?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1606144042614-b2417e99c4e3?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1551808525-51a94da548ce?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1567581935884-3349723552ca?auto=format&fit=crop&q=80&w=800",
]

IMG_FASHION = [
    "https://images.unsplash.com/photo-1520639888713-7851133b1ed0?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1539109136881-3be0616acf4b?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1556821840-3a63f95609a7?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1520520731457-9283dd14aa66?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1558769132-cb1aea458c5e?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1551232864-3f0890e580d9?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1469334031218-e382a71b716b?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1516762689617-e1cffcef479d?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1578587018452-892bacefd3f2?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1572635196237-14b3f281503f?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1594938298603-c8148c4b1987?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1523381210434-271e8be1f52b?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1560769629-975ec94e6a86?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1614680376408-81e91ffe3db7?auto=format&fit=crop&q=80&w=800",
]

IMG_KITCHEN = [
    "https://images.unsplash.com/photo-1584286595398-a59f21d313f5?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1510076857177-7470076d4098?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1567080597717-adc6513bad85?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1585771724684-38269d6639fd?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1556909172-54557c7e4fb7?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1528712306091-ed0763094c98?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1621298750629-77e0e68e4e35?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1607083206968-13611e3d76db?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1570733577524-3a047079e80d?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1595515106864-077d4d1a84b3?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1622209374-4ca8b9e3b4b8?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1583908600395-01f11ece8a84?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1565183928294-7063f23ce0f8?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1505968409348-bd000797c92e?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1598300042247-d088f8ab3a91?auto=format&fit=crop&q=80&w=800",
]

IMG_ACCESSORIES = [
    "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1627123424574-724758594e93?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1611923134239-b9be5816e23c?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1590874103328-eac38a683ce7?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1585386959984-a4155224a1ad?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1473188588951-666fce8e7c68?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1491553895911-0055eca6402d?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1575936123452-b67c3203c357?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1531297484001-80022131f5a1?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1563013544-824ae1b704d3?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1591561954557-26941169b49e?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1598300042247-d088f8ab3a91?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1614173897085-ebe7f30c8e72?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?auto=format&fit=crop&q=80&w=800",
    "https://images.unsplash.com/photo-1620813588659-f47bc0ba5ead?auto=format&fit=crop&q=80&w=800",
]

# ── 125 unique names + prices per category (125 × 4 = 500 products) ───────────

ELECTRONICS_PRODUCTS = [
    ("Wireless Noise-Cancelling Headphones Pro", 14999),
    ("Mechanical RGB Gaming Keyboard", 4500),
    ("Ultra-Wide 4K Productivity Monitor", 28999),
    ("USB-C Multi-Port Docking Hub", 3299),
    ("True Wireless Earbuds Elite", 7999),
    ("Smart 4K Android TV Box", 5499),
    ("Portable Bluetooth Speaker 360°", 3799),
    ("Gaming Mouse 25600 DPI", 2999),
    ("Foldable Wireless Charging Pad", 2199),
    ("Curved Gaming Monitor 165Hz", 32999),
    ("Mini PC Intel i7 NUC", 41999),
    ("Smart Home Hub Controller", 4999),
    ("Webcam 4K 60fps Auto-Focus", 6499),
    ("Mechanical Numpad RGB", 1799),
    ("Noise-Cancelling Neckband Earphones", 3499),
    ("Portable SSD 2TB Ultra Speed", 8999),
    ("Smart LED Desk Lamp USB-C", 2499),
    ("Wireless Presenter Remote Laser", 1499),
    ("Phone Gimbal Stabiliser 3-Axis", 4299),
    ("Foldable Bluetooth Keyboard", 2799),
    ("USB Condenser Microphone Studio", 4999),
    ("Ring Light 18-inch Professional", 3999),
    ("NVMe SSD 1TB PCIe Gen4", 7499),
    ("DDR5 RAM 32GB 6000MHz Kit", 12999),
    ("ATX Mid-Tower PC Case Mesh", 6999),
    ("80+ Gold PSU 750W Modular", 8499),
    ("CPU Cooler 240mm AIO Liquid", 6999),
    ("RTX-Class GPU Cooler Bracket", 1299),
    ("HDMI 2.1 48Gbps 3m Cable", 899),
    ("Thunderbolt 4 Dock 11-in-1", 9999),
    ("Smart Power Strip with USB", 2299),
    ("Wireless Gaming Headset 7.1", 5999),
    ("Earphone DAC Amplifier USB-C", 3299),
    ("Wireless Car Charger Mount", 1699),
    ("Action Camera 4K 60fps Waterproof", 14999),
    ("Digital Drawing Tablet A5", 5499),
    ("Smart Pen Stylus AI OCR", 3799),
    ("Pocket Projector 1080p HDMI", 18999),
    ("Laser Pico Projector 4K", 42999),
    ("Smart Doorbell Camera 2K", 4999),
    ("Indoor Security Camera Pan-Tilt", 2999),
    ("Robot Vacuum & Mop Combo", 19999),
    ("Smart Wireless Weather Station", 3499),
    ("Digital Microscope USB 1000x", 4999),
    ("Oscilloscope Handheld 50MHz", 8999),
    ("Soldering Station Digital 60W", 3499),
    ("Portable Power Station 500Wh", 24999),
    ("Solar Panel 100W Foldable", 8999),
    ("Raspberry Pi Starter Kit v5", 6999),
    ("Arduino Mega Starter Bundle", 2999),
    ("ESP32 IoT Dev Board Kit", 1299),
    ("Logic Analyser 8-Channel USB", 2499),
    ("Smart Sensor Kit 37 in 1", 1999),
    ("LED Strip WiFi 5m RGBW", 1299),
    ("Smart Switch Zigbee 3-Gang", 1799),
    ("Motion Sensor PIR Wireless", 799),
    ("Smart Lock Fingerprint Keypad", 7999),
    ("Video Doorbell Solar Powered", 6499),
    ("Wireless CCTV Kit 8-Channel 4K", 29999),
    ("NAS Storage 4-Bay Network", 16999),
    ("10GbE Network Switch Managed", 12999),
    ("Wi-Fi 6E Router Tri-Band", 13999),
    ("Wi-Fi Range Extender AX3000", 4499),
    ("Mesh Wi-Fi System 3-Pack", 15999),
    ("Gaming Chair with RGB LED", 14999),
    ("Ergonomic Office Chair Mesh", 11999),
    ("Monitor Arm Dual Adjustable", 4199),
    ("Cable Management Raceway Kit", 1199),
    ("Anti-Static Wrist Strap & Mat", 499),
    ("Thermal Paste Premium 3.5g", 399),
    ("Compressed Air Duster Electric", 1999),
    ("UPS 1000VA 600W Desktop", 7999),
    ("KVM Switch 2-Port HDMI 4K", 3499),
    ("HDMI Splitter 1x4 4K60", 1999),
    ("DisplayPort 1.4 Cable 2m", 599),
    ("USB-C to DisplayPort 8K Adapter", 1499),
    ("Graphic Tablet Pen Display 13\"", 21999),
    ("3D Pen PLA Filament Creative", 2499),
    ("FDM 3D Printer Auto-Levelling", 17999),
    ("Resin 3D Printer 4K Mono", 24999),
    ("CNC Laser Engraver 20W", 19999),
    ("Thermal Label Printer 4x6\"", 3999),
    ("Photo Printer A4 Inkless", 5999),
    ("Barcode Scanner 2D USB", 2499),
    ("POS Receipt Printer Thermal", 6999),
    ("RFID Card Reader Writer USB", 1199),
    ("Fingerprint Scanner USB Module", 1599),
    ("DSLR Camera Body 24MP APS-C", 49999),
    ("Mirrorless Camera Kit 20MP", 54999),
    ("Vlogging Camera 4K Flip Screen", 29999),
    ("Camera Drone GPS 4K OcuSync", 39999),
    ("FPV Racing Drone DIY Kit", 14999),
    ("Gimbal Camera 3-Axis Handheld", 22999),
    ("LED Video Light Panel Bi-Colour", 4999),
    ("Softbox Lighting Kit 2x70W", 5999),
    ("Backdrop Stand Kit 10x7ft", 3499),
    ("Green Screen Collapsible 5x7", 2499),
    ("Shotgun Microphone Camera XLR", 5499),
    ("Wireless Lavalier Microphone", 4999),
    ("Audio Interface 2-In 2-Out USB", 8499),
    ("Studio Monitor Speakers 5\"", 12999),
    ("DJ Controller 2-Deck Compact", 9999),
    ("MIDI Keyboard 49-Key USB", 5999),
    ("Guitar Effects Pedal Multi-FX", 7999),
    ("Digital Piano 88-Key Weighted", 34999),
    ("Electric Guitar Starter Pack", 12999),
    ("Bass Guitar Amp 15W Combo", 6999),
    ("Podcast Microphone USB XLR", 6499),
    ("Streaming Deck Hotkeys 15", 9999),
    ("Capture Card 4K HDMI USB-C", 7499),
    ("Gaming Monitor 27\" 240Hz IPS", 35999),
    ("Gaming Monitor 32\" 4K 144Hz", 45999),
    ("Ultrawide Monitor 34\" 100Hz", 28999),
    ("Portable Monitor 15.6\" USB-C", 13999),
    ("Smart TV 55\" 4K QLED Android", 54999),
    ("Projector 4K Laser Home Theater", 89999),
    ("Soundbar 3.1 Dolby Atmos", 18999),
    ("Wi-Fi Smart Speaker Assistant", 5999),
    ("Wireless Earphones ANC Sport", 4499),
    ("Over-Ear Audiophile Headphones", 22999),
    ("Hi-Fi Amplifier Class-D 200W", 15999),
    ("DAC Hi-Res USB Optical", 8999),
    ("Turntable Vinyl Bluetooth", 11999),
    ("Portable DAB FM Radio", 2999),
    ("Smart Clock Radio Wireless Charge", 3499),
]

FASHION_PRODUCTS = [
    ("Premium Beige Wool Trench Coat", 8999),
    ("Modern Black Aviator Sunglasses", 2499),
    ("Designer Italian Leather Boots", 12500),
    ("Organic Cotton Minimalist Hoodie", 1999),
    ("Slim-Fit Stretch Chinos Dark Navy", 2299),
    ("Floral Maxi Wrap Dress", 3499),
    ("Premium Leather Oxford Shoes", 5999),
    ("Athletic Performance Joggers", 1799),
    ("Oversized Linen Blazer Cream", 4999),
    ("Puffer Jacket Water-Repellent", 5499),
    ("Cashmere Turtleneck Sweater", 6999),
    ("High-Waist Pleated Midi Skirt", 2799),
    ("Canvas Low-Top Sneakers White", 2199),
    ("Leather Chelsea Boots Brown", 6499),
    ("Denim Jacket Vintage Wash", 3299),
    ("Printed Silk Blouse Floral", 3799),
    ("Men's Classic Polo Shirt Pique", 1499),
    ("Women's Ribbed Crop Tank", 999),
    ("Straight-Leg Raw Denim Jeans", 3999),
    ("Skinny Fit Black Jeans Stretch", 2499),
    ("Relaxed Fit Cargo Pants", 2699),
    ("Pleated Palazzo Wide-Leg Pants", 3199),
    ("Thermal Base Layer Set", 2199),
    ("Merino Wool Running Socks 3-Pack", 899),
    ("Compression Leggings High-Rise", 1799),
    ("Sports Bra High-Impact Racerback", 1299),
    ("Quick-Dry Swim Shorts Tropical", 1499),
    ("Printed Bandana Headscarf", 499),
    ("Knit Beanie Logo Embroidered", 699),
    ("Bucket Hat Reversible Cotton", 899),
    ("Classic Fedora Hat Wide Brim", 1999),
    ("Wool Flat Cap Herringbone", 1299),
    ("Baseball Cap Structured 6-Panel", 799),
    ("Ankle Strap Heeled Sandals", 3299),
    ("Block-Heel Mule Suede", 3799),
    ("Strappy Flat Sandals Leather", 2299),
    ("Platform Sneakers Chunky Sole", 4499),
    ("Slip-On Loafers Suede Tassel", 3999),
    ("Derby Shoes Brogue Cap-Toe", 5499),
    ("Monk Strap Leather Shoes", 6999),
    ("Running Shoes Responsive Foam", 5999),
    ("Trail Hiking Boots Gore-Tex", 7499),
    ("Waterproof Rain Boots Matte", 3999),
    ("Fur-Lined Snow Boots Lace-Up", 5999),
    ("Embroidered Denim Shorts", 1699),
    ("A-Line Mini Skirt Tweed", 2499),
    ("Bodycon Bandage Dress Mini", 2799),
    ("Off-Shoulder Evening Gown Satin", 8999),
    ("Tuxedo Suit 2-Piece Slim Fit", 12999),
    ("Double-Breasted Suit Charcoal", 14999),
    ("Linen Safari Shirt Short Sleeve", 1799),
    ("Chambray Shirt Button-Down", 1599),
    ("Flannel Overshirt Plaid", 2299),
    ("Henley Long-Sleeve Cotton", 1199),
    ("Graphic Tee Premium Cotton", 899),
    ("Essential V-Neck T-Shirt 3-Pack", 1299),
    ("Crew-Neck Sweatshirt Fleece", 1799),
    ("Zip-Up Hoodie Heavyweight", 2499),
    ("Bomber Jacket Satin Shell", 4999),
    ("Leather Biker Jacket Moto", 14999),
    ("Teddy Shearling Coat", 9999),
    ("Velvet Blazer Party-Ready", 6999),
    ("Knit Cardigan Button-Front", 2999),
    ("Mohair Blend Oversized Sweater", 4999),
    ("Fair Isle Intarsia Jumper", 3499),
    ("Turtleneck Cable-Knit Pullover", 3799),
    ("Mesh Insert Athletic Shorts", 1399),
    ("Cycling Bib Shorts Padded", 2499),
    ("Compression Arm Sleeves UV", 799),
    ("Yoga Pants 4-Way Stretch", 1999),
    ("Water-Repellent Windbreaker", 3499),
    ("Softshell Hiking Jacket", 4999),
    ("Raincoat Packable Poncho", 2799),
    ("Down Vest Quilted Light", 3299),
    ("Fleece Pullover Anti-Pill", 1899),
    ("Pocket Square Silk Printed", 599),
    ("Tie Slim Italian Silk", 1799),
    ("Bow Tie Self-Tie Classic", 999),
    ("Cufflinks Silver Polished", 1499),
    ("Lapel Pin Enamel Floral", 499),
    ("Scarf Cashmere Blend Plaid", 2999),
    ("Gloves Leather Lined Warm", 1799),
    ("Belt Braided Leather Brown", 1299),
    ("D-Ring Canvas Belt Casual", 899),
    ("Suspenders Leather End Y-Back", 1199),
    ("Socks Bamboo Ankle 5-Pack", 1099),
    ("No-Show Socks Cotton 6-Pack", 799),
    ("Knee-High Wool Socks Striped", 999),
    ("Tights 80 Denier Matte Black", 599),
    ("Strapless Bandeau Bra Seamless", 899),
    ("Lace Bralette Unlined", 1099),
    ("Full-Brief Cotton 5-Pack", 899),
    ("Boxer Briefs Modal Stretch 3-Pack", 1199),
    ("Pajama Set Flannel Plaid", 2499),
    ("Robe Waffle-Knit Cotton", 2999),
    ("Slip Dress Satin Midi Ivory", 3499),
    ("Corset Top Zip-Front Boned", 2799),
    ("Shacket Duster Linen Blend", 3999),
    ("Co-Ord Set Matching Two-Piece", 4499),
    ("Abaya Open-Front Modest Dress", 5999),
    ("Kurta Set Embroidered Cotton", 3999),
    ("Saree Georgette Printed", 4999),
    ("Lehenga Choli Festive", 8999),
    ("Sherwani Wedding Elaborate", 24999),
    ("Dhoti Kurta Traditional Cotton", 2999),
    ("Salwar Kameez Anarkali Flared", 4499),
    ("Dupatta Zari Woven Silk", 1999),
    ("Palazzo Kurti Set Party", 3499),
    ("Churidar Embroidered Floral", 2799),
    ("Kaftan Tie-Dye Resort Wear", 3299),
    ("Linen Co-Ord Relaxed Summer", 3999),
    ("Boilersuit Utility One-Piece", 3499),
    ("Jumpsuit Wide-Leg Belted", 4299),
    ("Romper Floral Print Smocked", 2499),
    ("Dungaree Denim Vintage", 2999),
    ("Pinafore Dress Check Wool", 3499),
    ("Shirt Dress Striped Poplin", 2999),
    ("Wrap Dress Midi Jersey", 2799),
    ("Bodysuit Ribbed Square Neck", 1299),
    ("Blazer Dress Power Shoulder", 6999),
    ("Longline Blazer Oversized", 5499),
    ("Cropped Jacket Bouclé Tweed", 7999),
    ("Halter Neck Bikini Set Tropical", 2499),
    ("UV Protective Rashguard Long Sleeve", 1999),
    ("Compression Shorts Running 7-Inch", 1299),
]

KITCHEN_PRODUCTS = [
    ("Sleek Matte Black Espresso Machine", 18999),
    ("Smart Multi-Cooker Air Fryer XL", 7500),
    ("Hand-Blown Glass Decanter Set", 3200),
    ("Minimalist Ceramic Dinnerware 12pc", 4900),
    ("Stainless Steel Pressure Cooker 6L", 5999),
    ("Cast Iron Skillet 12-inch Pre-Seasoned", 3499),
    ("Non-Stick Ceramic Cookware Set 9pc", 7999),
    ("Chef's Knife German Steel 8\"", 2999),
    ("Knife Block Set 15-Piece", 6999),
    ("Marble Rolling Pin with Handles", 1299),
    ("Silicone Baking Mat Set 3-Pack", 799),
    ("Stainless Mixing Bowl Set 5-Pack", 1999),
    ("Digital Kitchen Scale 10kg", 1499),
    ("Instant-Read Thermometer Precision", 1299),
    ("Stand Mixer 5.5L Professional", 18999),
    ("Hand Blender Immersion 800W", 2499),
    ("Food Processor 12-Cup Pulse", 5999),
    ("High-Power Blender 2HP", 8999),
    ("Cold Press Juicer Slow 80 RPM", 7999),
    ("Grain Mill Electric 500W", 5499),
    ("Pasta Maker Machine 9 Thickness", 4999),
    ("Bread Machine 2lb Progammable", 7499),
    ("Toaster Oven Convection 30L", 6999),
    ("Microwave Oven Inverter 25L", 9499),
    ("Electric Kettle Gooseneck 1L", 2999),
    ("French Press Coffee 1L Double Wall", 1599),
    ("Pour-Over Coffee Dripper Kit", 2199),
    ("Cold Brew Coffee Maker 1L", 1799),
    ("Stovetop Moka Pot 6-Cup", 1099),
    ("Coffee Grinder Burr Electric", 3499),
    ("Milk Frother Handheld Electric", 599),
    ("Waffle Maker Belgian Deep-Pockets", 3999),
    ("Sandwich Press Grill Panini", 2499),
    ("Crepe Maker 30cm Electric", 2299),
    ("Rice Cooker Fuzzy Logic 1.8L", 4999),
    ("Slow Cooker Oval 6.5L", 4499),
    ("Induction Cooktop Portable 2000W", 3499),
    ("Wok Carbon Steel 14\" Traditional", 2299),
    ("Dutch Oven Enamelled Cast Iron 5L", 8999),
    ("Tagine Moroccan Terracotta", 3999),
    ("Sushi Making Kit Complete 11pc", 1299),
    ("Mortar & Pestle Granite 15cm", 1799),
    ("Mandoline Slicer Adjustable 5-Blade", 2499),
    ("Spiralizer 7-Blade Vegetable", 1499),
    ("Cherry & Olive Pitter", 899),
    ("Garlic Press Stainless Rocker", 699),
    ("Herb Scissors 5-Blade", 599),
    ("Avocado Slicer Tool 3-in-1", 499),
    ("Egg Cooker 7-Egg Electric", 1299),
    ("Donut Pan Non-Stick 6-Cavity", 899),
    ("Bundt Cake Pan Heavy-Gauge", 1299),
    ("Springform Pan 10\" Leakproof", 1099),
    ("Cast Iron Loaf Pan Seasoned", 2499),
    ("Muffin Pan 12-Cup Non-Stick", 999),
    ("Pizza Steel Baking Stone 38cm", 3499),
    ("Sourdough Proving Basket Banneton", 1199),
    ("Lame Bread Scoring Knife", 799),
    ("Dough Scraper Bench Stainless", 499),
    ("Kitchen Aid Silicone Spatula Set", 899),
    ("Slotted Turner Stainless Fish", 699),
    ("Spider Strainer Wok Skimmer", 599),
    ("Ladle Stainless Deep Bowl", 549),
    ("Wooden Spoon Set Olive Wood 6pc", 999),
    ("Tongs Locking 30cm Silicone Tips", 699),
    ("Kitchen Scissors Heavy-Duty", 799),
    ("Peeler Y-Julianne 2-in-1", 499),
    ("Colander Stainless 5L Folding", 1299),
    ("Salad Spinner Large 5L", 1599),
    ("Compost Bin Countertop Charcoal", 1899),
    ("Food Saver Vacuum Sealer", 4999),
    ("Vacuum Bags Gallon 100-Count", 999),
    ("Reusable Silicone Food Bags 6pc", 1299),
    ("Beeswax Wraps Organic 8-Pack", 799),
    ("Glass Meal Prep Containers 5pc", 1499),
    ("Stainless Lunch Box 3-Tier", 1299),
    ("Tiffin Box 4-Layer Indian", 999),
    ("Thermos Flask 1L Vacuum", 1799),
    ("Water Bottle Insulated 750ml", 1299),
    ("Infuser Bottle Fruit Tea 700ml", 999),
    ("Drinkware Set Crystal 12pc", 3999),
    ("Wine Glasses Stemless 8-Pack", 2499),
    ("Champagne Flutes Fine Rim 6-Pack", 2199),
    ("Beer Stein Ceramic Lidded 1L", 1499),
    ("Cocktail Shaker Set Stainless 6pc", 2299),
    ("Bar Spoon Twisted Muddler", 699),
    ("Ice Ball Maker Silicone 4-Sphere", 899),
    ("Cutting Board Bamboo End-Grain XL", 3999),
    ("Cutting Board Set 3-Colour Plastic", 1199),
    ("Knife Magnetic Strip 40cm", 1299),
    ("Spice Rack Revolving 20-Jar", 1999),
    ("Salt & Pepper Grinder Set Glass", 1299),
    ("Oil & Vinegar Dispenser Set", 1099),
    ("Sugar Dispenser Stainless Pour", 699),
    ("Kitchen Timer Digital Magnetic", 799),
    ("Egg Slicer Wedger Sectioner", 499),
    ("Apple Corer Peeler Slicer 3-in-1", 799),
    ("Corn Stripper Peeler Cob", 449),
    ("Portion Scale Nutritional Display", 1999),
    ("Oven Thermometer Stainless Dial", 699),
    ("Candy Thermometer Clip 30cm", 799),
    ("Deep Fry Basket Stainless 28cm", 1299),
    ("Splatter Screen 13\" with Handle", 899),
    ("Oven Mitt Silicone Long 16\" Pair", 1199),
    ("Apron Canvas Barista Waxed", 1799),
    ("Chef Headband Hat White", 499),
    ("Kitchen Mat Anti-Fatigue 60x90cm", 2499),
    ("Dish Drying Rack Adjustable", 1799),
    ("Soap Dispenser Pump Stainless", 999),
    ("Bamboo Drawer Organiser 9-Slot", 1299),
    ("Pull-Out Cabinet Organiser", 1799),
    ("Lazy Susan Rotating Turntable", 1499),
    ("Utensil Holder Countertop Crock", 899),
    ("Paper Towel Holder Under-Cabinet", 799),
    ("Range Hood Filter Carbon Replacement", 899),
    ("Refrigerator Odour Absorber", 499),
    ("Dishwasher Cleaner Pods 30-Count", 799),
    ("Descaler Kettle Coffee Maker", 599),
    ("Copper Hammered Serving Bowl", 2999),
    ("Wooden Cheese Board & Knife Set", 2499),
    ("Slate Board Serving Tapas", 1999),
    ("Ramen Bowl Set 4-Piece Ceramic", 2299),
    ("Matcha Bowl Chawan Ceramic", 1199),
    ("Spaghetti Tong Stainless Lock", 499),
    ("Bento Box Lunch 1400ml 4-Comp", 1599),
    ("Electric Salt Pepper Grinder Auto", 1799),
]

ACCESSORIES_PRODUCTS = [
    ("Premium Leather Travel Backpack 40L", 6500),
    ("Slim Handcrafted Leather Wallet", 1499),
    ("Stainless Steel Mesh Smartwatch Band", 999),
    ("Carbon Fibre Laptop Case 15\"", 2800),
    ("Hardshell Spinner Luggage 24\"", 7999),
    ("Cabin Carry-On Polycarbonate 20\"", 5999),
    ("Toiletry Bag Hanging Organiser", 1799),
    ("Packing Cubes Set 6-Piece", 1499),
    ("Passport Holder RFID Block", 699),
    ("Travel Pillow Memory Foam U", 999),
    ("Noise-Cancelling Earplug Case", 599),
    ("Tech Pouch Organiser Cable Bag", 1299),
    ("Laptop Sleeve 14\" Neoprene", 999),
    ("Messenger Bag Canvas Waxed", 3499),
    ("Tote Bag Vegan Leather Structured", 2999),
    ("Crossbody Bag Mini Chain Strap", 2499),
    ("Bucket Bag Drawstring Leather", 3799),
    ("Satchel Bag Doctor Style", 4499),
    ("Clutch Bag Envelope Evening", 1999),
    ("Gym Bag Duffel Waterproof 40L", 2999),
    ("Drawstring Sack Pack Logo", 799),
    ("Fanny Pack Recycled Nylon", 1299),
    ("Belt Bag Hip Pouch Convertible", 1799),
    ("Sunglasses Polarised Wraparound", 1999),
    ("Sunglasses Round Metal Frame", 1799),
    ("Blue Light Glasses Anti-Fatigue", 1299),
    ("Reading Glasses +2.0 Compact Case", 899),
    ("Contact Lens Case Travel Dual", 299),
    ("Silk Eye Mask Sleeping Contoured", 699),
    ("Smart Sleep Tracker Band", 3499),
    ("Fitness Tracker 10-Day Battery", 4999),
    ("GPS Sports Watch Multisport", 14999),
    ("Casual Hybrid Smartwatch", 8999),
    ("Analogue Watch Minimalist Leather", 5999),
    ("Diver Watch 200m Stainless", 12999),
    ("Pocket Watch Skeleton Mechanical", 4999),
    ("Watch Roll Travel Case 5-Slot", 1999),
    ("Watch Cleaning Kit Spring Bar Tool", 699),
    ("Silicone Watch Band 42mm Quick", 499),
    ("NATO Strap Canvas Multi-Colour", 599),
    ("Leather Watch Strap Vintage 20mm", 899),
    ("Crystal Bracelet Healing Stones", 799),
    ("Beaded Bracelet Mala 108", 699),
    ("Cuff Bracelet Hammered Brass", 999),
    ("Tennis Bracelet CZ Stones", 1599),
    ("Chain Bracelet Cuban Link Silver", 2499),
    ("Charm Bracelet Sterling Silver", 3499),
    ("Men's Bead Bracelet Wood Onyx", 999),
    ("Paracord Bracelet Survival", 499),
    ("Necklace Layered Gold Dainty", 2999),
    ("Pendant Necklace Gemstone Drop", 1999),
    ("Choker Velvet Gothic", 699),
    ("Pearl Necklace Freshwater Long", 4999),
    ("Bead Necklace Boho Multi-Strand", 1299),
    ("Locket Necklace Heart Photo", 1499),
    ("Infinity Necklace Silver Script", 999),
    ("Earrings Hoop Gold Large 50mm", 1299),
    ("Stud Earrings Pearl Classic", 999),
    ("Drop Earrings Tassel Boho", 899),
    ("Ear Cuff No-Pierce Leaf", 699),
    ("Huggie Earrings Tiny Diamond", 2499),
    ("Ear Climber Crawler CZ", 1499),
    ("Threader Earrings Delicate Chain", 799),
    ("Ring Statement Cocktail CZ", 999),
    ("Signet Ring Personalised Engrave", 2499),
    ("Stacking Ring Set Thin Gold 5pc", 1799),
    ("Knuckle Rings Set Silver 4pc", 1299),
    ("Nose Ring Stud CZ Surgical", 299),
    ("Midi Ring Adjustable Boho", 499),
    ("Anklet Layered Beads Gold", 699),
    ("Toe Ring Adjustable Silver", 299),
    ("Hair Clip Claw Acetate Large", 699),
    ("Bobby Pin Set Jewelled 12-Pack", 399),
    ("Silk Scrunchie Set 5-Pack", 499),
    ("Hair Tie No-Crease Spiral 10pc", 399),
    ("Headband Padded Knotted Velvet", 599),
    ("Turban Wrap Pre-Tied Satin", 699),
    ("Scrunchie Giant Oversized Satin", 449),
    ("Key Chain Leather Tag Engraved", 699),
    ("Multi-Tool Wallet Card Credit", 999),
    ("Bottle Opener Brushed Stainless", 499),
    ("Lighter Windproof Arc Plasma", 1299),
    ("Money Clip Stainless Slim", 699),
    ("Coin Purse Leather Zip", 599),
    ("Card Holder Minimalist Front Pocket", 799),
    ("Card Case Aluminium Pop-Up", 999),
    ("Zip Card Wallet Trifold Leather", 1499),
    ("Business Card Case Stainless", 899),
    ("Umbrella Compact Windproof Auto", 1499),
    ("Travel Umbrella UV Protection", 1299),
    ("Clear Umbrella Bubble Dome", 1999),
    ("Sunscreen Stick SPF 50 Pocket", 599),
    ("Lip Balm Set Organic 4-Pack", 499),
    ("Hand Cream Travel Set 5 x 30ml", 799),
    ("Perfume Roller Ball Travel Size", 999),
    ("Cologne Solid Stick Pocket", 699),
    ("Makeup Bag Organiser Zippered", 1299),
    ("Jewellery Roll Case Velvet", 1499),
    ("Watch Box Display 6-Grid Glass", 2499),
    ("Ring Display Stand Set 12pc", 699),
    ("Necklace Stand Bust White", 799),
    ("Earring Organiser Holder Rotating", 1199),
    ("Jewellery Box Musical Ballerina", 1999),
    ("Jewellery Cleaner Ultrasonic Mini", 2499),
    ("Luggage Tag Set 2-Pack Leather", 799),
    ("Neck Pouch Security Anti-Theft", 899),
    ("Pop Socket Grip Phone Stand", 499),
    ("Phone Ring Holder Kickstand", 349),
    ("Magnetic Phone Mount Car Vent", 799),
    ("Wireless Charger Stand MagSafe", 2499),
    ("AirTag Case Keyring Leather", 699),
    ("Cable Organiser Velcro Ties 20pc", 399),
    ("Laptop Stand Portable Foldable", 2999),
    ("Phone Stand Desk Adjustable", 699),
    ("Monitor Riser Bamboo Shelf", 1999),
    ("Wrist Rest Mouse Pad Gel", 799),
    ("Mousepad Desk Mat XXL 90x40", 1299),
    ("Portable Ashtray Pocket Stainless", 399),
    ("Tie Clip Bar Silver Engravable", 699),
    ("Magnetic Bracelet Therapy Copper", 799),
    ("Fitness Resistance Bands Set 5pc", 1199),
    ("Yoga Mat Carry Strap Cork Natural", 2499),
    ("Gym Chalk Block Magnesium 8-Pack", 799),
    ("Jump Rope Speed Bearing Steel", 899),
    ("Resistance Loop Bands Set 5", 699),
]

# ── Seller pool (original 18) + 10 new discount sellers ──────────────────────
ORIGINAL_SELLER_NAMES = [
    "Apex Electronics", "Global Gadgets", "Zenith Systems", "TechHaven",
    "Prime Hardware", "Future Shop", "Nexus Gear", "Quantum Tech",
    "Elite Accessories", "Visionary Hub", "Modern Mart", "Velocity Supplies",
    "Pulse Electronics", "Stellar Connect", "Dynamic Solutions", "Orbit Tech",
    "Crystal Computing", "Infinity Gadgets",
]

DISCOUNT_SELLER_NAMES = [
    "BargainBay Store", "DealZone India", "PriceDrop Hub", "MegaSale Mart",
    "FlashDeals Pro", "ClearanceKing", "BudgetFirst Shop", "SavingsVault",
    "DiscountDuniya", "ThriftMaster India",
]

CATEGORY_IMAGES = {
    "Electronics": IMG_ELECTRONICS,
    "Fashion": IMG_FASHION,
    "Home & Kitchen": IMG_KITCHEN,
    "Accessories": IMG_ACCESSORIES,
}

CATEGORY_PRODUCTS = {
    "Electronics": ELECTRONICS_PRODUCTS,
    "Fashion": FASHION_PRODUCTS,
    "Home & Kitchen": KITCHEN_PRODUCTS,
    "Accessories": ACCESSORIES_PRODUCTS,
}

# ─────────────────────────────────────────────────────────────────────────────

def seed_market():
    print("--- Starting Massive Marketplace Seed (500 Products) ---")

    # 1. CLEAN UP
    products_collection.delete_many({})
    orders_collection.delete_many({})
    activity_logs_collection.delete_many({})
    users_collection.delete_many({"role": {"$ne": "admin"}})
    print("Deleted previous products, orders, activity logs, and non-admin users.")

    password_hash = generate_password_hash("password123")

    # 2. BUILD SELLERS

    all_sellers = []

    # Original sellers
    for i, name in enumerate(ORIGINAL_SELLER_NAMES):
        all_sellers.append({
            "name": name,
            "email": f"seller{i+1}@faircart.com",
            "password": password_hash,
            "role": "seller",
            "shop_name": name,
            "verified": True,
            "is_discount_seller": False,
            "aadhaar_number": f"12344321{1000+i}",
            "created_at": datetime.now()
        })

    # 10 NEW discount sellers — 30 % off all their products
    for j, name in enumerate(DISCOUNT_SELLER_NAMES):
        all_sellers.append({
            "name": name,
            "email": f"discount_seller{j+1}@faircart.com",
            "password": password_hash,
            "role": "seller",
            "shop_name": name,
            "verified": True,
            "is_discount_seller": True,
            "discount_pct": 30,
            "aadhaar_number": f"99887766{5000+j}",
            "created_at": datetime.now()
        })

    # 3. BUILD CUSTOMERS
    customers = []
    first_names = ["Anup","Rahul","Priya","Sara","Tom","John","Emma","Liam","David","Karan",
                   "Riya","Amit","Neha","Suresh","Pooja","Arjun","Diya","Vikas","Sneha","Ravi"]
    last_names  = ["Sharma","Verma","Smith","Jones","Doe","Kapoor","Gupta","Das","Roy","Sen",
                   "Patel","Nair","Joshi","Mehta","Reddy","Iyer","Kumar","Singh","Bose","Ghosh"]
    for i in range(150):
        customers.append({
            "name": f"{random.choice(first_names)} {random.choice(last_names)}",
            "email": f"customer{i+1}@test.com",
            "password": password_hash,
            "role": "customer",
            "created_at": datetime.now()
        })

    # 4. BUILD 500 PRODUCTS
    # Distribute: 125 products per category
    products = []
    categories = list(CATEGORY_PRODUCTS.keys())
    now = int(time.time())

    # Split sellers: original for normal, discount sellers for ~30% of products
    original_sellers = [s for s in all_sellers if not s["is_discount_seller"]]
    discount_sellers = [s for s in all_sellers if s["is_discount_seller"]]

    for cat in categories:
        items = CATEGORY_PRODUCTS[cat]          # 125 unique items
        imgs  = CATEGORY_IMAGES[cat]

        for idx, (prod_name, base_price) in enumerate(items):
            # Every 3rd product goes to a discount seller
            if idx % 3 == 1:
                seller = random.choice(discount_sellers)
                orig_price = base_price
                discounted = round(orig_price * 0.70)
                sale_price = discounted
                on_sale = True
                discount_label = "30% OFF"
            else:
                seller = random.choice(original_sellers)
                orig_price = base_price
                sale_price = base_price
                on_sale = False
                discount_label = None

            image_url = imgs[idx % len(imgs)]

            product = {
                "name": prod_name,
                "price": sale_price,
                "original_price": orig_price,
                "category": cat,
                "description": (
                    f"{prod_name} - a top-rated product in the {cat} category, "
                    f"brought to you by {seller['shop_name']}. "
                    f"{'[SALE] Currently on SALE at 30% off the regular price! ' if on_sale else ''}"
                    f"Crafted with premium materials and backed by quality assurance."
                ),
                "image_url": image_url,
                "image_urls": [image_url],
                "seller_id": seller["email"],
                "seller_name": seller["shop_name"],
                "approved": True,
                "status": "approved",
                "on_sale": on_sale,
                "discount_label": discount_label,
                "impressions": random.randint(20, 2000),
                "clicks": random.randint(0, 300),
                "rating": round(random.uniform(3.5, 5.0), 1),
                "reviews_count": random.randint(5, 500),
                "stock": random.randint(10, 200),
                "tags": [cat.lower(), "fair pick", seller["shop_name"].lower()],
                "seo_keywords": [cat.lower(), prod_name.lower(), seller["shop_name"].lower()],
                "hidden_seo_keywords": [cat.lower(), prod_name.lower(), seller["shop_name"].lower()],
                "created_at": now - random.randint(0, 60 * 24 * 3600),
                "updated_at": now,
            }
            products.append(apply_score_fields(product))

    # 5. EXECUTE INSERTS
    try:
        users_collection.insert_many(all_sellers + customers, ordered=False)
        inserted = products_collection.insert_many(products, ordered=False)

        inserted_products = []
        for inserted_id, product in zip(inserted.inserted_ids, products):
            stored_product = dict(product)
            stored_product["_id"] = inserted_id
            inserted_products.append(stored_product)

        order_statuses = ["Pending", "Shipped", "Delivered", "Delivered", "Delivered"]
        orders = []
        for i in range(300):
            product = random.choice(inserted_products)
            customer = random.choice(customers)
            qty = random.randint(1, 3)
            created_ts = now - random.randint(0, 45 * 24 * 3600)
            orders.append({
                "product_id": str(product["_id"]),
                "product_name": product["name"],
                "price": product["price"],
                "quantity": qty,
                "customer": customer["name"],
                "customer_email": customer["email"],
                "seller_id": product["seller_id"],
                "seller_name": product["seller_name"],
                "image_url": product.get("image_url", ""),
                "status": random.choice(order_statuses),
                "date": datetime.fromtimestamp(created_ts).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "created_at": created_ts,
            })
        orders_collection.insert_many(orders, ordered=False)

        activity_logs_collection.insert_many([
            {
                "type": "SEED",
                "message": "Demo marketplace seeded with fair exposure data",
                "user_email": "System",
                "user_id": "System",
                "timestamp": now,
                "date": datetime.fromtimestamp(now).strftime("%Y-%m-%d %H:%M:%S"),
            },
            {
                "type": "PRODUCT_ADD",
                "message": f"{len(products)} approved demo products are live",
                "user_email": "System",
                "user_id": "System",
                "timestamp": now,
                "date": datetime.fromtimestamp(now).strftime("%Y-%m-%d %H:%M:%S"),
            },
        ], ordered=False)

        total_sellers     = len(all_sellers)
        disc_sellers      = len(discount_sellers)
        normal_sellers    = len(original_sellers)
        sale_products     = sum(1 for p in products if p["on_sale"])
        total_products    = len(products)
        print(f"\n*** SUCCESS! ***")
        print(f"   Sellers  : {total_sellers} total ({normal_sellers} regular + {disc_sellers} discount-30%)")
        print(f"   Customers: {len(customers)}")
        print(f"   Products : {total_products} total  ({sale_products} at 30% off)")
        print(f"   Orders   : {len(orders)}")
        print(f"   Categories: {', '.join(categories)}")
        print("   Demo login password for sellers/customers: password123")
    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    seed_market()
