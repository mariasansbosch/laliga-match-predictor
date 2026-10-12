"""Team display names and crest lookup.

The datasets identify teams with an upper-case key (e.g. ``"CELTA VIGO"``).
Crests live in ``assets/logos/<slug>.png`` where slug is the lower-case key
with spaces replaced by hyphens (``celta-vigo.png``).
"""

import base64
from pathlib import Path

import streamlit as st

from core.config import LOGO_DIR

TEAM_NAMES = {
    "ALAVES": "Deportivo Alavés",
    "ATHLETIC CLUB": "Athletic Club",
    "ATLETICO MADRID": "Atlético de Madrid",
    "BARCELONA": "FC Barcelona",
    "CELTA VIGO": "RC Celta",
    "ELCHE": "Elche CF",
    "ESPANYOL": "RCD Espanyol",
    "GETAFE": "Getafe CF",
    "GIRONA": "Girona FC",
    "LEVANTE": "Levante UD",
    "MALLORCA": "RCD Mallorca",
    "OSASUNA": "CA Osasuna",
    "OVIEDO": "Real Oviedo",
    "RAYO VALLECANO": "Rayo Vallecano",
    "REAL BETIS": "Real Betis",
    "REAL MADRID": "Real Madrid",
    "REAL SOCIEDAD": "Real Sociedad",
    "SEVILLA": "Sevilla FC",
    "VALENCIA": "Valencia CF",
    "VILLARREAL": "Villarreal CF",
}


def display_name(team_key: str) -> str:
    """Human-readable club name for a dataset team key."""
    return TEAM_NAMES.get(team_key, team_key.title())


def logo_path(team_key: str) -> Path | None:
    path = LOGO_DIR / f"{team_key.lower().replace(' ', '-')}.png"
    return path if path.exists() else None


@st.cache_data(show_spinner=False)
def logo_data_uri(team_key: str) -> str | None:
    """Crest as a base64 data URI (cached), or ``None`` if there is no file."""
    path = logo_path(team_key)
    if path is None:
        return None
    encoded = base64.b64encode(path.read_bytes()).decode()
    return f"data:image/png;base64,{encoded}"
