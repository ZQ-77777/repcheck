"""Shared test setup: import path and example locations."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
INPUTS = ROOT / "examples" / "inputs"
CACHE = ROOT / "tests" / "fixtures" / "cache"   # frozen test answers; examples/cache holds demo answers
E1 = INPUTS / "e1_coverage_investment.pdf"
E2 = INPUTS / "e2_board_payout.pdf"
SCANNED = INPUTS / "f1_scanned.pdf"
