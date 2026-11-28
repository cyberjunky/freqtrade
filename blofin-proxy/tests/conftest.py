import pathlib
import sys

# Make the hyphenated project directory importable (`import blofin_proxy`).
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
