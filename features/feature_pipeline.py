"""
AquaWatch — Feature Pipeline

Orchestrates all feature‑engineering modules and returns a combined vector.
"""

from typing import Dict
from features.temperature_features import compute_temperature_features, estimate_water_temp
from features.precipitation_features import compute_precipitation_features
from features.nutrient_features import compute_nutrient_features
from features.light_features import compute_light_features
from features.stagnation_features import compute_stagnation_features


def build_feature_vector(raw_data: Dict) -> Dict:
    """Build the full feature vector from raw pipeline data.

    Parameters
    ----------
    raw_data : dict
        Output of ``DataPipeline.fetch_all()``.

    Returns
    -------
    dict with keys: temperature, precipitation, nutrients, light,
    stagnation, and a flat ``scores`` sub‑dict for the models.
    """
    weather = raw_data.get("weather") or {}
    hist_temp = raw_data.get("historical_temp")
    rainfall = raw_data.get("rainfall_history")
    land_use = raw_data.get("land_use") or {}
    location = raw_data.get("location") or {}
    lat = location.get("lat", 40.0)

    # --- 1. Temperature features ----------------------------------------
    current = weather.get("current", {}) if weather else {}
    air_temp = current.get("temperature", 20.0)
    water_temp = estimate_water_temp(air_temp)
    temp_feats = compute_temperature_features(hist_temp, water_temp, lat)

    # --- 2. Precipitation features --------------------------------------
    precip_feats = compute_precipitation_features(rainfall, weather)

    # --- 3. Nutrient proxy features -------------------------------------
    nutrient_feats = compute_nutrient_features(land_use, precip_feats)

    # --- 4. Light / UV features -----------------------------------------
    light_feats = compute_light_features(weather, lat)

    # --- 5. Stagnation features -----------------------------------------
    stag_feats = compute_stagnation_features(weather, precip_feats, water_temp)

    # --- Flat scores dict for models ------------------------------------
    scores = {
        "temperature_score": temp_feats.get("temp_score", 50),
        "nutrient_score": nutrient_feats.get("nutrient_score", 50),
        "stagnation_score": stag_feats.get("stagnation_score", 50),
        "light_score": light_feats.get("light_score", 50),
    }

    return {
        "temperature": temp_feats,
        "precipitation": precip_feats,
        "nutrients": nutrient_feats,
        "light": light_feats,
        "stagnation": stag_feats,
        "scores": scores,
        "water_temp": water_temp,
        "air_temp": air_temp,
    }
