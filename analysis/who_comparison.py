"""
AquaWatch — WHO Threshold Comparison Formatter

Maps risk score / cells/mL to formatted WHO output for dashboard display.
"""

from typing import Dict
from config.constants import WHO_CYANO_THRESHOLDS, WHO_SEVERITY_LABELS, RISK_LEVELS


def format_who_comparison(
    risk_score: float,
    estimated_cells: int,
    who_severity: str,
) -> Dict:
    """
    Format WHO comparison data for dashboard display.

    Returns
    -------
    dict with display-ready strings, colours, and threshold proximity.
    """
    thresholds = [
        {"label": "WHO Low",       "cells": WHO_CYANO_THRESHOLDS["low"],      "score": 30, "color": "#2ecc71"},
        {"label": "WHO Moderate",  "cells": WHO_CYANO_THRESHOLDS["moderate"], "score": 55, "color": "#f1c40f"},
        {"label": "WHO High",      "cells": WHO_CYANO_THRESHOLDS["high"],     "score": 80, "color": "#e74c3c"},
    ]

    # Next threshold the current reading is approaching
    next_threshold = None
    for t in thresholds:
        if estimated_cells < t["cells"]:
            next_threshold = t
            break

    if next_threshold:
        gap_cells = next_threshold["cells"] - estimated_cells
        gap_pct   = round(estimated_cells / next_threshold["cells"] * 100, 1)
        proximity_text = (
            f"{estimated_cells:,} cells/mL — "
            f"{gap_pct}% of {next_threshold['label']} threshold "
            f"({next_threshold['cells']:,} cells/mL)"
        )
    else:
        proximity_text = (
            f"{estimated_cells:,} cells/mL — EXCEEDS all WHO thresholds"
        )

    level_info = RISK_LEVELS.get(
        _severity_to_level(who_severity),
        RISK_LEVELS["SAFE"]
    )

    return {
        "who_severity": who_severity,
        "who_label": WHO_SEVERITY_LABELS.get(who_severity, "Unknown"),
        "estimated_cells": estimated_cells,
        "estimated_cells_formatted": f"{estimated_cells:,}",
        "proximity_text": proximity_text,
        "risk_color": level_info["color"],
        "risk_emoji": level_info["emoji"],
        "thresholds": thresholds,
        "next_threshold": next_threshold,
        "risk_score": round(risk_score, 1),
    }


def _severity_to_level(severity: str) -> str:
    mapping = {
        "low": "SAFE",
        "moderate": "LOW",
        "high": "WARNING",
        "very_high": "CRITICAL",
    }
    return mapping.get(severity, "SAFE")
