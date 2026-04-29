import pickle
import pandas as pd
from pathlib import Path
import sys

TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from path_helper import backend_path

def main():
    behavior_path = backend_path("Ml", "behavior.pkl")
    
    print(f"Behavior path: {behavior_path}")
    print(f"Exists: {behavior_path.exists()}")
    
    if not behavior_path.exists():
        print("Behavior.pkl not found!")
        return
    
    try:
        with behavior_path.open('rb') as f:
            data = pickle.load(f)
        
        print(f"\nType: {type(data)}")
        
        if isinstance(data, pd.DataFrame):
            print(f"Shape: {data.shape}")
            print(f"Index type: {type(data.index[0]) if len(data.index) > 0 else 'Empty'}")
            print(f"Sample index values: {list(data.index[:5]) if len(data.index) > 0 else 'Empty'}")
            print(f"Columns: {list(data.columns[:5]) if len(data.columns) > 0 else 'Empty'}")
            
            # Check if it's a similarity matrix
            print(f"\nIs square matrix? {data.shape[0] == data.shape[1]}")
            if data.shape[0] > 0 and data.shape[1] > 0:
                print(f"Sample value at [0,0]: {data.iloc[0,0]}")
                print(f"Sample value at [0,1]: {data.iloc[0,1]}")
        else:
            print(f"Data is not a DataFrame. Attributes: {dir(data)}")
            
    except Exception as e:
        print(f"Error loading behavior.pkl: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
