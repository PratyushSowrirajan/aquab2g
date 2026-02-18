"""
AquaWatch — Open-Meteo Weather Client

Fetches REAL weather data from Open-Meteo API.
- No API key required
- No rate limits for basic use
- Real-time current conditions
- 7-day forecast
- Historical archive (back to 1940)
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional


class WeatherClient:
    """Client for Open-Meteo free weather API."""

    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
    HISTORICAL_URL = "https://archive-api.open-meteo.com/v1/archive"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "Cache-Control": "no-cache",
        })

    # -----------------------------------------------------------------
    # Current + 7-day history + 7-day forecast (single call)
    # -----------------------------------------------------------------
    def get_current_and_forecast(self, lat: float, lon: float) -> Dict:
        """
        Fetch current conditions, 7-day history, and 7-day forecast.
        Returns structured dict with all weather data needed.
        """
        params = {
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "current": ",".join([
                "temperature_2m",
                "relative_humidity_2m",
                "precipitation",
                "wind_speed_10m",
                "wind_direction_10m",
                "cloud_cover",
                "uv_index",
            ]),
            "daily": ",".join([
                "temperature_2m_max",
                "temperature_2m_min",
                "temperature_2m_mean",
                "precipitation_sum",
                "uv_index_max",
                "wind_speed_10m_max",
                "wind_direction_10m_dominant",
                "cloud_cover_mean",
            ]),
            "past_days": 7,
            "forecast_days": 7,
            "timezone": "auto",
        }

        resp = self.session.get(self.FORECAST_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        current = data.get("current", {})
        daily = data.get("daily", {})

        return {
            "current": {
                "temperature": current.get("temperature_2m"),
                "humidity": current.get("relative_humidity_2m"),
                "precipitation": current.get("precipitation"),
                "wind_speed": current.get("wind_speed_10m"),
                "wind_direction": current.get("wind_direction_10m"),
                "cloud_cover": current.get("cloud_cover"),
                "uv_index": current.get("uv_index"),
            },
            "daily": {
                "dates": daily.get("time", []),
                "temp_max": daily.get("temperature_2m_max", []),
                "temp_min": daily.get("temperature_2m_min", []),
                "temp_mean": daily.get("temperature_2m_mean", []),
                "precipitation": daily.get("precipitation_sum", []),
                "uv_max": daily.get("uv_index_max", []),
                "wind_max": daily.get("wind_speed_10m_max", []),
                "wind_direction": daily.get("wind_direction_10m_dominant", []),
                "cloud_cover": daily.get("cloud_cover_mean", []),
            },
            "location": {"lat": lat, "lon": lon},
            "fetched_at": datetime.now().isoformat(),
        }

    # -----------------------------------------------------------------
    # Historical temperature for baseline (up to 10 years)
    # -----------------------------------------------------------------
    def get_historical_temperature(
        self, lat: float, lon: float, years_back: int = 5
    ) -> pd.DataFrame:
        """
        Fetch historical daily temperature for seasonal baseline calculation.
        Used for z-score anomaly detection and harmonic regression.
        """
        end_date = datetime.now() - timedelta(days=14)
        start_date = end_date - timedelta(days=365 * years_back)

        params = {
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "daily": "temperature_2m_max,temperature_2m_min,temperature_2m_mean",
            "timezone": "auto",
        }

        resp = self.session.get(self.HISTORICAL_URL, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        daily = data.get("daily", {})
        df = pd.DataFrame({
            "date": pd.to_datetime(daily.get("time", [])),
            "temp_max": daily.get("temperature_2m_max", []),
            "temp_min": daily.get("temperature_2m_min", []),
            "temp_mean": daily.get("temperature_2m_mean", []),
        })
        df = df.dropna(subset=["temp_mean"])
        df["month"] = df["date"].dt.month
        df["day_of_year"] = df["date"].dt.dayofyear
        return df

    # -----------------------------------------------------------------
    # Historical rainfall for stagnation + runoff analysis
    # -----------------------------------------------------------------
    def get_rainfall_history(
        self, lat: float, lon: float, days: int = 30
    ) -> pd.DataFrame:
        """Fetch daily precipitation history for stagnation and runoff models."""
        end_date = datetime.now() - timedelta(days=1)
        start_date = end_date - timedelta(days=days)

        params = {
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "daily": "precipitation_sum,rain_sum",
            "timezone": "auto",
        }

        resp = self.session.get(self.HISTORICAL_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        daily = data.get("daily", {})
        df = pd.DataFrame({
            "date": pd.to_datetime(daily.get("time", [])),
            "precipitation_mm": daily.get("precipitation_sum", []),
        })
        df["precipitation_mm"] = df["precipitation_mm"].fillna(0.0)
        return df
