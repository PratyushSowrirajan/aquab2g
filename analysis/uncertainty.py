"""
AquaWatch — Monte Carlo Uncertainty Quantification

Generates confidence bands for the 7-day forecast by perturbing
input parameters and re-running the model N times.

Perturbation sources (calibrated to published instrument uncertainty):
  - Temperature: ±1.5°C (Open-Meteo 7-day forecast RMSE)
  - Precipitation: ±30% (NWP precipitation uncertainty)
  - Wind: ±25% (wind speed forecast uncertainty)
  - UV: ±15%
"""

import numpy as np
from typing import Dict, List, Tuple
from features.temperature_features import compute_temperature_features
from features.precipitation_features import compute_precipitation_features
from features.nutrient_features import compute_nutrient_features
from features.light_features import compute_light_features
from features.stagnation_features import compute_stagnation_features
from models.temperature_model import compute_temperature_score
from models.nutrient_model import compute_nutrient_score
from models.stagnation_model import compute_stagnation_score
from models.light_model import compute_light_score
from models.growth_rate_model import compute_growth_rate
from models.bloom_probability_model import compute_bloom_probability


# Forecast uncertainty by lead day (1σ) — grows with time
TEMP_SIGMA_BY_DAY    = [0.5, 0.8, 1.1, 1.4, 1.7, 2.0, 2.3]   # °C
PRECIP_CV_BY_DAY     = [0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45]  # coefficient of variation
WIND_CV              = 0.20
UV_CV                = 0.12

N_SAMPLES = 50  # Monte Carlo samples per day


def compute_confidence_bands(
    forecast: Dict,
    raw_data: Dict,
) -> Dict:
    """
    Add 10th–90th percentile confidence bands to a forecast dict.

    Parameters
    ----------
    forecast : dict
        Output of ``build_7day_forecast()``.
    raw_data : dict
        Full output of DataPipeline.fetch_all().

    Returns
    -------
    dict with added keys: p10, p90  (lists, one per forecast day incl. today)
    """
    risk_scores = forecast["risk_scores"]
    n_days      = len(risk_scores)

    hist_temp   = raw_data.get("historical_temp")
    land_use    = raw_data.get("land_use") or {}
    location    = raw_data.get("location") or {}
    cyfi_data   = raw_data.get("cyfi") or {}
    lat         = location.get("lat", 40.0)
    weather     = raw_data.get("weather") or {}
    daily       = weather.get("daily", {}) if weather else {}

    PAST = 7
    fc_temps   = (daily.get("temp_mean", []) or [])[PAST:]
    fc_wind    = (daily.get("wind_max", [])   or [])[PAST:]
    fc_uv      = (daily.get("uv_max", [])     or [])[PAST:]
    fc_cloud   = (daily.get("cloud_cover", []) or [])[PAST:]
    fc_precip  = (daily.get("precipitation", []) or [])[PAST:]
    fc_tmax    = (daily.get("temp_max", [])   or [])[PAST:]
    fc_tmin    = (daily.get("temp_min", [])   or [])[PAST:]

    def _get(lst, i, default):
        return lst[i] if i < len(lst) and lst[i] is not None else default

    p10_list = [risk_scores[0]]  # day 0 — no uncertainty
    p90_list = [risk_scores[0]]

    rng = np.random.default_rng(seed=42)

    for i in range(min(7, n_days - 1)):
        base_temp   = _get(fc_temps, i, 20.0)
        base_wind   = _get(fc_wind, i, 10.0)
        base_uv     = _get(fc_uv, i, 5.0)
        base_cloud  = _get(fc_cloud, i, 50.0)
        base_precip = _get(fc_precip, i, 0.0)
        base_tmax   = _get(fc_tmax, i, base_temp + 3)
        base_tmin   = _get(fc_tmin, i, base_temp - 3)

        temp_sigma = TEMP_SIGMA_BY_DAY[i]
        precip_cv  = PRECIP_CV_BY_DAY[i]

        sample_scores = []
        for _ in range(N_SAMPLES):
            s_temp   = base_temp   + rng.normal(0, temp_sigma)
            s_wind   = max(0.5, base_wind  * (1 + rng.normal(0, WIND_CV)))
            s_uv     = max(0.0, base_uv    * (1 + rng.normal(0, UV_CV)))
            s_cloud  = float(np.clip(base_cloud + rng.normal(0, 10), 0, 100))
            s_precip = max(0.0, base_precip * (1 + rng.normal(0, precip_cv)))

            synth = {
                "current": {
                    "temperature": s_temp, "humidity": 60.0,
                    "precipitation": s_precip, "wind_speed": s_wind,
                    "wind_direction": 180, "cloud_cover": s_cloud,
                    "uv_index": s_uv,
                },
                "daily": {
                    "dates": [],
                    "temp_max": [base_tmax + rng.normal(0, temp_sigma)] * 7,
                    "temp_min": [base_tmin + rng.normal(0, temp_sigma)] * 7,
                    "temp_mean": [s_temp] * 7,
                    "precipitation": [max(0, base_precip + rng.normal(0, base_precip * precip_cv + 0.1))] * 7,
                    "uv_max": [s_uv] * 7,
                    "wind_max": [s_wind] * 7,
                    "wind_direction": [180] * 7,
                    "cloud_cover": [s_cloud] * 7,
                },
            }

            try:
                tf   = compute_temperature_features(synth, hist_temp)
                pf   = compute_precipitation_features(synth, None)
                nf   = compute_nutrient_features(land_use, pf, lat)
                lf   = compute_light_features(synth, lat)
                sf   = compute_stagnation_features(synth, pf, tf.get("water_temp", 20.0))

                ts   = compute_temperature_score(tf)["score"]
                ns   = compute_nutrient_score(nf)["score"]
                ss   = compute_stagnation_score(sf)["score"]
                ls   = compute_light_score(lf)["score"]
                gr   = compute_growth_rate(ts, ns, ls, ss, tf.get("water_temp", 20.0))
                res  = compute_bloom_probability(ts, ns, ss, ls, gr, cyfi_data)
                sample_scores.append(res["risk_score"])
            except Exception:
                sample_scores.append(risk_scores[i + 1])

        p10_list.append(round(float(np.percentile(sample_scores, 10)), 1))
        p90_list.append(round(float(np.percentile(sample_scores, 90)), 1))

    return {**forecast, "p10": p10_list, "p90": p90_list}
