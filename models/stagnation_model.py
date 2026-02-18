"""
AquaWatch — Model 3: Stagnation Index

Thin model wrapper around stagnation features.
Wind mixing + hydrological stagnation + thermal stratification.

Source: Huisman et al. (2004) "Changes in Turbulent Mixing" — Ecology 85(11)
"""

import numpy as np
from typing import Dict


def compute_stagnation_score(stagnation_features: Dict) -> Dict:
    """
    Compute hydrological stagnation risk score (0–100).

    Parameters
    ----------
    stagnation_features : dict
        Output of ``compute_stagnation_features()`` from feature pipeline.

    Returns
    -------
    dict with keys: score, wind_mixing_score, hydro_stagnation,
                    stratification_score, avg_wind_7d, diurnal_temp_range, factors
    """
    score         = stagnation_features.get("stagnation_score", 50.0)
    wind_mix      = stagnation_features.get("wind_mixing_score", 0.5)
    hydro         = stagnation_features.get("hydro_stagnation", 0.5)
    strat         = stagnation_features.get("stratification_score", 0.3)
    avg_wind      = stagnation_features.get("avg_wind_7d", 10.0)
    diurnal       = stagnation_features.get("diurnal_temp_range", 8.0)
    factors       = list(stagnation_features.get("factors", []))

    score = float(np.clip(score, 0, 100))

    if not factors:
        if wind_mix >= 0.7:
            factors.append(f"Low wind ({avg_wind:.0f} km/h) — insufficient mixing")
        if hydro >= 0.7:
            factors.append("Below-average rainfall — water body poorly flushed")
        if strat >= 0.6:
            factors.append(f"Thermal stratification likely (diurnal range {diurnal:.1f}°C)")

    return {
        "score": round(score, 1),
        "wind_mixing_score": round(wind_mix, 3),
        "hydro_stagnation": round(hydro, 3),
        "stratification_score": round(strat, 3),
        "avg_wind_7d": round(avg_wind, 1),
        "diurnal_temp_range": round(diurnal, 1),
        "factors": factors,
    }
