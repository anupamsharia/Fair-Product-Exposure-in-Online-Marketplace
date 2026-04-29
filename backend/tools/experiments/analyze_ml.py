import pickle
from pathlib import Path
import sys

TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from path_helper import backend_path

def analyze_pickle(filename):
    print(f"\n--- Analyzing {filename} ---")
    path = Path(filename)
    if not path.exists():
        print("File not found")
        return
    try:
        with path.open('rb') as f:
            data = pickle.load(f)
        print(f"Type: {type(data)}")
        if isinstance(data, dict):
            print(f"Keys: {list(data.keys())[:10]}")
        elif hasattr(data, 'shape'):
            print(f"Shape: {data.shape}")
        
        # Check for model attributes
        if hasattr(data, 'predict'):
            print("Action: Found .predict() method (Model)")
        if hasattr(data, 'transform'):
            print("Action: Found .transform() method (Transformer)")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_pickle(backend_path("Ml", "behavior.pkl"))
    analyze_pickle(backend_path("Ml", "reviews.pkl"))
