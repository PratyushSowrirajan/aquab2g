"""
AquaWatch — Spatial Risk — IDW Grid for Heatmap

Generates a regular grid of risk scores around the target point
using Inverse Distance Weighting interpolation.

Used to produce the Folium heatmap visual.
Wind direction is used to skew the bloom plume downwind.
"""

import numpy as np
from typing import Dict, List, Tuple


def build_spatial_grid(
    lat: float,
    lon: float,
    risk_score: float,
    wind_direction_deg: float = 180.0,
    n_grid: int = 20,
    radius_deg: float = 0.10,
) -> List[Tuple[float, float, float]]:
    """
    Generate heatmap points as (lat, lon, intensity) tuples.

    Strategy:
      - Create a regular grid within radius_deg of the centre point.
      - Assign weight using IDW (power=2) decaying from centre.
      - Apply wind-direction bias: downwind cells receive higher risk,
        upwind cells receive lower risk (bloom accumulates downwind).
      - Return list of (lat, lon, normalised_intensity) for Folium HeatMap.

    Parameters
    ----------
    lat, lon : float
        Centre coordinates.
    risk_score : float
        Overall risk score 0–100 at the centre point.
    wind_direction_deg : float
        Meteorological wind direction (degrees FROM, 0=N, 90=E, 180=S, 270=W).
    n_grid : int
        Grid resolution (n_grid × n_grid points).
    radius_deg : float
        Half-width of grid in decimal degrees (~6 km at mid-latitudes).

    Returns
    -------
    list of (lat, lon, intensity)
        intensity is 0–1 normalised for Folium HeatMap.
    """
    lats = np.linspace(lat - radius_deg, lat + radius_deg, n_grid)
    lons = np.linspace(lon - radius_deg, lon + radius_deg, n_grid)

    # Wind vector — blooms accumulate on the downwind shore
    wind_rad = np.radians(wind_direction_deg)
    # Wind FROM direction means bloom moves TO the opposite direction
    bloom_dir_rad = wind_rad + np.pi
    wind_vec = np.array([np.cos(bloom_dir_rad), np.sin(bloom_dir_rad)])

    points = []
    for g_lat in lats:
        for g_lon in lons:
            dlat = g_lat - lat
            dlon = g_lon - lon
            dist = max(np.sqrt(dlat**2 + dlon**2), 1e-6)

            # IDW weight (power=2)
            idw_weight = 1.0 / (dist ** 2)

            # Wind bias — positive when point is downwind of centre
            point_vec = np.array([dlat, dlon])
            if dist > 0:
                point_vec_norm = point_vec / dist
            else:
                point_vec_norm = np.array([0.0, 0.0])
            wind_alignment = float(np.dot(wind_vec, point_vec_norm))
            wind_bias = 1.0 + 0.35 * wind_alignment

            # Distance decay (normalised to radius)
            decay = np.exp(-3.0 * (dist / radius_deg) ** 2)

            intensity = (risk_score / 100.0) * decay * wind_bias
            intensity = float(np.clip(intensity, 0.0, 1.0))
            points.append((round(float(g_lat), 6), round(float(g_lon), 6), round(intensity, 4)))

    return points


def build_shore_risk_points(
    lat: float,
    lon: float,
    risk_score: float,
    wind_direction_deg: float = 180.0,
    n_shore: int = 16,
    radius_deg: float = 0.04,
) -> List[Dict]:
    """
    Generate shore-point risk annotations (for marker overlays).
    Returns list of dicts with lat, lon, risk, label.
    """
    points = []
    wind_rad = np.radians(wind_direction_deg)
    bloom_dir_rad = wind_rad + np.pi

    for i in range(n_shore):
        angle = 2 * np.pi * i / n_shore
        dlat = radius_deg * np.cos(angle)
        dlon = radius_deg * np.sin(angle)

        # Alignment with bloom direction
        alignment = np.cos(angle - bloom_dir_rad)
        shore_risk = risk_score * (0.5 + 0.4 * alignment)
        shore_risk = float(np.clip(shore_risk, 0, 100))

        points.append({
            "lat": round(lat + dlat, 6),
            "lon": round(lon + dlon, 6),
            "risk": round(shore_risk, 1),
        })

    return points
