"""Round-by-round match cards: model probabilities, and actual result once played."""

import streamlit as st

from core.config import GAP_THRESHOLD, OUTCOME_LABELS
from core.data import last_played_round, load_matches
from core.ui import COLORS, badge, footer, header, html, team_block

header("Round-by-round predictions from a machine-learning model, compared with actual results")

matches = load_matches()
last_played = last_played_round(matches)
rounds = sorted(matches["round"].unique())
next_round = min(last_played + 1, max(rounds))


def round_label(r: int) -> str:
    return f"Round {r} · played" if r <= last_played else f"Round {r} · upcoming"


col_select, col_summary = st.columns([1, 3], vertical_alignment="bottom")
with col_select:
    selected = st.selectbox("Round", rounds, index=rounds.index(next_round), format_func=round_label)

round_df = matches[matches["round"] == selected]
# For later rounds the dataset only has one placeholder date per round, not real kick-off times.
exact_times = round_df["date"].nunique() > 1

with col_summary:
    if round_df["played"].all():
        hits = int(round_df["correct"].sum())
        st.markdown(f"**{hits}/{len(round_df)}** predictions correct in round {selected}.")
    else:
        n_rel = int(round_df["reliable"].sum())
        st.markdown(
            f"**{n_rel}/{len(round_df)}** predictions in round {selected} are flagged as reliable "
            f"(GAP > {GAP_THRESHOLD:.0%})."
        )
    if not exact_times:
        st.caption(f"Matchday of {round_df['date'].iloc[0]:%d %b %Y} · exact kick-off times not available")


def probability_bar(row) -> str:
    segments = "".join(
        f"<div style='width:{getattr(row, col) * 100:.1f}%; background:{COLORS[key]}'></div>"
        for col, key in [("p_home", "HOME_WIN"), ("p_draw", "DRAW"), ("p_away", "AWAY_WIN")]
    )
    labels = (
        f"<span style='color:{COLORS['HOME_WIN']}'>Home {row.p_home:.0%}</span>"
        f"<span style='color:{COLORS['DRAW']}'>Draw {row.p_draw:.0%}</span>"
        f"<span style='color:{COLORS['AWAY_WIN']}'>Away {row.p_away:.0%}</span>"
    )
    return f"<div class='prob-bar'>{segments}</div><div class='prob-labels'>{labels}</div>"


def match_card(row) -> str:
    predicted = badge(OUTCOME_LABELS[row.predicted_result], COLORS[row.predicted_result])

    if row.played:
        actual = badge(OUTCOME_LABELS[row.result], COLORS[row.result])
        verdict = (
            badge("✓ Correct", COLORS["reliable"]) if row.correct else badge("✗ Missed", COLORS["muted"])
        )
        status = (
            f"<div><div class='small-label'>Predicted</div>{predicted}</div>"
            f"<div><div class='small-label'>Actual</div>{actual}</div>"
            f"<div><div class='small-label'>&nbsp;</div>{verdict}</div>"
        )
    else:
        reliability = (
            badge("Reliable", COLORS["reliable"]) if row.reliable else badge("Uncertain", COLORS["uncertain"])
        )
        status = (
            f"<div><div class='small-label'>Prediction</div>{predicted}</div>"
            f"<div><div class='small-label'>GAP {row.gap:.1%}</div>{reliability}</div>"
        )

    date = f"<div class='match-date'>{row.date:%a %d %b %Y · %H:%M}</div>" if exact_times else ""
    return f"""
        <div class="card">
            {date}
            <div class="match-grid">
                {team_block(row.home_team)}
                <div class="vs">VS</div>
                {team_block(row.away_team)}
            </div>
            {probability_bar(row)}
            <div class="footer-row" style="gap:18px; text-align:center">{status}</div>
        </div>
    """


rows = list(round_df.itertuples(index=False))
for i in range(0, len(rows), 2):
    left, right = st.columns(2, gap="large")
    with left:
        html(match_card(rows[i]))
    if i + 1 < len(rows):
        with right:
            html(match_card(rows[i + 1]))

footer()
