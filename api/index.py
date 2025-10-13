# api/index.py
from pathlib import Path
import sys

# ensure project root is in Python path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from main import app  # app is created in main.py
