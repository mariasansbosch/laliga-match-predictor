import pandas as pd
import pytest

from core.data import evaluation_summary, read_matches, standings, team_match_points


@pytest.fixture
def tiny(tmp_path):
    preds = pd.DataFrame({
        "round": [1, 1, 2, 2],
        "date": ["2025-08-15 17:00"] * 4,
        "home_team": ["A", "C", "B", "D"],
        "away_team": ["B", "D", "C", "A"],
        "predicted_result": ["HOME_WIN", "DRAW", "AWAY_WIN", "HOME_WIN"],
        "p_home": [0.6, 0.35, 0.2, 0.5],
        "p_draw": [0.2, 0.40, 0.3, 0.3],
        "p_away": [0.2, 0.25, 0.5, 0.2],
        "confidence": [0.6, 0.40, 0.5, 0.5],
        "gap": [0.4, 0.05, 0.2, 0.2],
    })
    results = pd.DataFrame({
        "round": [1, 1], "date": ["2025-08-15 17:00"] * 2,
        "home_team": ["A", "C"], "away_team": ["B", "D"], "result": ["HOME_WIN", "AWAY_WIN"],
    })
    p, r = tmp_path / "p.csv", tmp_path / "r.csv"
    preds.to_csv(p, index=False)
    results.to_csv(r, index=False)
    return read_matches(p, r)


def test_merge_flags_played_and_correct(tiny):
    assert tiny["played"].tolist() == [True, True, False, False]
    assert tiny.loc[tiny["played"], "correct"].tolist() == [1.0, 0.0]


def test_most_likely_uses_actual_results_first(tiny):
    long = team_match_points(tiny, use_real_results=True, method="most_likely")
    table = standings(long).set_index("team")
    # Round 1 (actual): A beats B, D wins at C.
    # Round 2 (predicted): C wins at B, D beats A.  ->  D 6, A 3, C 3, B 0
    assert table["Pts"].to_dict() == {"D": 6, "A": 3, "C": 3, "B": 0}
    assert table.loc["D", "Pos"] == 1
    assert table["P"].eq(2).all()
    assert set(long.loc[long["round"] == 1, "source"]) == {"actual"}


def test_expected_points_use_probabilities(tiny):
    long = team_match_points(tiny, use_real_results=True, method="expected")
    d_round2 = long[(long["team"] == "D") & (long["round"] == 2)]
    assert d_round2["pts"].iloc[0] == pytest.approx(3 * 0.5 + 0.3)


@pytest.mark.parametrize("method", ["expected", "most_likely"])
def test_total_points_consistent(tiny, method):
    long = team_match_points(tiny, use_real_results=False, method=method)
    draw_mass = tiny["p_draw"].sum() if method == "expected" else (tiny["predicted_result"] == "DRAW").sum()
    assert standings(long)["Pts"].sum() == pytest.approx(3 * len(tiny) - draw_mass)


def test_evaluation_summary(tiny):
    s = evaluation_summary(tiny)
    assert s["n_played"] == 2
    assert s["accuracy"] == pytest.approx(0.5)
