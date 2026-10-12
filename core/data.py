"""Data loading and pure analytics (no Streamlit UI code here, so it is testable)."""

import numpy as np
import pandas as pd
import streamlit as st

from core.config import GAP_THRESHOLD, OUTCOMES, PREDICTIONS_CSV, RESULTS_CSV

POINTS = {"win": 3, "draw": 1}


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def read_matches(predictions_csv=PREDICTIONS_CSV, results_csv=RESULTS_CSV) -> pd.DataFrame:
    """One row per fixture: model prediction + actual result (NaN if not played yet)."""
    preds = pd.read_csv(predictions_csv, parse_dates=["date"])
    results = pd.read_csv(results_csv, usecols=["round", "home_team", "away_team", "result"])

    matches = preds.merge(results, on=["round", "home_team", "away_team"], how="left", validate="1:1")
    matches["played"] = matches["result"].notna()
    matches["correct"] = np.where(matches["played"], matches["predicted_result"] == matches["result"], np.nan)
    matches["reliable"] = matches["gap"] > GAP_THRESHOLD
    return matches.sort_values(["round", "date", "home_team"]).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_matches() -> pd.DataFrame:
    return read_matches()


def last_played_round(matches: pd.DataFrame) -> int:
    """Highest round in which every fixture already has a result (0 if none)."""
    complete = matches.groupby("round")["played"].all()
    complete = complete[complete]
    return int(complete.index.max()) if len(complete) else 0


# ---------------------------------------------------------------------------
# Season projection & standings
# ---------------------------------------------------------------------------

def team_match_points(matches: pd.DataFrame, use_real_results: bool = True, method: str = "expected") -> pd.DataFrame:
    """Long format: one row per (team, match) with W/D/L and points.

    * ``use_real_results``: played matches count with their actual result;
      otherwise every match uses the model.
    * ``method="most_likely"``: each pending match counts as its most likely
      outcome (argmax). Simple, but it overstates favourites because it never
      lets them drop points.
    * ``method="expected"``: each pending match contributes probabilities
      (W = p_win, D = p_draw), so points are *expected points* (3·p_win + p_draw).
    """
    one_hot = {o: (matches["predicted_result"] == o).astype(float) for o in OUTCOMES}
    if method == "expected":
        model = {"HOME_WIN": matches["p_home"], "DRAW": matches["p_draw"], "AWAY_WIN": matches["p_away"]}
    elif method == "most_likely":
        model = one_hot
    else:
        raise ValueError(f"Unknown method: {method}")

    use_actual = matches["played"] if use_real_results else pd.Series(False, index=matches.index)
    prob = {o: np.where(use_actual, (matches["result"] == o).astype(float), model[o]) for o in OUTCOMES}
    source = np.where(use_actual, "actual", "predicted")

    base = matches[["round"]].assign(source=source)
    home = base.assign(team=matches["home_team"], W=prob["HOME_WIN"], D=prob["DRAW"], L=prob["AWAY_WIN"])
    away = base.assign(team=matches["away_team"], W=prob["AWAY_WIN"], D=prob["DRAW"], L=prob["HOME_WIN"])
    long = pd.concat([home, away], ignore_index=True)
    long["pts"] = POINTS["win"] * long["W"] + POINTS["draw"] * long["D"]
    return long.sort_values(["team", "round"]).reset_index(drop=True)


def standings(long: pd.DataFrame) -> pd.DataFrame:
    """League table sorted by points, then wins, then team name.

    Goal difference (LaLiga's real tie-breaker after head-to-head) is not
    available because the model predicts outcomes, not scores.
    """
    table = (
        long.groupby("team")
        .agg(P=("pts", "size"), W=("W", "sum"), D=("D", "sum"), L=("L", "sum"), Pts=("pts", "sum"))
        .reset_index()
        .sort_values(["Pts", "W", "team"], ascending=[False, False, True])
        .reset_index(drop=True)
    )
    table.insert(0, "Pos", range(1, len(table) + 1))
    return table


def cumulative_points(long: pd.DataFrame) -> pd.DataFrame:
    long = long.copy()
    long["cum_pts"] = long.groupby("team")["pts"].cumsum()
    return long


# ---------------------------------------------------------------------------
# Model evaluation (played matches only)
# ---------------------------------------------------------------------------

def evaluation_summary(matches: pd.DataFrame) -> dict:
    played = matches[matches["played"]]
    if played.empty:
        return {}

    y = played["result"].map({"AWAY_WIN": 0, "DRAW": 1, "HOME_WIN": 2}).to_numpy()
    probs = played[["p_away", "p_draw", "p_home"]].to_numpy()
    log_loss = float(-np.log(np.clip(probs[np.arange(len(y)), y], 1e-15, 1)).mean())

    reliable = played[played["reliable"]]
    uncertain = played[~played["reliable"]]
    return {
        "n_played": len(played),
        "accuracy": played["correct"].mean(),
        "baseline_home": (played["result"] == "HOME_WIN").mean(),
        "baseline_random": 1 / 3,
        "n_reliable": len(reliable),
        "accuracy_reliable": reliable["correct"].mean() if len(reliable) else np.nan,
        "accuracy_uncertain": uncertain["correct"].mean() if len(uncertain) else np.nan,
        "log_loss": log_loss,
        "log_loss_uniform": float(np.log(3)),
    }


def accuracy_by_gap(matches: pd.DataFrame, bins=(0, 0.03, 0.07, 0.12, 1.0)) -> pd.DataFrame:
    played = matches[matches["played"]].copy()
    labels = [f"{lo:.0%}–{hi:.0%}" if hi < 1 else f">{lo:.0%}" for lo, hi in zip(bins[:-1], bins[1:])]
    played["gap_bucket"] = pd.cut(played["gap"], bins=list(bins), labels=labels, include_lowest=True)
    return (
        played.groupby("gap_bucket", observed=False)["correct"]
        .agg(accuracy="mean", matches="size")
        .reset_index()
    )


def confusion(matches: pd.DataFrame) -> pd.DataFrame:
    played = matches[matches["played"]]
    return pd.crosstab(played["result"], played["predicted_result"]).reindex(
        index=OUTCOMES, columns=OUTCOMES, fill_value=0
    )
