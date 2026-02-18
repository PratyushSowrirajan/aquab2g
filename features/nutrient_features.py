"""
AquaWatch — Nutrient Loading Feature Engineering

Proxy model: land_use × rainfall × season → estimated nutrient load.
Source: Beaulac & Reckhow (1982) nutrient export coefficients.
"""

import numpy as np
from datetime import datetime
from typing import Dict
from config.constants import LAND_USE_NUTRIENT_EXPORT, RAINFALL


def compute_nutrient_features(
    land_use: Dict,
    precip_features: Dict,
    lat: float,
) -> Dict:
    """
    Estimate nutrient loading from land use + rainfall + season.
    We cannot measure N/P directly — this is a proxy model.
    """
    ag_pct = land_use.get("agricultural_pct", 0)
    urban_pct = land_use.get("urban_pct", 0)
    forest_pct = land_use.get("forest_pct", 0)
    wetland_pct = land_use.get("wetland_pct", 0)

    # Land-use nutrient export coefficient (Beaulac & Reckhow 1982)
    land_coeff = (
        ag_pct * LAND_USE_NUTRIENT_EXPORT["cropland"]
        + urban_pct * LAND_USE_NUTRIENT_EXPORT["urban"]
        + forest_pct * LAND_USE_NUTRIENT_EXPORT["forest"]
        + wetland_pct * LAND_USE_NUTRIENT_EXPORT["wetland"]
    ) / 100.0

    # Rainfall delivery mechanism
    rainfall_48h = precip_features.get("rainfall_48h", 0)
    days_since_rain = precip_features.get("days_since_significant_rain", 0)
    first_flush = precip_features.get("first_flush_event", 0)

    if first_flush >= 0.6:
        delivery_score = 0.90
    elif rainfall_48h >= RAINFALL["heavy_mm"]:
        delivery_score = 0.70
    elif precip_features.get("rainfall_7d", 0) > 30:
        delivery_score = 0.50
    elif rainfall_48h >= RAINFALL["significant_mm"]:
        delivery_score = 0.30
    else:
        delivery_score = 0.15

    # Seasonal weight
    month = datetime.now().month
    is_southern = lat < 0
    if is_southern:
        month = (month + 6 - 1) % 12 + 1  # Shift 6 months

    if 4 <= month <= 9:
        season_weight = 1.0   # Growing season
        season_label = "Growing season"
    elif month in (10, 11):
        season_weight = 0.8   # Post-harvest
        season_label = "Post-harvest"
    else:
        season_weight = 0.3   # Winter
        season_label = "Winter (low activity)"

    # Combined nutrient loading score (0-100)
    nutrient_score = land_coeff * delivery_score * season_weight * 100
    nutrient_score = round(min(nutrient_score, 100), 1)

    factors = []
    if ag_pct > 40:
        factors.append(f"{ag_pct:.0f}% agricultural land — high fertilizer runoff potential")
    if urban_pct > 40:
        factors.append(f"{urban_pct:.0f}% urban land — sewage/lawn fertilizer runoff")
    if first_flush >= 0.6:
        factors.append("First flush event delivering accumulated nutrients to water body")
    if season_weight >= 0.8:
        factors.append(f"Season: {season_label} — elevated nutrient availability")

    return {
        "land_use_coefficient": round(land_coeff, 3),
        "delivery_score": round(delivery_score, 2),
        "season_weight": season_weight,
        "season_label": season_label,
        "nutrient_score": nutrient_score,
        "agricultural_pct": ag_pct,
        "urban_pct": urban_pct,
        "factors": factors,
    }
