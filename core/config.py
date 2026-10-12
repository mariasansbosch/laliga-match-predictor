"""Project-wide paths and constants."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
LOGO_DIR = ROOT / "assets" / "logos"

PREDICTIONS_CSV = DATA_DIR / "predictions_2025_26.csv"
RESULTS_CSV = DATA_DIR / "results_2025_26.csv"

SEASON_LABEL = "2025–26"

OUTCOMES = ["HOME_WIN", "DRAW", "AWAY_WIN"]
OUTCOME_LABELS = {"HOME_WIN": "Home win", "DRAW": "Draw", "AWAY_WIN": "Away win"}

# A prediction is flagged as "reliable" when the probability of the predicted
# outcome beats the runner-up by more than this margin (see README: GAP).
GAP_THRESHOLD = 0.07

# LaLiga 2025–26 qualification / relegation slots (by final position).
CHAMPIONS_LEAGUE_SPOTS = 4
EUROPA_LEAGUE_SPOT = 5
CONFERENCE_LEAGUE_SPOT = 6
RELEGATION_SPOTS = 3
