import pickle
import pandas as pd
from pathlib import Path
import sys

TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from path_helper import backend_path

def deep_analyze(filename):
    print(f"\n--- Deep Analyzing {filename} ---")
    with Path(filename).open('rb') as f:
        data = pickle.load(f)
    
    if isinstance(data, pd.DataFrame):
        print(f"Index Head: {data.index[:5].tolist()}")
        print(f"Columns Head: {data.columns[:5].tolist()}")
        print(f"Index Type: {data.index.dtype}")
    elif isinstance(data, pd.Series):
        print(f"Index Head: {data.index[:5].tolist()}")
        print(f"Values Head: {data.values[:5].tolist()}")

if __name__ == "__main__":
    deep_analyze(backend_path("Ml", "behavior.pkl"))
    deep_analyze(backend_path("Ml", "reviews.pkl"))
