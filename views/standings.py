"""Projected final table: actual results so far + model predictions for remaining rounds."""

import plotly.express as px
import streamlit as st

from core.config import (
    CHAMPIONS_LEAGUE_SPOTS,
    CONFERENCE_LEAGUE_SPOT,
    EUROPA_LEAGUE_SPOT,
    RELEGATION_SPOTS,
)
from core.data import cumulative_points, last_played_round, load_matches, standings, team_match_points
from core.teams import display_name, logo_data_uri
from core.ui import COLORS, PLOTLY_LAYOUT, footer, header, html, team_tile

header("Projected final standings based on the model's predictions")

matches = load_matches()
last_played = last_played_round(matches)
n_rounds = int(matches["round"].max())

ctrl_method, ctrl_real = st.columns([2, 1], vertical_alignment="bottom")
with ctrl_method:
    method = st.segmented_control(
        "Projection method",
        options=["expected", "most_likely"],
        format_func={"expected": "Expected points", "most_likely": "Most likely outcome"}.get,
        default="expected",
        help="**Expected points** weights each pending match by its probabilities "
        "(3·P(win) + P(draw)), which gives realistic point totals. **Most likely outcome** "
        "assigns every pending match its single most probable result; it is easier to read "
        "but inflates the favourites, since they never drop points.",
    ) or "expected"
with ctrl_real:
    use_real = st.toggle(
        f"Use actual results for rounds 1–{last_played}",
        value=True,
        disabled=last_played == 0,
        help="Turn off to see what the model alone would have projected for the whole season.",
    ) and last_played > 0

long = team_match_points(matches, use_real_results=use_real, method=method)
table = standings(long)
evolution = cumulative_points(long)

if use_real:
    st.caption(f"Rounds 1–{last_played}: actual results · Rounds {last_played + 1}–{n_rounds}: model projection")
else:
    st.caption(f"All {n_rounds} rounds: model projection")

# --------------------------------------------------------------------------
# Headline: champion + relegation
# --------------------------------------------------------------------------
champion = table.iloc[0]
relegated = table.tail(RELEGATION_SPOTS)

col_champ, col_releg = st.columns([1, 3])
with col_champ:
    st.markdown("**🏆 Projected champion**")
    html(f"<div class='tiles'>{team_tile(champion.team, f'{champion.Pts:.0f} pts', COLORS['accent'])}</div>")
with col_releg:
    st.markdown("**🔻 Projected relegation**")
    tiles = "".join(team_tile(r.team, f"{r.Pts:.0f} pts", COLORS["AWAY_WIN"]) for r in relegated.itertuples())
    html(f"<div class='tiles'>{tiles}</div>")

# --------------------------------------------------------------------------
# Table + points evolution
# --------------------------------------------------------------------------
left, right = st.columns([1.1, 1], gap="large")


def zone(pos: int) -> tuple[str, str]:
    """(label, colour) of the qualification / relegation zone for a final position."""
    if pos <= CHAMPIONS_LEAGUE_SPOTS:
        return "Champions League", "#4da8ff"
    if pos == EUROPA_LEAGUE_SPOT:
        return "Europa League", "#fb923c"
    if pos == CONFERENCE_LEAGUE_SPOT:
        return "Conference League", "#22c55e"
    if pos > len(table) - RELEGATION_SPOTS:
        return "Relegation", "#ff4d4d"
    return "", "transparent"


def fmt(value: float) -> str:
    return f"{value:.1f}" if method == "expected" else f"{value:.0f}"


def table_html() -> str:
    rows = []
    for r in table.itertuples():
        label, color = zone(r.Pos)
        uri = logo_data_uri(r.team)
        crest = (
            f"<img src='{uri}' alt='' style='width:22px;height:22px;display:inline-block;"
            "vertical-align:middle;margin:0 8px 0 0'>" if uri else ""
        )
        rows.append(
            f"<tr><td class='pos' style='border-left:4px solid {color}' title='{label}'>{r.Pos}</td>"
            f"<td class='club' style='white-space:nowrap;text-align:left'>{crest}{display_name(r.team)}</td>"
            f"<td>{fmt(r.W)}</td><td>{fmt(r.D)}</td><td>{fmt(r.L)}</td><td class='pts'>{fmt(r.Pts)}</td></tr>"
        )
    legend = "".join(
        f"<span style='margin-right:16px;white-space:nowrap'><span style='display:inline-block;width:10px;"
        f"height:10px;border-radius:2px;margin-right:5px;background:{c}'></span>{name}</span>"
        for name, c in [("Champions League", "#4da8ff"), ("Europa League", "#fb923c"),
                        ("Conference League", "#22c55e"), ("Relegation", "#ff4d4d")]
    )
    return (
        "<table class='standings'><thead><tr><th>#</th><th>Club</th><th>W</th><th>D</th><th>L</th>"
        f"<th>Pts</th></tr></thead><tbody>{''.join(rows)}</tbody></table>"
        f"<div style='font-size:0.75rem;color:#9aa4b2;margin:8px 0 4px 0'>{legend}</div>"
    )


with left:
    st.subheader("Table")
    html(table_html())
    st.caption(
        ("W/D/L and points include expected values for pending matches. " if method == "expected" else "")
        + "Ties broken by number of wins (the model predicts outcomes, not scores, so goal difference "
        "is not available). European places are indicative: they can change with cup winners and "
        "UEFA coefficient bonuses."
    )

with right:
    st.subheader("Points evolution")
    team_keys = table["team"].tolist()
    chosen = st.multiselect(
        "Teams to compare",
        options=team_keys,
        default=team_keys[:2],
        format_func=display_name,
        max_selections=6,
    )
    data = evolution[evolution["team"].isin(chosen)].assign(Team=lambda d: d["team"].map(display_name))
    fig = px.line(
        data,
        x="round",
        y="cum_pts",
        color="Team",
        markers=True,
        labels={"round": "Round", "cum_pts": "Cumulative points"},
        color_discrete_sequence=["#00ffcc", "#ff6b6b", "#ffd93d", "#4da8ff", "#c084fc", "#fb923c"],
    )
    if use_real:
        fig.add_vline(x=last_played + 0.5, line_dash="dash", line_color="gray")
        fig.add_annotation(
            x=last_played + 0.5, y=1, yref="paper", text="predictions →",
            showarrow=False, xanchor="left", font=dict(color="gray"),
        )
    fig.update_traces(line=dict(width=2), marker=dict(size=5))
    fig.update_layout(**PLOTLY_LAYOUT, height=600, legend_title_text="", legend=dict(orientation="h", y=-0.15))
    st.plotly_chart(fig, width="stretch")

# --------------------------------------------------------------------------
# European places
# --------------------------------------------------------------------------
st.subheader("Top 6 — European places")
tiles = "".join(
    team_tile(r.team, f"{r.Pos}º · {r.Pts:.0f} pts", COLORS["accent"]) for r in table.head(6).itertuples()
)
html(f"<div class='tiles'>{tiles}</div>")

footer()
