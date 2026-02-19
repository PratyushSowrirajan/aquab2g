"""
AquaWatch — Surface Temperature Heat Map

Renders an interactive Folium map with satellite imagery and a
thermal heatmap overlay showing satellite-derived water surface
temperature across the area of interest.
"""

import folium
from folium.plugins import HeatMap
import branca.colormap as cm
import plotly.graph_objects as go
import numpy as np
from typing import List, Tuple, Optional


def build_surface_heatmap(
    thermal_grid: List[Tuple[float, float, float]],
    centre_lat: float,
    centre_lon: float,
    water_temp: float = 20.0,
    water_temp_source: str = "estimated",
    source_detail: str = "",
) -> folium.Map:
    """
    Build a Folium map with satellite imagery and thermal heatmap overlay.

    Parameters
    ----------
    thermal_grid : list of (lat, lon, temperature_celsius)
        Grid points from SatelliteThermalClient.get_thermal_grid().
    centre_lat, centre_lon : float
        Centre of the analysis area.
    water_temp : float
        Water temperature at the centre point.
    water_temp_source : str
        "satellite" or "estimated".
    source_detail : str
        Name of the satellite source used.
    """
    if not thermal_grid or len(thermal_grid) < 4:
        # Return a minimal map with a message marker
        m = folium.Map(location=[centre_lat, centre_lon], zoom_start=10, tiles=None)
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri", name="🛰 Satellite",
        ).add_to(m)
        folium.Marker(
            [centre_lat, centre_lon],
            popup="Insufficient thermal data",
            icon=folium.Icon(color="gray", icon="info-sign"),
        ).add_to(m)
        return m

    temps = np.array([p[2] for p in thermal_grid])
    t_min = float(np.nanmin(temps))
    t_max = float(np.nanmax(temps))

    # Normalize temps to 0-1 weight for heatmap intensity
    t_range = t_max - t_min if t_max > t_min else 1.0
    heatmap_data = [
        [p[0], p[1], max(0.05, (p[2] - t_min) / t_range)]
        for p in thermal_grid
    ]

    # ------------------------------------------------------------------
    # Build Folium map
    # ------------------------------------------------------------------
    m = folium.Map(
        location=[centre_lat, centre_lon],
        zoom_start=11,
        tiles=None,
    )

    # Satellite imagery base
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

    # Labels overlay
    folium.TileLayer(
        tiles="https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="📍 Labels",
        overlay=True,
        control=True,
    ).add_to(m)

    # ------------------------------------------------------------------
    # Temperature heatmap — cool-to-warm water colourscale
    # ------------------------------------------------------------------
    HeatMap(
        heatmap_data,
        min_opacity=0.35,
        max_opacity=0.75,
        radius=40,
        blur=30,
        gradient={
            "0.0":  "#0c2c84",   # deep cold
            "0.15": "#225ea8",
            "0.30": "#1d91c0",   # cool
            "0.45": "#41b6c4",   # temperate
            "0.60": "#7fcdbb",
            "0.75": "#ffffcc",   # warm
            "0.85": "#feb24c",   # hot
            "0.95": "#f03b20",   # very hot
            "1.0":  "#bd0026",   # extreme
        },
        name="🌡 Surface Temperature",
    ).add_to(m)

    # ------------------------------------------------------------------
    # Temperature colorbar legend
    # ------------------------------------------------------------------
    colormap = cm.LinearColormap(
        colors=["#0c2c84", "#225ea8", "#1d91c0", "#41b6c4",
                "#7fcdbb", "#ffffcc", "#feb24c", "#f03b20", "#bd0026"],
        vmin=round(t_min, 1),
        vmax=round(t_max, 1),
        caption=f"Surface Temp ({t_min:.1f}–{t_max:.1f}°C)",
    )
    colormap.add_to(m)

    # ------------------------------------------------------------------
    # Grid point markers (small circles with temp tooltip)
    # ------------------------------------------------------------------
    for lat_pt, lon_pt, temp_val in thermal_grid:
        frac = (temp_val - t_min) / t_range if t_range > 0 else 0.5
        # Pick colour along scale
        if frac < 0.3:
            dot_col = "#1d91c0"
        elif frac < 0.6:
            dot_col = "#7fcdbb"
        elif frac < 0.8:
            dot_col = "#feb24c"
        else:
            dot_col = "#f03b20"

        folium.CircleMarker(
            location=[lat_pt, lon_pt],
            radius=3,
            color=dot_col,
            fill=True,
            fill_color=dot_col,
            fill_opacity=0.6,
            weight=0.5,
            tooltip=f"{temp_val:.1f}°C",
        ).add_to(m)

    # ------------------------------------------------------------------
    # Centre marker with popup
    # ------------------------------------------------------------------
    src_icon = "🛰" if water_temp_source == "satellite" else "🔧"
    src_badge = water_temp_source.title()
    popup_html = f"""
    <div style="font-family:'Segoe UI',sans-serif;min-width:200px;line-height:1.6;">
      <div style="background:#1d91c0;color:white;padding:6px 10px;border-radius:6px 6px 0 0;
                  font-weight:700;font-size:14px;text-align:center;">
        {src_icon} {water_temp:.1f}°C — {src_badge}
      </div>
      <div style="padding:8px 10px;background:#f8f9fa;border-radius:0 0 6px 6px;">
        <b>Source</b>: {source_detail}<br>
        <b>Range</b>: {t_min:.1f}–{t_max:.1f}°C<br>
        <b>Coordinates</b>: {centre_lat:.4f}, {centre_lon:.4f}
      </div>
    </div>
    """

    folium.Marker(
        location=[centre_lat, centre_lon],
        popup=folium.Popup(popup_html, max_width=260),
        tooltip=f"📍 {water_temp:.1f}°C ({src_badge}) — Click for details",
        icon=folium.Icon(
            color="blue" if water_temp < 15 else ("orange" if water_temp < 25 else "red"),
            icon="thermometer-half",
            prefix="fa",
        ),
    ).add_to(m)

    # Pulsing circle around centre
    folium.CircleMarker(
        location=[centre_lat, centre_lon],
        radius=16,
        color="#1d91c0",
        fill=True,
        fill_color="#1d91c0",
        fill_opacity=0.12,
        weight=2,
        dash_array="5 5",
    ).add_to(m)

    # ------------------------------------------------------------------
    # Layer control
    # ------------------------------------------------------------------
    folium.LayerControl(collapsed=False).add_to(m)

    return m


def build_temp_timeline(
    sat_skin_7d: List[float],
    sat_skin_dates: List[str],
    water_temp_source: str = "estimated",
) -> Optional[go.Figure]:
    """
    Build a 7-day satellite skin temperature timeline chart.
    Returns None if insufficient data.
    """
    if not sat_skin_7d or len(sat_skin_7d) < 3:
        return None

    dates = sat_skin_dates if sat_skin_dates else [f"Day {i+1}" for i in range(len(sat_skin_7d))]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=dates,
        y=sat_skin_7d,
        mode="lines+markers",
        line=dict(color="#1d91c0", width=2.5),
        marker=dict(size=7, color="#1d91c0", line=dict(width=1, color="white")),
        fill="tozeroy",
        fillcolor="rgba(29, 145, 192, 0.12)",
        hovertemplate="<b>%{x}</b><br>Surface Temp: %{y:.1f}°C<extra></extra>",
        name="Surface Temperature",
    ))

    # 25°C bloom threshold reference
    fig.add_hline(
        y=25, line_dash="dash", line_color="#e74c3c", line_width=1.5,
        annotation_text="Bloom threshold (25°C)",
        annotation_position="top left",
        annotation_font=dict(size=10, color="#e74c3c"),
    )

    # Trend line
    if len(sat_skin_7d) >= 4:
        from scipy import stats as sp_stats
        slope, intercept, _, _, _ = sp_stats.linregress(range(len(sat_skin_7d)), sat_skin_7d)
        trend_y = [intercept + slope * i for i in range(len(sat_skin_7d))]
        trend_dir = "↑" if slope > 0.05 else ("↓" if slope < -0.05 else "→")

        fig.add_trace(go.Scatter(
            x=dates,
            y=trend_y,
            mode="lines",
            line=dict(color="#e67e22", width=1.5, dash="dot"),
            name=f"Trend {trend_dir} ({slope:+.2f}°C/day)",
            hoverinfo="skip",
        ))

    source_label = "🛰 Satellite" if water_temp_source == "satellite" else "🔧 Estimated"

    fig.update_layout(
        title=dict(
            text=f"7-Day Surface Temperature · {source_label}",
            font=dict(size=13),
            x=0.02, xanchor="left",
        ),
        xaxis=dict(title="", gridcolor="#e8e8e8"),
        yaxis=dict(title="Temperature (°C)", gridcolor="#e8e8e8"),
        height=260,
        margin=dict(l=50, r=20, t=45, b=30),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=11),
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1, font=dict(size=10),
        ),
    )

    return fig


def _empty_figure(message: str) -> go.Figure:
    """Return a placeholder figure with a message."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=14, color="#999"),
    )
    fig.update_layout(
        height=300,
        paper_bgcolor="white",
        plot_bgcolor="white",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig
