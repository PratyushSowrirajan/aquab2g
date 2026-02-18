"""
AquaWatch — Stagnation Index Feature Engineering

Wind mixing + rainfall deficit + thermal stratification proxy.
Source: Huisman et al. (2004) "Changes in Turbulent Mixing" — Ecology
"""

import numpy as np
from typing import Dict


def compute_stagnation_features(
    weather_data: Dict,
    precip_features: Dict,
    water_temp: float,
) -> Dict:
    """Compute water body stagnation index."""
    current = weather_data.get("current", {}) if weather_data else {}
    daily = weather_data.get("daily", {}) if weather_data else {}

    current_wind = current.get("wind_speed", 10.0) or 10.0
    wind_maxes = [w for w in (daily.get("wind_max") or []) if w is not None]
    avg_wind_7d = np.mean(wind_maxes[:7]) if wind_maxes else current_wind

    days_since_rain = precip_features.get("days_since_significant_rain", 3)
    stag_index = precip_features.get("stagnation_index", 0.5)

    # Wind mixing score (calm = bad for water quality)
    if avg_wind_7d > 20:
        wind_mixing = 0.10
    elif avg_wind_7d > 10:
        wind_mixing = 0.40
    elif avg_wind_7d > 5:
        wind_mixing = 0.70
    else:
        wind_mixing = 1.00

    # Hydrological stagnation (from precipitation features)
    hydro_stagnation = stag_index

    # Thermal stratification proxy
    temp_maxes = [t for t in (daily.get("temp_max") or []) if t is not None]
    temp_mins = [t for t in (daily.get("temp_min") or []) if t is not None]
    if temp_maxes and temp_mins:
        diurnal_range = np.mean(temp_maxes[:7]) - np.mean(temp_mins[:7])
    else:
        diurnal_range = 8.0

    if diurnal_range > 10 and avg_wind_7d < 10:
        stratification = 0.80
    elif water_temp > 25 and avg_wind_7d < 15:
        stratification = 0.60
    else:
        stratification = 0.20

    # Combined stagnation score (0-100)
    stagnation_score = (
        0.40 * wind_mixing
        + 0.40 * hydro_stagnation
        + 0.20 * stratification
    ) * 100
    stagnation_score = round(min(max(stagnation_score, 0), 100), 1)

    factors = []
    if avg_wind_7d < 10:
        factors.append(f"Low wind ({avg_wind_7d:.0f} km/h) — poor water mixing")
    if days_since_rain >= 5:
        factors.append(f"No significant rain for {days_since_rain} days — stagnant")
    if stratification >= 0.6:
        factors.append(f"Thermal stratification likely at {water_temp}°C")

    return {
        "avg_wind_7d": round(avg_wind_7d, 1),
        "wind_mixing_score": round(wind_mixing, 3),
        "hydro_stagnation": round(hydro_stagnation, 3),
        "stratification_score": round(stratification, 3),
        "diurnal_temp_range": round(diurnal_range, 1),
        "stagnation_score": stagnation_score,
        "factors": factors,
    }
