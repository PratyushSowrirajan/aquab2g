"""
AquaWatch — Plotly Risk Gauge

Speedometer-style gauge for the overall risk score.
"""

import plotly.graph_objects as go
from config.constants import RISK_LEVELS


def build_risk_gauge(risk_score: float, title: str = "Overall Risk") -> go.Figure:
    """
    Build a Plotly gauge chart for a 0–100 risk score.

    Parameters
    ----------
    risk_score : float  0–100
    title : str

    Returns
    -------
    plotly.graph_objects.Figure
    """
    level = _score_to_level(risk_score)
    needle_color = RISK_LEVELS[level]["color"]

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=risk_score,
        number={"font": {"size": 40, "color": needle_color}, "suffix": ""},
        title={"text": title, "font": {"size": 14, "color": "#555"}},
        gauge={
            "axis": {
                "range": [0, 100],
                "tickwidth": 1,
                "tickcolor": "#aaa",
                "tickvals": [0, 25, 50, 75, 100],
                "ticktext": ["0", "25", "50", "75", "100"],
            },
            "bar": {"color": needle_color, "thickness": 0.25},
            "bgcolor": "white",
            "borderwidth": 0,
            "steps": [
                {"range": [0,  25], "color": "#d5f5e3"},   # SAFE — light green
                {"range": [25, 50], "color": "#fef9e7"},   # LOW — light yellow
                {"range": [50, 75], "color": "#fdebd0"},   # WARNING — light orange
                {"range": [75, 100],"color": "#fadbd8"},   # CRITICAL — light red
            ],
            "threshold": {
                "line": {"color": needle_color, "width": 4},
                "thickness": 0.75,
                "value": risk_score,
            },
        },
    ))

    fig.update_layout(
        height=220,
        margin=dict(l=20, r=20, t=40, b=10),
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif"),
    )
    return fig


def build_component_gauges(component_scores: dict) -> go.Figure:
    """
    Build four small gauges in a 2×2 grid for component scores.

    Parameters
    ----------
    component_scores : dict
        {"Temperature": float, "Nutrients": float,
         "Stagnation": float, "Light": float}

    Returns
    -------
    plotly.graph_objects.Figure
    """
    from plotly.subplots import make_subplots

    labels = list(component_scores.keys())
    values = list(component_scores.values())

    fig = make_subplots(
        rows=1, cols=4,
        specs=[[{"type": "indicator"}] * 4],
        subplot_titles=labels,
    )

    for i, (label, value) in enumerate(zip(labels, values), start=1):
        level = _score_to_level(value)
        color = RISK_LEVELS[level]["color"]
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=value,
                number={"font": {"size": 20, "color": color}},
                gauge={
                    "axis": {"range": [0, 100], "showticklabels": False},
                    "bar": {"color": color, "thickness": 0.3},
                    "steps": [
                        {"range": [0,  25], "color": "#d5f5e3"},
                        {"range": [25, 50], "color": "#fef9e7"},
                        {"range": [50, 75], "color": "#fdebd0"},
                        {"range": [75, 100],"color": "#fadbd8"},
                    ],
                },
            ),
            row=1, col=i,
        )

    fig.update_layout(
        height=180,
        margin=dict(l=10, r=10, t=35, b=5),
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=11),
    )
    return fig


def _score_to_level(score: float) -> str:
    for level, bounds in RISK_LEVELS.items():
        if bounds["min"] <= score < bounds["max"]:
            return level
    return "CRITICAL"
