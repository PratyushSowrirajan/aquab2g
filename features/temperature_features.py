"""
AquaWatch — Temperature Feature Engineering

Statistical techniques:
  - Harmonic regression (sinusoidal seasonal baseline)
  - Z-score anomaly detection
  - Linear regression (7-day warming trend)
  - Percentile ranking
  - Satellite thermal data (Open-Meteo Marine SST / ERA5 skin / NASA POWER)
  - Fallback: Water temp estimation from air temp (Livingstone & Lotter 1998)
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.special import expit
from typing import Dict, Optional


def estimate_water_temp(
    current_air_temp: float,
    avg_air_temp_7d: float,
    wind_speed_kmh: float = 10.0,
    humidity_pct: float = 50.0,
) -> float:
    """
    Estimate surface water temperature from air temperature.
    Livingstone & Lotter (1998), Boreal Environment Research.
    Used ONLY as fallback when satellite thermal data is unavailable.
    """
    base = 0.65 * current_air_temp + 0.35 * avg_air_temp_7d
    wind_cooling = max(0.0, (wind_speed_kmh - 5.0) * 0.08)
    humidity_correction = (humidity_pct - 50.0) / 100.0 * 1.5
    water_temp = base - wind_cooling + humidity_correction
    return round(max(water_temp, 0.5), 1)


def compute_temperature_features(
    weather_data: Dict,
    historical_temp_df: Optional[pd.DataFrame],
    satellite_thermal: Optional[Dict] = None,
) -> Dict:
    """Compute all temperature-derived features for the model.

    Parameters
    ----------
    weather_data : dict
        Current weather from Open-Meteo API.
    historical_temp_df : DataFrame or None
        5-year historical daily temperature.
    satellite_thermal : dict or None
        Satellite-derived surface temperature from SatelliteThermalClient.
        Keys: water_surface_temp, skin_temp_current, skin_temp_7d, source, method,
              resolution, confidence.
    """
    current = weather_data.get("current", {})
    daily = weather_data.get("daily", {})

    current_temp = current.get("temperature", 20.0) or 20.0
    wind_speed = current.get("wind_speed", 10.0) or 10.0
    humidity = current.get("humidity", 50.0) or 50.0

    # 7-day average from daily means (past days are first 7 entries)
    temp_means = [t for t in (daily.get("temp_mean") or []) if t is not None]
    past_temps = temp_means[:7] if len(temp_means) >= 7 else temp_means
    avg_7d = np.mean(past_temps) if past_temps else current_temp

    # ─── Water temperature: prefer satellite, fallback to air-temp model ──
    water_temp_source = "estimated"
    satellite_source_detail = ""
    satellite_confidence = "LOW"

    sat = satellite_thermal or {}
    sat_water_temp = sat.get("water_surface_temp")

    if sat_water_temp is not None and sat.get("source", "none") != "none":
        # Use satellite-derived temperature
        water_temp = round(float(sat_water_temp), 1)
        water_temp_source = "satellite"
        satellite_source_detail = sat.get("source", "")
        satellite_confidence = sat.get("confidence", "MEDIUM")
    else:
        # Fallback: air-temp estimation (Livingstone & Lotter 1998)
        water_temp = estimate_water_temp(current_temp, avg_7d, wind_speed, humidity)
        water_temp_source = "estimated"
        satellite_source_detail = "Livingstone & Lotter 1998 (air→water model)"
        satellite_confidence = "LOW"

    # Satellite 7-day skin temperature series (if available)
    sat_skin_7d = sat.get("skin_temp_7d", [])
    sat_skin_dates = sat.get("skin_temp_dates", [])

    # 7-day warming trend (slope of linear regression)
    # Prefer satellite skin temp series if available, else air temp
    trend_series = sat_skin_7d if len(sat_skin_7d) >= 4 else past_temps

    if len(trend_series) >= 4:
        slope, _, r_value, p_value, _ = stats.linregress(range(len(trend_series)), trend_series)
        warming_trend = round(slope, 3)
        trend_significant = p_value < 0.1
    else:
        warming_trend = 0.0
        trend_significant = False

    # Z-score anomaly vs historical baseline
    z_score = 0.0
    temp_anomaly = 0.0
    percentile = 50.0
    seasonal_baseline = avg_7d

    if historical_temp_df is not None and len(historical_temp_df) > 30:
        current_month = pd.Timestamp.now().month
        same_month = historical_temp_df[historical_temp_df["month"] == current_month]
        if len(same_month) < 10:
            same_month = historical_temp_df

        hist_mean = same_month["temp_mean"].mean()
        hist_std = same_month["temp_mean"].std()

        if hist_std > 0 and not np.isnan(hist_std):
            z_score = round((current_temp - hist_mean) / hist_std, 2)
            temp_anomaly = round(current_temp - hist_mean, 2)

        percentile = round(stats.percentileofscore(
            same_month["temp_mean"].dropna(), current_temp
        ), 1)

        # Harmonic regression for seasonal baseline
        seasonal_baseline = _harmonic_baseline(historical_temp_df)

    # Bloom temperature probability (logistic curve)
    # Paerl & Huisman (2008): blooms accelerate above 25°C
    bloom_temp_prob = round(float(expit(0.3 * (water_temp - 25.0))), 3)

    factors = []
    if water_temp > 25:
        factors.append(f"Water temp {water_temp}°C exceeds bloom threshold (25°C)")
    if warming_trend > 0.3 and trend_significant:
        factors.append(f"Temperature rising {warming_trend}°C/day")
    if z_score > 1.5:
        factors.append(f"Temperature anomaly: z-score {z_score} (significantly above baseline)")
    if percentile > 90:
        factors.append(f"Current temp is in {percentile}th percentile for this month")
    if water_temp_source == "satellite":
        factors.append(f"Water temp from {satellite_source_detail}")

    return {
        "current_air_temp": current_temp,
        "avg_air_temp_7d": round(avg_7d, 1),
        "water_temp": water_temp,
        "water_temp_source": water_temp_source,
        "water_temp_source_detail": satellite_source_detail,
        "water_temp_confidence": satellite_confidence,
        "satellite_skin_7d": sat_skin_7d,
        "satellite_skin_dates": sat_skin_dates,
        "warming_trend_per_day": warming_trend,
        "trend_significant": trend_significant,
        "z_score": z_score,
        "temp_anomaly_c": temp_anomaly,
        "percentile": percentile,
        "seasonal_baseline": round(seasonal_baseline, 1),
        "bloom_temp_probability": bloom_temp_prob,
        "above_bloom_threshold": water_temp >= 25.0,
        "factors": factors,
    }


def _harmonic_baseline(hist_df: pd.DataFrame) -> float:
    """
    Seasonal baseline via harmonic regression:
    T(t) = a + b*sin(2π*doy/365) + c*cos(2π*doy/365)
    """
    current_doy = pd.Timestamp.now().dayofyear
    doy = hist_df["day_of_year"].values
    temps = hist_df["temp_mean"].values
    mask = ~np.isnan(temps)
    doy, temps = doy[mask], temps[mask]

    if len(temps) < 30:
        return float(np.nanmean(temps))

    sin_t = np.sin(2 * np.pi * doy / 365)
    cos_t = np.cos(2 * np.pi * doy / 365)
    X = np.column_stack([np.ones(len(doy)), sin_t, cos_t])

    try:
        coeffs, _, _, _ = np.linalg.lstsq(X, temps, rcond=None)
        x_now = np.array([1, np.sin(2 * np.pi * current_doy / 365),
                          np.cos(2 * np.pi * current_doy / 365)])
        return float(np.dot(coeffs, x_now))
    except Exception:
        return float(np.nanmean(temps))
