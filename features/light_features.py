"""
AquaWatch — Light & UV Feature Engineering

Factors: UV index, photoperiod (day length), cloud cover, seasonality.
"""

import numpy as np
from datetime import datetime
from typing import Dict


def compute_light_features(weather_data: Dict, lat: float) -> Dict:
    """Compute light availability features for cyanobacteria photosynthesis."""
    current = weather_data.get("current", {}) if weather_data else {}
    uv_index = current.get("uv_index", 5.0) or 5.0
    cloud_cover = current.get("cloud_cover", 50.0) or 50.0

    doy = datetime.now().timetuple().tm_yday

    # UV component (normalized to max ~11)
    uv_score = min(uv_index / 11.0, 1.0)

    # Photoperiod calculation (astronomical)
    lat_rad = np.radians(lat)
    declination = np.radians(23.45 * np.sin(np.radians(360 / 365 * (doy - 81))))

    # Hour angle for sunrise/sunset
    cos_ha = -np.tan(lat_rad) * np.tan(declination)
    cos_ha = np.clip(cos_ha, -1.0, 1.0)
    hour_angle = np.degrees(np.arccos(cos_ha))
    day_length_hours = 2.0 * hour_angle / 15.0
    photoperiod_score = min(day_length_hours / 16.0, 1.0)

    # Cloud suppression (clouds reduce but don't eliminate photosynthesis)
    cloud_factor = 1.0 - (cloud_cover / 100.0 * 0.60)

    # Seasonal bloom risk (cosine wave peaking at mid-summer)
    if lat >= 0:
        peak_day = 200  # Mid-July NH
    else:
        peak_day = 15   # Mid-January SH
    seasonal_angle = 2 * np.pi * (doy - peak_day) / 365
    seasonal_score = (np.cos(seasonal_angle) + 1) / 2

    # Combined light score (0-100)
    light_score = (
        0.40 * uv_score
        + 0.25 * photoperiod_score
        + 0.15 * cloud_factor
        + 0.20 * seasonal_score
    ) * 100
    light_score = round(min(max(light_score, 0), 100), 1)

    factors = []
    if uv_index >= 6:
        factors.append(f"High UV index ({uv_index}) favoring surface bloom formation")
    if seasonal_score > 0.6:
        factors.append(f"Peak bloom season (seasonal risk {seasonal_score:.0%})")
    if day_length_hours > 14:
        factors.append(f"Long day length ({day_length_hours:.1f}h) — extended photosynthesis")

    return {
        "uv_index": uv_index,
        "uv_score": round(uv_score, 3),
        "day_length_hours": round(day_length_hours, 1),
        "photoperiod_score": round(photoperiod_score, 3),
        "cloud_cover_pct": cloud_cover,
        "cloud_factor": round(cloud_factor, 3),
        "seasonal_score": round(seasonal_score, 3),
        "light_score": light_score,
        "factors": factors,
    }
