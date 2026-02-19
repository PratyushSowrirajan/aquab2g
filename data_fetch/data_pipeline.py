"""
AquaWatch — Data Pipeline Orchestrator
Fetches ALL data sources for a given location and returns unified dict.
"""

from typing import Dict
from datetime import datetime
from data_fetch.weather_client import WeatherClient
from data_fetch.cyfi_client import CyFiClient
from data_fetch.land_use_reader import LandUseReader
from data_fetch.satellite_thermal import SatelliteThermalClient


class DataPipeline:
    def __init__(self):
        self.weather = WeatherClient()
        self.cyfi = CyFiClient()
        self.land_use = LandUseReader()
        self.thermal = SatelliteThermalClient()

    def fetch_all(self, lat: float, lon: float) -> Dict:
        errors = {}

        try:
            weather_data = self.weather.get_current_and_forecast(lat, lon)
        except Exception as e:
            weather_data = None
            errors["weather"] = str(e)

        try:
            historical_temp = self.weather.get_historical_temperature(lat, lon, years_back=5)
        except Exception as e:
            historical_temp = None
            errors["historical_temp"] = str(e)

        try:
            rainfall_history = self.weather.get_rainfall_history(lat, lon, days=30)
        except Exception as e:
            rainfall_history = None
            errors["rainfall_history"] = str(e)

        try:
            cyfi_data = self.cyfi.get_prediction(lat, lon)
        except Exception as e:
            cyfi_data = {"density_cells_per_ml": 0, "severity": "unknown",
                         "severity_score": 0, "source": "unavailable"}
            errors["cyfi"] = str(e)

        try:
            land_use_data = self.land_use.get_land_use(lat, lon)
        except Exception as e:
            land_use_data = LandUseReader._default()
            errors["land_use"] = str(e)

        # Satellite thermal data (surface skin / water temperature)
        try:
            satellite_thermal = self.thermal.get_surface_temperature(lat, lon)
        except Exception as e:
            satellite_thermal = {
                "water_surface_temp": None, "source": "none",
                "confidence": "LOW",
            }
            errors["satellite_thermal"] = str(e)

        # Thermal grid for surface heat map
        try:
            thermal_grid = self.thermal.get_thermal_grid(lat, lon)
        except Exception as e:
            thermal_grid = []
            errors["thermal_grid"] = str(e)

        available_count = sum([
            weather_data is not None,
            historical_temp is not None and len(historical_temp) > 100,
            cyfi_data.get("source", "") != "unavailable",
        ])
        if available_count >= 3:
            confidence = "HIGH"
        elif available_count >= 2:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        return {
            "location": {"lat": lat, "lon": lon},
            "weather": weather_data,
            "cyfi": cyfi_data,
            "land_use": land_use_data,
            "historical_temp": historical_temp,
            "rainfall_history": rainfall_history,
            "satellite_thermal": satellite_thermal,
            "thermal_grid": thermal_grid,
            "fetched_at": datetime.now().isoformat(),
            "data_quality": {"confidence": confidence, "errors": errors},
        }
