"""
AquaWatch — Folium Risk Map

Renders an interactive Leaflet map with:
  - Satellite imagery base layer (Esri World Imagery)
  - Layer control to toggle between satellite / street / topo
  - Heatmap overlay (bloom-like cyan → green → yellow → red)
  - Centre marker with rich popup
  - Wind direction indicator
  - Shore risk ring markers
"""

import folium
from folium.plugins import HeatMap
from typing import List, Tuple, Dict
import branca.colormap as cm


def build_risk_map(
    lat: float,
    lon: float,
    risk_score: float,
    heatmap_points: List[Tuple[float, float, float]],
    wind_direction_deg: float = 180.0,
    risk_level: str = "SAFE",
    who_severity: str = "low",
    zoom: int = 11,
) -> folium.Map:
    """
    Build a Folium map with satellite imagery and bloom risk heatmap overlay.
    """
    color_map = {
        "SAFE":     "#2ecc71",
        "LOW":      "#f1c40f",
        "WARNING":  "#e67e22",
        "CRITICAL": "#e74c3c",
    }
    centre_color = color_map.get(risk_level, "#3498db")

    # ------------------------------------------------------------------
    # Base map — Esri Satellite as default
    # ------------------------------------------------------------------
    m = folium.Map(
        location=[lat, lon],
        zoom_start=zoom,
        tiles=None,  # start with no default tile
    )

    # Satellite imagery (default, on top)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri, Maxar, Earthstar Geographics",
        name="🛰 Satellite",
        overlay=False,
        control=True,
    ).add_to(m)

    # Street map option
    folium.TileLayer(
        tiles="OpenStreetMap",
        name="🗺 Street Map",
        overlay=False,
        control=True,
    ).add_to(m)

    # Satellite + Labels hybrid
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="🛰 Satellite + Labels",
        overlay=False,
        control=True,
    ).add_to(m)
    # Add label overlay for hybrid
    folium.TileLayer(
        tiles="https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Labels",
        overlay=True,
        control=True,
    ).add_to(m)

    # ------------------------------------------------------------------
    # Heatmap layer — cyanobacteria bloom–style gradient
    # ------------------------------------------------------------------
    if heatmap_points:
        HeatMap(
            heatmap_points,
            min_opacity=0.30,
            max_opacity=0.80,
            radius=35,
            blur=28,
            gradient={
                "0.0":  "#0d3b66",   # deep blue (water)
                "0.15": "#1b998b",   # teal-green (low chlorophyll)
                "0.30": "#2dc653",   # green (moderate growth)
                "0.50": "#f4d35e",   # yellow
                "0.65": "#ee964b",   # orange
                "0.80": "#e74c3c",   # red (heavy bloom)
                "1.0":  "#7b0d1e",   # dark red (scum)
            },
            name="🦠 Bloom Risk Heatmap",
        ).add_to(m)

    # ------------------------------------------------------------------
    # Colorbar legend
    # ------------------------------------------------------------------
    colormap = cm.LinearColormap(
        colors=["#0d3b66", "#1b998b", "#2dc653", "#f4d35e", "#ee964b", "#e74c3c", "#7b0d1e"],
        vmin=0, vmax=100,
        caption="Bloom Risk Score (0–100)",
    )
    colormap.add_to(m)

    # ------------------------------------------------------------------
    # Centre marker with rich popup
    # ------------------------------------------------------------------
    severity_emoji = {"low": "🟢", "moderate": "🟡", "high": "🟠", "very_high": "🔴"}
    emoji = severity_emoji.get(who_severity, "⚪")
    popup_html = f"""
    <div style="font-family:'Segoe UI',sans-serif;min-width:200px;line-height:1.6;">
      <div style="background:{centre_color};color:white;padding:6px 10px;border-radius:6px 6px 0 0;
                  font-weight:700;font-size:14px;text-align:center;">
        Risk Score: {risk_score:.0f} / 100
      </div>
      <div style="padding:8px 10px;background:#f8f9fa;border-radius:0 0 6px 6px;">
        <b>WHO Severity</b>: {emoji} {who_severity.replace('_', ' ').title()}<br>
        <b>Risk Level</b>: {risk_level}<br>
        <b>Coordinates</b>: {lat:.4f}, {lon:.4f}<br>
        <b>Wind</b>: {_deg_to_compass(wind_direction_deg)} ({wind_direction_deg:.0f}°)
      </div>
    </div>
    """

    folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(popup_html, max_width=260),
        tooltip=f"📍 Risk: {risk_score:.0f}/100 — Click for details",
        icon=folium.Icon(
            color="red" if risk_score > 55 else ("orange" if risk_score > 30 else "green"),
            icon="tint",
            prefix="fa",
        ),
    ).add_to(m)

    # Pulsing circle around centre
    folium.CircleMarker(
        location=[lat, lon],
        radius=18,
        color=centre_color,
        fill=True,
        fill_color=centre_color,
        fill_opacity=0.15,
        weight=2,
        dash_array="5 5",
    ).add_to(m)

    # ------------------------------------------------------------------
    # Wind direction indicator
    # ------------------------------------------------------------------
    compass = _deg_to_compass(wind_direction_deg)
    import math
    arrow_dist = 0.035
    arrow_lat = lat + arrow_dist * math.cos(math.radians(wind_direction_deg))
    arrow_lon = lon + arrow_dist * math.sin(math.radians(wind_direction_deg))

    folium.Marker(
        location=[arrow_lat, arrow_lon],
        icon=folium.DivIcon(
            html=f'<div style="font-size:12px;color:#fff;background:rgba(0,0,0,0.7);'
                 f'padding:3px 8px;border-radius:4px;white-space:nowrap;'
                 f'box-shadow:0 1px 3px rgba(0,0,0,0.3);">'
                 f'💨 Wind: {compass} ({wind_direction_deg:.0f}°)</div>',
            icon_size=(170, 26),
        ),
        tooltip="Wind direction (meteorological)",
    ).add_to(m)

    # ------------------------------------------------------------------
    # Layer control
    # ------------------------------------------------------------------
    folium.LayerControl(collapsed=False).add_to(m)

    return m


def build_click_map(lat: float = 20.0, lon: float = 0.0, zoom: int = 3) -> folium.Map:
    """Build a simple world map for click-to-select location."""
    m = folium.Map(
        location=[lat, lon],
        zoom_start=zoom,
        tiles=None,
    )
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri, Maxar, Earthstar Geographics",
        name="🛰 Satellite",
    ).add_to(m)
    folium.TileLayer(
        tiles="OpenStreetMap",
        name="🗺 Street Map",
    ).add_to(m)
    folium.LayerControl().add_to(m)

    # Add crosshair at click location
    m.add_child(folium.LatLngPopup())

    return m


def _deg_to_compass(deg: float) -> str:
    directions = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
                  "S","SSW","SW","WSW","W","WNW","NW","NNW"]
    idx = round(deg / 22.5) % 16
    return directions[idx]
