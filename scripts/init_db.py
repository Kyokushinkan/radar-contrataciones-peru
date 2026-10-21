from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.db import initialize, DB_PATH
initialize()
print(f"DB_INITIALIZED={DB_PATH}")
