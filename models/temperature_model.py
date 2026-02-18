"""
AquaWatch — Model 1: Temperature Anomaly Score

Combines z-score statistical anomaly with absolute biological thresholds
and warming trend to produce a 0-100 temperature risk score.

Sources:
  Paerl & Huisman (2008) — "Blooms Like It Hot", Science 320(5872)
  Robarts & Zohary (1987) — Temperature response curves
"""

import numpy as np
from scipy.special import expit
from typing import Dict
from config.constants import BLOOM_TEMP, TEMP_RESPONSE


def compute_temperature_score(temp_features: Dict) -> Dict:
    """
    Compute temperature anomaly risk score (0–100).

    Parameters
    ----------
    temp_features : dict
        Output of ``compute_temperature_features()`` from feature pipeline.

    Returns
    -------
    dict with keys: score, z_score, anomaly_c, percentile, water_temp,
                    warming_trend, absolute_bracket, factors
    """
    water_temp     = temp_features.get("water_temp", 20.0)
    z_score        = temp_features.get("z_score", 0.0)
    percentile     = temp_features.get("percentile", 50.0)
    warming_trend  = temp_features.get("warming_trend_per_day", 0.0)
    trend_sig      = temp_features.get("trend_significant", False)
    temp_anomaly   = temp_features.get("temp_anomaly_c", 0.0)

    # ---------------------------------------------------------------
    # 1. Absolute biological bracket score (Paerl & Huisman 2008)
    # ---------------------------------------------------------------
    t = water_temp
    if t < BLOOM_TEMP["minimum_growth"]:
        bracket_score = 5.0
    elif t < BLOOM_TEMP["accelerated"]:
        bracket_score = 20.0 + (t - BLOOM_TEMP["minimum_growth"]) / (
            BLOOM_TEMP["accelerated"] - BLOOM_TEMP["minimum_growth"]
        ) * 20.0
    elif t < BLOOM_TEMP["optimal_min"]:
        bracket_score = 40.0 + (t - BLOOM_TEMP["accelerated"]) / (
            BLOOM_TEMP["optimal_min"] - BLOOM_TEMP["accelerated"]
        ) * 25.0
    elif t < BLOOM_TEMP["peak"]:
        bracket_score = 65.0 + (t - BLOOM_TEMP["optimal_min"]) / (
            BLOOM_TEMP["peak"] - BLOOM_TEMP["optimal_min"]
        ) * 25.0
    elif t < BLOOM_TEMP["optimal_max"]:
        bracket_score = 90.0 + (t - BLOOM_TEMP["peak"]) / (
            BLOOM_TEMP["optimal_max"] - BLOOM_TEMP["peak"]
        ) * 5.0
    else:
        # Above 35°C — some stress, slightly lower
        bracket_score = max(80.0, 95.0 - (t - BLOOM_TEMP["optimal_max"]) * 3.0)

    bracket_score = float(np.clip(bracket_score, 0, 100))

    # ---------------------------------------------------------------
    # 2. Z-score anomaly component
    # ---------------------------------------------------------------
    # sigmoid: z=0 → 50, z=+2 → ~88, z=-2 → ~12
    z_component = float(expit(0.8 * z_score)) * 100

    # ---------------------------------------------------------------
    # 3. Combined base score (weighted)
    # ---------------------------------------------------------------
    base_score = 0.60 * bracket_score + 0.40 * z_component

    # ---------------------------------------------------------------
    # 4. Warming trend bonus
    # ---------------------------------------------------------------
    trend_bonus = 0.0
    if warming_trend > 0.5 and trend_sig:
        trend_bonus = min(warming_trend * 12.0, 20.0)
    elif warming_trend > 0.3 and trend_sig:
        trend_bonus = min(warming_trend * 8.0, 12.0)

    # ---------------------------------------------------------------
    # 5. High percentile bonus
    # ---------------------------------------------------------------
    percentile_bonus = 0.0
    if percentile > 95:
        percentile_bonus = 10.0
    elif percentile > 90:
        percentile_bonus = 5.0

    final_score = float(np.clip(base_score + trend_bonus + percentile_bonus, 0, 100))

    # ---------------------------------------------------------------
    # Contextual factors
    # ---------------------------------------------------------------
    factors = list(temp_features.get("factors", []))
    if not factors:
        if water_temp >= BLOOM_TEMP["optimal_min"]:
            factors.append(
                f"Water temp {water_temp}°C in optimal bloom range "
                f"({BLOOM_TEMP['optimal_min']}–{BLOOM_TEMP['optimal_max']}°C)"
            )
        if z_score > 1.0:
            factors.append(
                f"Temperature {temp_anomaly:+.1f}°C above seasonal baseline (z={z_score:.1f})"
            )

    return {
        "score": round(final_score, 1),
        "z_score": z_score,
        "anomaly_c": temp_anomaly,
        "percentile": percentile,
        "water_temp": water_temp,
        "warming_trend_per_day": warming_trend,
        "absolute_bracket": round(bracket_score, 1),
        "z_component": round(z_component, 1),
        "trend_bonus": round(trend_bonus, 1),
        "factors": factors,
    }
