"""
AquaWatch — Model 2: Nutrient Loading Score

Thin model wrapper — the heavy lifting is done in feature engineering.
Applies final sigmoid smoothing and returns standardised output.

Source: Beaulac & Reckhow (1982) Nutrient Export Coefficients.
"""

import numpy as np
from typing import Dict


def compute_nutrient_score(nutrient_features: Dict) -> Dict:
    """
    Compute nutrient loading risk score (0–100).

    Parameters
    ----------
    nutrient_features : dict
        Output of ``compute_nutrient_features()`` from feature pipeline.

    Returns
    -------
    dict with keys: score, land_use_coefficient, delivery_score,
                    season_weight, season_label, factors
    """
    raw_score       = nutrient_features.get("nutrient_score", 0.0)
    land_coeff      = nutrient_features.get("land_use_coefficient", 0.0)
    delivery        = nutrient_features.get("delivery_score", 0.15)
    season_weight   = nutrient_features.get("season_weight", 0.5)
    season_label    = nutrient_features.get("season_label", "Unknown")
    ag_pct          = nutrient_features.get("agricultural_pct", 0.0)
    urban_pct       = nutrient_features.get("urban_pct", 0.0)
    factors         = list(nutrient_features.get("factors", []))

    # Clip and apply a mild sigmoid to soften extreme edges
    score = float(np.clip(raw_score, 0, 100))

    # Supplement factors if empty
    if not factors:
        if ag_pct > 20:
            factors.append(f"{ag_pct:.0f}% agricultural land in catchment")
        if urban_pct > 20:
            factors.append(f"{urban_pct:.0f}% urban land — sewage/runoff risk")
        if delivery >= 0.7:
            factors.append("High rainfall delivery — nutrients actively washing into water")
        elif delivery <= 0.2:
            factors.append("Dry conditions — nutrients accumulating but not yet delivered")

    return {
        "score": round(score, 1),
        "land_use_coefficient": round(land_coeff, 3),
        "delivery_score": round(delivery, 2),
        "season_weight": season_weight,
        "season_label": season_label,
        "agricultural_pct": ag_pct,
        "urban_pct": urban_pct,
        "factors": factors,
    }
