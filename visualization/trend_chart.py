"""
AquaWatch — Plotly 7-Day Forecast Chart

Interactive line chart with:
  - Risk score trajectory
  - Monte Carlo confidence band (shaded)
  - WHO threshold lines (horizontal dashed)
  - Temperature subplot
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List
from config.constants import RISK_LEVELS


# WHO score equivalents for horizontal reference lines
WHO_LINES = [
    {"score": 30, "label": "WHO Moderate",  "color": "#f1c40f", "dash": "dash"},
    {"score": 55, "label": "WHO High",       "color": "#e67e22", "dash": "dash"},
    {"score": 80, "label": "WHO Very High",  "color": "#e74c3c", "dash": "dot"},
]


def build_forecast_chart(forecast: Dict) -> go.Figure:
    """
    Build a Plotly figure: risk trajectory + confidence band + WHO lines.

    Parameters
    ----------
    forecast : dict
        Output of uncertainty.compute_confidence_bands().
        Keys: dates, risk_scores, p10, p90, temperatures, precip.

    Returns
    -------
    plotly.graph_objects.Figure
    """
    dates  = forecast.get("dates", [])
    scores = forecast.get("risk_scores", [])
    p10    = forecast.get("p10", scores)
    p90    = forecast.get("p90", scores)
    temps  = forecast.get("temperatures", [])

    # Pad confidence bands if missing
    if len(p10) < len(scores):
        p10 = scores[:]
    if len(p90) < len(scores):
        p90 = scores[:]

    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.70, 0.30],
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=("7-Day Cyanobacteria Risk Score", "Air Temperature (°C)"),
    )

    # ------------------------------------------------------------------
    # Confidence band (shaded area)
    # ------------------------------------------------------------------
    fig.add_trace(
        go.Scatter(
            x=dates + dates[::-1],
            y=p90 + p10[::-1],
            fill="toself",
            fillcolor="rgba(52,152,219,0.15)",
            line=dict(color="rgba(255,255,255,0)"),
            name="80% Confidence Band",
            showlegend=True,
            hoverinfo="skip",
        ),
        row=1, col=1,
    )

    # ------------------------------------------------------------------
    # Risk score line — coloured segments
    # ------------------------------------------------------------------
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=scores,
            mode="lines+markers",
            name="Risk Score",
            line=dict(color="#3498db", width=3),
            marker=dict(
                size=8,
                color=_scores_to_colors(scores),
                line=dict(color="white", width=1.5),
            ),
            hovertemplate="<b>%{x}</b><br>Risk: %{y:.0f}/100<extra></extra>",
        ),
        row=1, col=1,
    )

    # ------------------------------------------------------------------
    # WHO threshold lines
    # ------------------------------------------------------------------
    for wl in WHO_LINES:
        fig.add_hline(
            y=wl["score"],
            line_dash=wl["dash"],
            line_color=wl["color"],
            line_width=1.5,
            annotation_text=wl["label"],
            annotation_position="top right",
            annotation_font_size=10,
            row=1, col=1,
        )

    # ------------------------------------------------------------------
    # Temperature subplot
    # ------------------------------------------------------------------
    if temps and len(temps) == len(dates):
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=temps,
                mode="lines+markers",
                name="Air Temp (°C)",
                line=dict(color="#e74c3c", width=2),
                marker=dict(size=5),
                hovertemplate="<b>%{x}</b><br>Temp: %{y:.1f}°C<extra></extra>",
            ),
            row=2, col=1,
        )
        # Optimal bloom temp reference band
        fig.add_hrect(
            y0=25, y1=35,
            fillcolor="rgba(231,76,60,0.08)",
            line_width=0,
            annotation_text="Bloom temp range",
            annotation_font_size=9,
            row=2, col=1,
        )

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    fig.update_layout(
        height=480,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )
    fig.update_yaxes(range=[0, 105], title_text="Risk Score", row=1, col=1,
                     gridcolor="#f0f0f0")
    fig.update_yaxes(title_text="°C", row=2, col=1, gridcolor="#f0f0f0")
    fig.update_xaxes(gridcolor="#f0f0f0")

    return fig


def _scores_to_colors(scores: List[float]) -> List[str]:
    """Map individual scores to risk colours."""
    colors = []
    for s in scores:
        if s < 25:
            colors.append(RISK_LEVELS["SAFE"]["color"])
        elif s < 50:
            colors.append(RISK_LEVELS["LOW"]["color"])
        elif s < 75:
            colors.append(RISK_LEVELS["WARNING"]["color"])
        else:
            colors.append(RISK_LEVELS["CRITICAL"]["color"])
    return colors
