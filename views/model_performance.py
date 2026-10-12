"""How well did the model do on the matches that have already been played?"""

import plotly.express as px
import streamlit as st

from core.config import GAP_THRESHOLD, OUTCOME_LABELS
from core.data import accuracy_by_gap, confusion, evaluation_summary, last_played_round, load_matches
from core.ui import COLORS, PLOTLY_LAYOUT, footer, header

header("Model evaluation against actual results")

matches = load_matches()
summary = evaluation_summary(matches)

if not summary:
    st.info("No matches have been played yet, so there is nothing to evaluate.")
    st.stop()

last_played = last_played_round(matches)
st.caption(f"Evaluated on the {summary['n_played']} matches of rounds 1–{last_played}.")

c1, c2, c3, c4 = st.columns(4)
c1.metric(
    "Accuracy",
    f"{summary['accuracy']:.1%}",
    f"{summary['accuracy'] - summary['baseline_home']:+.1%} vs. always 'home win'",
)
c2.metric(
    "Baseline: always home win",
    f"{summary['baseline_home']:.1%}",
    help="Naive benchmark: predicting a home win for every match. Random guessing gives 33.3%.",
)
c3.metric(
    f"Accuracy when GAP > {GAP_THRESHOLD:.0%}",
    f"{summary['accuracy_reliable']:.1%}",
    f"{summary['n_reliable']} of {summary['n_played']} matches",
    delta_color="off",
)
c4.metric(
    "Log loss",
    f"{summary['log_loss']:.3f}",
    f"{summary['log_loss'] - summary['log_loss_uniform']:+.3f} vs. uniform guess",
    delta_color="inverse",
    help="Measures the quality of the predicted probabilities (lower is better). "
    "Assigning 1/3 to each outcome gives 1.099.",
)

st.divider()
left, right = st.columns(2, gap="large")

with left:
    st.subheader("Accuracy by GAP")
    st.caption("The larger the gap between the top two probabilities, the more often the model is right.")
    by_gap = accuracy_by_gap(matches)
    fig = px.bar(
        by_gap,
        x="gap_bucket",
        y="accuracy",
        text=[f"{a:.0%} (n={n})" for a, n in zip(by_gap["accuracy"], by_gap["matches"])],
        labels={"gap_bucket": "GAP between top two probabilities", "accuracy": "Accuracy"},
        color_discrete_sequence=[COLORS["accent"]],
    )
    fig.add_hline(
        y=summary["baseline_home"], line_dash="dash", line_color="gray",
        annotation_text="always 'home win'", annotation_position="top left",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(**PLOTLY_LAYOUT, yaxis_tickformat=".0%", yaxis_range=[0, 1])
    st.plotly_chart(fig, width="stretch")

cm = confusion(matches)
with right:
    st.subheader("Confusion matrix")
    st.caption("Rows: actual result · Columns: predicted result")
    fig = px.imshow(
        cm.rename(index=OUTCOME_LABELS, columns=OUTCOME_LABELS),
        text_auto=True,
        color_continuous_scale="Teal",
        aspect="auto",
        labels=dict(x="Predicted", y="Actual", color="Matches"),
    )
    fig.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False)
    st.plotly_chart(fig, width="stretch")

st.subheader("Accuracy per round")
per_round = matches[matches["played"]].groupby("round")["correct"].mean().rename("accuracy").reset_index()
fig = px.bar(
    per_round, x="round", y="accuracy",
    labels={"round": "Round", "accuracy": "Accuracy"},
    color_discrete_sequence=[COLORS["HOME_WIN"]],
)
fig.add_hline(
    y=summary["accuracy"], line_dash="dash", line_color=COLORS["accent"],
    annotation_text=f"overall {summary['accuracy']:.1%}", annotation_position="top left",
)
fig.update_layout(**PLOTLY_LAYOUT, yaxis_tickformat=".0%", yaxis_range=[0, 1], height=320)
st.plotly_chart(fig, width="stretch")

draws_hit, draws_total = int(cm.loc["DRAW", "DRAW"]), int(cm.loc["DRAW"].sum())
st.info(
    f"Draws are the hardest outcome to predict — a well-known challenge in football forecasting: "
    f"the model got {draws_hit} of {draws_total} actual draws right. Predictions with a small GAP do "
    f"no better than the naive baseline, which is exactly why the app flags them as *uncertain*."
)

footer()
