"""Entry point: `streamlit run app.py`."""

import streamlit as st

from core.ui import inject_css

st.set_page_config(page_title="LaLiga Match Predictor", page_icon="⚽", layout="wide")
inject_css()

pages = [
    st.Page("views/matches.py", title="Match predictions", icon="⚽", default=True),
    st.Page("views/standings.py", title="Projected standings", icon="🏆"),
    st.Page("views/model_performance.py", title="Model performance", icon="📊"),
]
st.navigation(pages).run()
