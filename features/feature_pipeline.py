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
    satellite_thermal = raw_data.get("satellite_thermal")

    # --- 1. Temperature features ----------------------------------------
    # compute_temperature_features expects (weather_data, historical_temp_df, satellite_thermal)
    temp_feats = compute_temperature_features(weather, hist_temp, satellite_thermal)

    # Derive water_temp and air_temp from the temperature feature output
    water_temp = temp_feats.get("water_temp", 20.0)
    current = weather.get("current", {}) if weather else {}
    air_temp = current.get("temperature", 20.0) or 20.0

    # --- 2. Precipitation features --------------------------------------
    precip_feats = compute_precipitation_features(weather, rainfall)

    # --- 3. Nutrient proxy features -------------------------------------
    nutrient_feats = compute_nutrient_features(land_use, precip_feats, lat)

    # --- 4. Light / UV features -----------------------------------------
    light_feats = compute_light_features(weather, lat)

    # --- 5. Stagnation features -----------------------------------------
    stag_feats = compute_stagnation_features(weather, precip_feats, water_temp)

    # --- Flat scores dict for models ------------------------------------
    # temperature_features returns "bloom_temp_probability" not "temp_score"
    # Derive a 0-100 temperature score from bloom_temp_probability + z_score
    bloom_prob = temp_feats.get("bloom_temp_probability", 0.5)
    z_score = temp_feats.get("z_score", 0.0)
    import numpy as np
    from scipy.special import expit
    temp_score = float(expit(0.3 * (water_temp - 25.0) + 0.5 * z_score)) * 100

    scores = {
        "temperature_score": round(min(max(temp_score, 0), 100), 1),
        "nutrient_score":    nutrient_feats.get("nutrient_score", 50),
        "stagnation_score":  stag_feats.get("stagnation_score", 50),
        "light_score":       light_feats.get("light_score", 50),
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
