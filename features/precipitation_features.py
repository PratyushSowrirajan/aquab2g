"""
AquaWatch — Precipitation & Stagnation Feature Engineering

Techniques: cumulative analysis, event detection, exponential decay weighting.
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional
from config.constants import RAINFALL


def compute_precipitation_features(
    weather_data: Dict,
    rainfall_history: Optional[pd.DataFrame],
) -> Dict:
    """Compute all precipitation-derived features."""
    daily = weather_data.get("daily", {}) if weather_data else {}
    precip_daily = [p for p in (daily.get("precipitation") or []) if p is not None]

    # Use rainfall_history if available, else build from daily
    if rainfall_history is not None and len(rainfall_history) > 3:
        rain_series = rainfall_history["precipitation_mm"].values
    elif precip_daily:
        rain_series = np.array(precip_daily[:7])
    else:
        rain_series = np.array([0.0])

    # Cumulative rainfall
    rainfall_48h = float(np.sum(rain_series[-2:])) if len(rain_series) >= 2 else 0.0
    rainfall_7d = float(np.sum(rain_series[-7:])) if len(rain_series) >= 7 else float(np.sum(rain_series))
    rainfall_30d = float(np.sum(rain_series))

    # Days since significant rain (>5mm)
    days_since_rain = len(rain_series)
    for i in range(len(rain_series) - 1, -1, -1):
        if rain_series[i] >= RAINFALL["significant_mm"]:
            days_since_rain = len(rain_series) - 1 - i
            break

    # Stagnation index (0-1)
    if len(rain_series) >= 7:
        weekly_rain = np.sum(rain_series[-7:])
        expected_weekly = max(float(np.median(
            [np.sum(rain_series[i:i+7]) for i in range(0, max(1, len(rain_series)-6))]
        )), 5.0)
        stagnation = 1.0 - min(weekly_rain / expected_weekly, 1.0)
    else:
        stagnation = 0.5

    stagnation = round(max(0.0, stagnation), 3)

    # First flush detection
    first_flush = 0.0
    if days_since_rain <= 2 and rainfall_48h >= RAINFALL["first_flush_rain_mm"]:
        # Check if there was a dry period before
        if len(rain_series) >= 5:
            dry_days = sum(1 for r in rain_series[-5:-2] if r < 2.0)
            if dry_days >= RAINFALL["first_flush_dry_days"]:
                first_flush = 1.0
            elif dry_days >= 2 and rainfall_48h >= RAINFALL["heavy_mm"]:
                first_flush = 0.6

    # Rainfall intensity (exponential decay: recent rain matters more)
    decay_rate = 0.3
    intensity = 0.0
    for i, rain in enumerate(reversed(rain_series)):
        intensity += rain * np.exp(-decay_rate * i)
    intensity = round(min(intensity / 50.0, 1.0), 3)

    factors = []
    if days_since_rain >= RAINFALL["stagnation_days"]:
        factors.append(f"No significant rain for {days_since_rain} days — stagnant conditions")
    if first_flush >= 0.6:
        factors.append(f"First flush event: {rainfall_48h:.0f}mm rain after dry period")
    if rainfall_48h >= RAINFALL["heavy_mm"]:
        factors.append(f"Heavy rainfall ({rainfall_48h:.0f}mm in 48h) driving nutrient runoff")
    if stagnation > 0.7:
        factors.append(f"High stagnation index ({stagnation:.2f}) — water body poorly flushed")

    return {
        "rainfall_48h": round(rainfall_48h, 1),
        "rainfall_7d": round(rainfall_7d, 1),
        "rainfall_30d": round(rainfall_30d, 1),
        "days_since_significant_rain": days_since_rain,
        "stagnation_index": stagnation,
        "first_flush_event": first_flush,
        "rainfall_intensity": intensity,
        "factors": factors,
    }
