from pathlib import Path
import sys

TOOLS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = TOOLS_DIR.parent


def ensure_backend_on_path():
    backend_path = str(BACKEND_DIR)
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    return BACKEND_DIR


def backend_path(*parts):
    return BACKEND_DIR.joinpath(*parts)
