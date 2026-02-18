"""
AquaWatch — Component Breakdown Chart

Horizontal bar chart showing contribution of each risk factor
and a Monod kinetics factor chart showing individual growth limiters.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict
from config.constants import RISK_LEVELS


def build_component_bar(component_scores: Dict) -> go.Figure:
    """
    Horizontal bar chart: Temperature / Nutrients / Stagnation / Light.

    Parameters
    ----------
    component_scores : dict  {"Temperature": float, ...}

    Returns
    -------
    plotly.graph_objects.Figure
    """
    labels = list(component_scores.keys())
    values = [component_scores[k] for k in labels]
    colors = [_score_color(v) for v in values]

    fig = go.Figure(go.Bar(
        x=values,
        y=labels,
        orientation="h",
        marker=dict(color=colors, line=dict(color="white", width=1)),
        text=[f"{v:.0f}" for v in values],
        textposition="outside",
        hovertemplate="<b>%{y}</b>: %{x:.0f}/100<extra></extra>",
    ))

    # Reference lines at WHO score thresholds
    for x_val, label in [(30, "Moderate"), (55, "High"), (80, "Very High")]:
        fig.add_vline(
            x=x_val,
            line_dash="dot",
            line_color="#bbb",
            line_width=1,
            annotation_text=label,
            annotation_position="top",
            annotation_font_size=9,
        )

    fig.update_layout(
        xaxis=dict(range=[0, 110], title="Score (0–100)", gridcolor="#f5f5f5"),
        yaxis=dict(title=""),
        height=230,
        margin=dict(l=10, r=20, t=15, b=30),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=12),
        showlegend=False,
    )
    return fig


def build_monod_factors_chart(growth_rate: Dict) -> go.Figure:
    """
    Radar / bar chart showing the four Monod limitation factors (0–1).

    Parameters
    ----------
    growth_rate : dict
        Output of ``compute_growth_rate()``.

    Returns
    -------
    plotly.graph_objects.Figure
    """
    factor_keys = {
        "f(T) Temperature": growth_rate.get("f_temperature", 0),
        "f(N) Nutrients":   growth_rate.get("f_nutrients", 0),
        "f(L) Light":       growth_rate.get("f_light", 0),
        "f(S) Stagnation":  growth_rate.get("f_stagnation", 0),
    }
    labels = list(factor_keys.keys())
    values = [v * 100 for v in factor_keys.values()]
    colors = [_score_color(v) for v in values]

    mu     = growth_rate.get("mu_per_day", 0.0)
    dbl    = growth_rate.get("doubling_time_hours")
    dbl_txt = f"{dbl:.0f}h" if dbl else "No growth"

    fig = go.Figure(go.Bar(
        x=labels,
        y=values,
        marker=dict(color=colors),
        text=[f"{v:.0f}%" for v in values],
        textposition="outside",
        hovertemplate="<b>%{x}</b>: %{y:.0f}%<extra></extra>",
    ))

    fig.update_layout(
        title=dict(
            text=f"Monod Growth Factors — µ={mu:.3f}/day · Doubling: {dbl_txt}",
            font=dict(size=12),
            x=0,
        ),
        yaxis=dict(range=[0, 115], title="Limitation Factor (%)", gridcolor="#f5f5f5"),
        xaxis=dict(title=""),
        height=250,
        margin=dict(l=10, r=10, t=45, b=20),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=11),
        showlegend=False,
    )
    return fig


def _score_color(score: float) -> str:
    for level, bounds in RISK_LEVELS.items():
        if bounds["min"] <= score < bounds["max"]:
            return bounds["color"]
    return RISK_LEVELS["CRITICAL"]["color"]
