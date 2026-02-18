"""
AquaWatch — Model 4: Light / UV Score

UV index + photoperiod + cloud suppression → photosynthesis availability.
Thin model wrapper around light features.

Source: Reynolds (2006) The Ecology of Phytoplankton, Cambridge Univ. Press.
"""

import numpy as np
from typing import Dict


def compute_light_score(light_features: Dict) -> Dict:
    """
    Compute light availability risk score (0–100).

    Parameters
    ----------
    light_features : dict
        Output of ``compute_light_features()`` from feature pipeline.

    Returns
    -------
    dict with keys: score, uv_index, uv_score, day_length_hours,
                    photoperiod_score, cloud_cover_pct, seasonal_score, factors
    """
    score           = light_features.get("light_score", 50.0)
    uv_index        = light_features.get("uv_index", 5.0)
    uv_score        = light_features.get("uv_score", 0.5)
    day_length      = light_features.get("day_length_hours", 12.0)
    photo_score     = light_features.get("photoperiod_score", 0.5)
    cloud_cover     = light_features.get("cloud_cover_pct", 50.0)
    cloud_factor    = light_features.get("cloud_factor", 0.7)
    seasonal_score  = light_features.get("seasonal_score", 0.5)
    factors         = list(light_features.get("factors", []))

    score = float(np.clip(score, 0, 100))

    if not factors:
        if uv_index >= 6:
            factors.append(f"UV index {uv_index:.0f} — high photosynthesis potential")
        if day_length > 13:
            factors.append(f"Day length {day_length:.1f}h — extended bloom-forming window")
        if cloud_cover > 80:
            factors.append(f"Heavy cloud cover ({cloud_cover:.0f}%) suppressing photosynthesis")

    return {
        "score": round(score, 1),
        "uv_index": uv_index,
        "uv_score": round(uv_score, 3),
        "day_length_hours": round(day_length, 1),
        "photoperiod_score": round(photo_score, 3),
        "cloud_cover_pct": round(cloud_cover, 1),
        "cloud_factor": round(cloud_factor, 3),
        "seasonal_score": round(seasonal_score, 3),
        "factors": factors,
    }
