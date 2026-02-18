"""
AquaWatch — 7-Day Forecast Engine

Projects risk score forward 7 days using:
  - Forecast weather data (temperature, precipitation, wind, UV)
  - Current feature state
  - Growth-rate model

Each future day re-runs the full feature + model pipeline using
forecast weather, producing a day-by-day risk trajectory.
"""

import numpy as np
import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta

from features.temperature_features import compute_temperature_features, estimate_water_temp
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


def build_7day_forecast(raw_data: Dict, current_risk: float) -> Dict:
    """
    Build a 7-day forward risk score trajectory.

    Parameters
    ----------
    raw_data : dict
        Full output of DataPipeline.fetch_all().
    current_risk : float
        Today's computed risk score (day 0).

    Returns
    -------
    dict with keys:
        dates          — list of ISO date strings (8 values: today + 7 days)
        risk_scores    — list of float risk scores
        who_severities — list of WHO severity strings
        temperatures   — list of forecast daily mean temps
        precip         — list of forecast daily precipitation
    """
    weather    = raw_data.get("weather") or {}
    hist_temp  = raw_data.get("historical_temp")
    land_use   = raw_data.get("land_use") or {}
    location   = raw_data.get("location") or {}
    cyfi_data  = raw_data.get("cyfi") or {}
    lat        = location.get("lat", 40.0)

    daily      = weather.get("daily", {}) if weather else {}
    dates_raw  = daily.get("dates", [])
    temp_means = daily.get("temp_mean", [])
    temp_maxes = daily.get("temp_max", [])
    temp_mins  = daily.get("temp_min", [])
    precips    = daily.get("precipitation", [])
    wind_maxes = daily.get("wind_max", [])
    uv_maxes   = daily.get("uv_max", [])
    clouds     = daily.get("cloud_cover", [])

    # Open-Meteo returns past_days=7 + forecast_days=7 = 14 entries
    # Days 0..6 are past, days 7..13 are forecast
    # We want indices 7..13 for the 7-day forecast
    PAST = 7
    forecast_dates     = dates_raw[PAST:]      if len(dates_raw) > PAST else []
    forecast_temps     = temp_means[PAST:]     if len(temp_means) > PAST else []
    forecast_temp_max  = temp_maxes[PAST:]     if len(temp_maxes) > PAST else []
    forecast_temp_min  = temp_mins[PAST:]      if len(temp_mins) > PAST else []
    forecast_precip    = precips[PAST:]        if len(precips) > PAST else []
    forecast_wind      = wind_maxes[PAST:]     if len(wind_maxes) > PAST else []
    forecast_uv        = uv_maxes[PAST:]       if len(uv_maxes) > PAST else []
    forecast_cloud     = clouds[PAST:]         if len(clouds) > PAST else []

    # Fill any missing forecast days with last-known values or defaults
    def _fill(lst, default, n=7):
        result = list(lst)[:n]
        last = result[-1] if result else default
        while len(result) < n:
            result.append(last)
        return result

    fc_temps  = _fill(forecast_temps, 20.0)
    fc_tmax   = _fill(forecast_temp_max, 22.0)
    fc_tmin   = _fill(forecast_temp_min, 15.0)
    fc_precip = _fill(forecast_precip, 0.0)
    fc_wind   = _fill(forecast_wind, 10.0)
    fc_uv     = _fill(forecast_uv, 5.0)
    fc_cloud  = _fill(forecast_cloud, 50.0)

    today = datetime.now()
    output_dates    = [today.strftime("%Y-%m-%d")]
    output_scores   = [round(current_risk, 1)]
    output_severity = [_score_to_severity(current_risk)]
    output_temps    = [fc_temps[0] if fc_temps else 20.0]
    output_precip   = [fc_precip[0] if fc_precip else 0.0]

    # Build a rolling precipitation array for stagnation computation
    # start from the last 7 days history
    hist_rain = _fill(
        [p for p in (daily.get("precipitation") or []) if p is not None][:7],
        0.0, 7
    )
    rolling_rain = list(hist_rain)

    for i in range(7):
        day_temp    = fc_temps[i]
        day_wind    = fc_wind[i]
        day_uv      = fc_uv[i]
        day_cloud   = fc_cloud[i]
        day_precip  = fc_precip[i]
        day_tmax    = fc_tmax[i]
        day_tmin    = fc_tmin[i]

        # Advance rolling rain window
        rolling_rain.append(day_precip)
        if len(rolling_rain) > 30:
            rolling_rain.pop(0)

        # Build a synthetic weather dict for this forecast day
        synth_weather = {
            "current": {
                "temperature": day_temp,
                "humidity": 60.0,
                "precipitation": day_precip,
                "wind_speed": day_wind,
                "wind_direction": 180,
                "cloud_cover": day_cloud,
                "uv_index": day_uv,
            },
            "daily": {
                "dates": [],
                "temp_max": [day_tmax] * 7,
                "temp_min": [day_tmin] * 7,
                "temp_mean": [day_temp] * 7,
                "precipitation": rolling_rain[-7:],
                "uv_max": [day_uv] * 7,
                "wind_max": [day_wind] * 7,
                "wind_direction": [180] * 7,
                "cloud_cover": [day_cloud] * 7,
            },
        }
        rain_df = pd.DataFrame({
            "date": pd.date_range(end=today + timedelta(days=i+1), periods=len(rolling_rain)),
            "precipitation_mm": rolling_rain,
        })

        # Feature computation
        temp_f   = compute_temperature_features(synth_weather, hist_temp)
        precip_f = compute_precipitation_features(synth_weather, rain_df)
        nutr_f   = compute_nutrient_features(land_use, precip_f, lat)
        light_f  = compute_light_features(synth_weather, lat)
        stag_f   = compute_stagnation_features(synth_weather, precip_f, temp_f.get("water_temp", 20.0))

        # Model scoring
        t_score = compute_temperature_score(temp_f)["score"]
        n_score = compute_nutrient_score(nutr_f)["score"]
        s_score = compute_stagnation_score(stag_f)["score"]
        l_score = compute_light_score(light_f)["score"]
        gr      = compute_growth_rate(t_score, n_score, l_score, s_score, temp_f.get("water_temp", 20.0))
        result  = compute_bloom_probability(t_score, n_score, s_score, l_score, gr, cyfi_data)

        day_date = (today + timedelta(days=i + 1)).strftime("%Y-%m-%d")
        output_dates.append(day_date)
        output_scores.append(result["risk_score"])
        output_severity.append(result["who_severity"])
        output_temps.append(round(day_temp, 1))
        output_precip.append(round(day_precip, 1))

    return {
        "dates": output_dates,
        "risk_scores": output_scores,
        "who_severities": output_severity,
        "temperatures": output_temps,
        "precip": output_precip,
    }


def _score_to_severity(score: float) -> str:
    from config.constants import WHO_CYANO_THRESHOLDS, CELLS_MAPPING
    slope     = CELLS_MAPPING["slope"]
    intercept = CELLS_MAPPING["intercept"]
    cells     = 10 ** (slope * score + intercept)
    if cells >= WHO_CYANO_THRESHOLDS["high"]:
        return "very_high"
    elif cells >= WHO_CYANO_THRESHOLDS["moderate"]:
        return "high"
    elif cells >= WHO_CYANO_THRESHOLDS["low"]:
        return "moderate"
    return "low"
