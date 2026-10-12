"""Shared styling and small HTML helpers for the Streamlit views."""

import streamlit as st

from core.config import GAP_THRESHOLD, SEASON_LABEL
from core.teams import display_name, logo_data_uri

COLORS = {
    "HOME_WIN": "#4da8ff",
    "DRAW": "#ffd93d",
    "AWAY_WIN": "#ff6b6b",
    "accent": "#00ffcc",
    "reliable": "#22c55e",
    "uncertain": "#fb923c",
    "muted": "#9aa4b2",
}

PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="white"),
    margin=dict(l=10, r=10, t=50, b=10),
)

_CSS = """
<style>
.stApp {
  background:
    radial-gradient(ellipse at 20% 0%, rgba(0,255,204,0.10), transparent 55%),
    radial-gradient(ellipse at 90% 100%, rgba(77,168,255,0.12), transparent 55%),
    #0b0f17;
}
h1.app-title { font-size: 2.6rem; font-weight: 800; text-align: center; margin-bottom: 0.2rem; }
p.app-subtitle { text-align: center; color: #c7ced9; font-size: 1.05rem; margin-bottom: 1.8rem; }

/* ---------- Generic card ---------- */
.card {
  background: rgba(20,26,36,0.85);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px;
  padding: 16px 18px;
  box-shadow: 0 10px 28px rgba(0,0,0,0.45);
  margin-bottom: 18px;
}

/* ---------- Match card ---------- */
.match-date { text-align: center; color: #9aa4b2; font-size: 0.85rem; margin-bottom: 10px; }
.match-grid { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 8px; }
.team { display: flex; flex-direction: column; align-items: center; text-align: center; }
.team img { width: 64px; height: 64px; object-fit: contain; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.6)); }
.team-name { font-weight: 700; font-size: 0.95rem; margin-top: 8px; min-height: 2.4em; display: flex; align-items: center; }
.vs { color: #888; font-weight: 800; font-size: 1.1rem; }

.prob-bar { display: flex; height: 10px; border-radius: 999px; overflow: hidden; margin: 14px 0 6px 0; }
.prob-labels { display: flex; justify-content: space-between; font-size: 0.8rem; font-weight: 600; }

.footer-row { display: flex; flex-wrap: wrap; justify-content: center; align-items: center; gap: 8px; margin-top: 14px; }
.badge {
  display: inline-block; padding: 5px 12px; border-radius: 999px; font-size: 0.75rem;
  font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; border: 1px solid;
}
.small-label { color: #9aa4b2; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.6px; }

/* ---------- Team tiles (standings page) ---------- */
.tiles { display: flex; gap: 14px; flex-wrap: wrap; margin: 6px 0 18px 0; }
.tile {
  flex: 1 1 140px; text-align: center; background: rgba(20,26,36,0.85);
  border-radius: 14px; padding: 12px 10px; border: 1px solid rgba(255,255,255,0.08);
}
.tile img { width: 52px; height: 52px; object-fit: contain; }
.tile .name { font-weight: 700; margin-top: 6px; line-height: 1.15; }
.tile .pts { margin-top: 4px; font-size: 0.9rem; }

/* ---------- Standings table ---------- */
table.standings { width: 100%; border-collapse: collapse; font-size: 0.9rem; background: rgba(20,26,36,0.85);
  border-radius: 12px; overflow: hidden; }
table.standings th { color: #00ffcc; font-weight: 700; text-align: center; padding: 8px 6px;
  border-bottom: 1px solid rgba(255,255,255,0.12); }
table.standings td { text-align: center; padding: 5px 6px; border-bottom: 1px solid rgba(255,255,255,0.05); }
table.standings td.club { text-align: left; white-space: nowrap; }
table.standings td.club img { width: 22px; height: 22px; object-fit: contain; vertical-align: middle; margin-right: 8px; }
table.standings td.pts { font-weight: 800; }

.footer { text-align: center; color: #8a93a0; font-size: 0.8rem; margin-top: 40px;
  border-top: 1px solid rgba(255,255,255,0.08); padding-top: 14px; }
</style>
"""


def html(markup: str) -> None:
    """Render raw HTML via st.markdown.

    Lines are stripped because Markdown treats 4-space-indented lines as code
    blocks, which would print the HTML instead of rendering it.
    """
    compact = " ".join(line.strip() for line in markup.splitlines())
    st.markdown(compact, unsafe_allow_html=True)


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def header(subtitle: str) -> None:
    html(f"""
        <h1 class="app-title">LaLiga {SEASON_LABEL} · Match Outcome Predictor</h1>
        <p class="app-subtitle">{subtitle}</p>
    """)


def footer() -> None:
    html(f"""
        <div class="footer">
            CatBoost multiclass model · public LaLiga match data · built with Streamlit<br>
            <b>GAP</b> = probability of the predicted outcome minus the second most likely one.
            Predictions with GAP &gt; {GAP_THRESHOLD:.0%} are flagged as <i>reliable</i>.
        </div>
    """)


def badge(text: str, color: str) -> str:
    return (
        f"<span class='badge' style='color:{color}; border-color:{color}66; "
        f"background:{color}22'>{text}</span>"
    )


def team_block(team_key: str) -> str:
    uri = logo_data_uri(team_key)
    img = f"<img src='{uri}' alt=''>" if uri else "<div style='height:64px'></div>"
    return f"<div class='team'>{img}<div class='team-name'>{display_name(team_key)}</div></div>"


def team_tile(team_key: str, caption: str, color: str) -> str:
    uri = logo_data_uri(team_key)
    img = f"<img src='{uri}' alt=''>" if uri else ""
    return (
        f"<div class='tile' style='box-shadow:0 0 14px {color}33'>{img}"
        f"<div class='name'>{display_name(team_key)}</div>"
        f"<div class='pts' style='color:{color}'>{caption}</div></div>"
    )
