"""
AquaWatch — Main Streamlit Dashboard
=====================================
Water Contamination Risk Early Warning System

Entry point: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from streamlit_folium import st_folium

# ── Internal imports ──────────────────────────────────────────────────────────
from config.demo_sites import DEMO_SITES
from config.constants import RISK_LEVELS, WHO_CYANO_THRESHOLDS

from data_fetch.data_pipeline import DataPipeline

from features.feature_pipeline import build_feature_vector

from models.temperature_model import compute_temperature_score
from models.nutrient_model import compute_nutrient_score
from models.stagnation_model import compute_stagnation_score
from models.light_model import compute_light_score
from models.growth_rate_model import compute_growth_rate
from models.bloom_probability_model import compute_bloom_probability

from analysis.forecast_engine import build_7day_forecast
from analysis.uncertainty import compute_confidence_bands
from analysis.trend_analysis import compute_trend
from analysis.spatial_risk import build_spatial_grid
from analysis.who_comparison import format_who_comparison

from visualization.risk_map import build_risk_map, build_click_map
from visualization.trend_chart import build_forecast_chart
from visualization.risk_gauge import build_risk_gauge, build_component_gauges
from visualization.component_breakdown import build_component_bar, build_monod_factors_chart
from visualization.report_generator import generate_pdf_report
from visualization.surface_heatmap import build_surface_heatmap, build_temp_timeline

# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AquaWatch — Water Risk Monitor",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Risk card styling */
  .risk-card {
      background: #f8fafc; border-radius: 10px; padding: 14px 18px;
      border-left: 5px solid #3498db; margin-bottom: 10px;
  }
  .risk-card h3 { margin: 0 0 4px 0; font-size: 1.0rem; color: #555; }
  .risk-card .big { font-size: 2.0rem; font-weight: 700; }

  /* Factor tags */
  .factor-tag {
      display: inline-block; background: #eaf4ff; color: #1e6bb8;
      border-radius: 6px; padding: 3px 10px; font-size: 0.78rem; margin: 2px;
      font-weight: 500; border: 1px solid #c3ddf7;
  }

  /* WHO alert banner */
  .who-banner {
      padding: 14px 20px; border-radius: 8px; margin: 10px 0;
      font-weight: 600; font-size: 1.0rem;
  }

  /* Smaller metric labels */
  .stMetric label { font-size: 0.78rem !important; }

  /* Sidebar polish */
  [data-testid="stSidebar"] {
      background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
  }

  /* Better dividers */
  hr { border-color: #e2e8f0 !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Helper: WHO comparison bar — defined here so it is always available
# ─────────────────────────────────────────────────────────────────────────────
def _build_who_bar(cells_per_ml: int, thresholds: list, risk_color: str):
    """Small Plotly bar showing cells/mL vs WHO thresholds (log scale)."""
    import plotly.graph_objects as go

    labels = ["Current"] + [t["label"] for t in thresholds]
    values = [max(cells_per_ml, 100)] + [t["cells"] for t in thresholds]
    colors = [risk_color] + [t["color"] for t in thresholds]

    fig = go.Figure(go.Bar(
        x=labels, y=values,
        marker_color=colors,
        text=[f"{v:,.0f}" for v in values],
        textposition="outside",
        hovertemplate="<b>%{x}</b>: %{y:,.0f} cells/mL<extra></extra>",
    ))
    fig.update_layout(
        yaxis=dict(type="log", title="cells/mL (log scale)", gridcolor="#f0f0f0"),
        xaxis=dict(title=""),
        height=220,
        margin=dict(l=10, r=10, t=10, b=20),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=11),
        showlegend=False,
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Cached pipeline
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def run_full_pipeline(lat: float, lon: float):
    """Fetch all data and compute full risk assessment."""
    pipeline = DataPipeline()
    raw = pipeline.fetch_all(lat, lon)

    # Feature vector
    fv = build_feature_vector(raw)
    scores = fv["scores"]

    # Models 1-4
    t_out  = compute_temperature_score(fv["temperature"])
    n_out  = compute_nutrient_score(fv["nutrients"])
    s_out  = compute_stagnation_score(fv["stagnation"])
    l_out  = compute_light_score(fv["light"])

    t_score = t_out["score"]
    n_score = n_out["score"]
    s_score = s_out["score"]
    l_score = l_out["score"]
    water_temp = fv.get("water_temp", 20.0)

    # Model 5 — growth rate
    gr = compute_growth_rate(t_score, n_score, l_score, s_score, water_temp)

    # Model 6 — bloom probability
    risk = compute_bloom_probability(
        t_score, n_score, s_score, l_score,
        gr, raw.get("cyfi"), raw["data_quality"]["confidence"]
    )

    # Forecast
    forecast_raw = build_7day_forecast(raw, risk["risk_score"])
    forecast     = compute_confidence_bands(forecast_raw, raw)

    # Trend (build 30-day synthetic series from forecast + current)
    trend_series = _build_trend_series(raw, risk["risk_score"])
    trend        = compute_trend(trend_series)

    # Spatial heatmap
    wind_dir = (raw.get("weather") or {}).get("current", {}).get("wind_direction", 180) or 180
    heatmap_points = build_spatial_grid(lat, lon, risk["risk_score"], wind_dir)

    # WHO comparison
    who_info = format_who_comparison(
        risk["risk_score"],
        risk["estimated_cells_per_ml"],
        risk["who_severity"],
    )

    return {
        "raw": raw,
        "feature_vector": fv,
        "t_out": t_out, "n_out": n_out, "s_out": s_out, "l_out": l_out,
        "growth_rate": gr,
        "risk": risk,
        "forecast": forecast,
        "trend": trend,
        "heatmap_points": heatmap_points,
        "who_info": who_info,
        "wind_dir": wind_dir,
        "thermal_grid": raw.get("thermal_grid", []),
    }


def _build_trend_series(raw: dict, current_score: float):
    """
    Build a 30-day historical risk score series.
    Uses historical temperature z-scores as a proxy for past risk.
    """
    hist = raw.get("historical_temp")
    if hist is None or len(hist) < 10:
        return [current_score]

    hist = hist.copy()
    recent = hist.tail(30).copy()

    mu  = recent["temp_mean"].mean()
    sig = recent["temp_mean"].std()
    if sig == 0 or np.isnan(sig):
        return [current_score] * min(30, len(recent))

    from scipy.special import expit
    scores = []
    for _, row in recent.iterrows():
        z = (row["temp_mean"] - mu) / sig
        s = float(expit(0.3 * (row["temp_mean"] - 25.0) + 0.4 * z)) * 100
        scores.append(round(s, 1))
    scores.append(current_score)
    return scores


# ─────────────────────────────────────────────────────────────────────────────
# Session state defaults
# ─────────────────────────────────────────────────────────────────────────────
if "analyze" not in st.session_state:
    st.session_state["analyze"] = False
if "map_lat" not in st.session_state:
    st.session_state["map_lat"] = None
if "map_lon" not in st.session_state:
    st.session_state["map_lon"] = None

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:8px 0;">
      <span style="font-size:2.2rem;">💧</span><br>
      <span style="font-size:1.3rem;font-weight:700;color:#1a73e8;">AquaWatch</span><br>
      <span style="font-size:0.72rem;color:#888;">Water Contamination Risk Monitor</span>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    input_mode = st.radio(
        "📍 Location Input",
        ["Demo Site", "Click on Map", "Enter Coordinates"],
        horizontal=False,
    )

    if input_mode == "Demo Site":
        site_key = st.selectbox(
            "Select Demo Site",
            list(DEMO_SITES.keys()),
            format_func=lambda k: DEMO_SITES[k]["name"],
        )
        site = DEMO_SITES[site_key]
        lat = site["lat"]
        lon = site["lon"]
        st.info(f"📍 {site['name']}\n\n{site['description']}")

    elif input_mode == "Click on Map":
        lat = st.session_state.get("map_lat") or 20.0
        lon = st.session_state.get("map_lon") or 0.0
        if st.session_state.get("map_lat"):
            st.success(f"📍 Selected: {lat:.4f}, {lon:.4f}")
        else:
            st.info("👆 Click anywhere on the map below to select a location")

    else:  # Enter Coordinates
        lat = st.number_input("Latitude", value=41.6833, min_value=-90.0, max_value=90.0, format="%.4f")
        lon = st.number_input("Longitude", value=-82.8833, min_value=-180.0, max_value=180.0, format="%.4f")

    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🔍 Analyze", type="primary"):
            st.session_state["analyze"] = True
            # Clear cache to get fresh real-time data
            run_full_pipeline.clear()
    with col_b:
        if st.button("🔄 Refresh"):
            st.session_state["analyze"] = True
            run_full_pipeline.clear()

    st.divider()

    # Data source panel
    st.markdown("**🔗 Data Sources**")
    st.markdown("""
    <div style="font-size:0.78rem;line-height:1.8;color:#555;">
      🟢 <b>Open-Meteo API</b> — Live weather (no key)<br>
      🟢 <b>Satellite Thermal</b> — SST / ERA5 / NASA POWER<br>
      🟢 <b>CyFi / NASA</b> — Satellite ML bloom prediction<br>
      🟢 <b>ESA WorldCover</b> — Land use classification<br>
      🟢 <b>WHO 2003</b> — Recreational water guidelines<br>
      <span style="color:#2ecc71;font-weight:600;">Cost: $0 · All open data</span>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
st.title("💧 AquaWatch — Water Contamination Risk Monitor")
st.caption(f"Cyanobacteria Early Warning System · {datetime.now().strftime('%d %B %Y · %H:%M UTC')}")

# ─────────────────────────────────────────────────────────────────────────────
# Click-on-Map mode — show selector map first
# ─────────────────────────────────────────────────────────────────────────────
if input_mode == "Click on Map" and not st.session_state.get("analyze", False):
    st.subheader("🗺 Click anywhere on the map to select a water body")
    st.caption("Click a lake, river, or coastline — coordinates will be captured automatically.")
    click_map = build_click_map()
    map_data = st_folium(click_map, height=500, width="100%")

    if map_data and map_data.get("last_clicked"):
        clicked = map_data["last_clicked"]
        st.session_state["map_lat"] = clicked["lat"]
        st.session_state["map_lon"] = clicked["lng"]
        lat = clicked["lat"]
        lon = clicked["lng"]
        st.success(f"✅ Location selected: **{lat:.4f}, {lon:.4f}** — Press **Analyze** in the sidebar!")
    st.stop()

if not st.session_state.get("analyze", False):
    # Landing page
    st.markdown("""
    <div style="background:linear-gradient(135deg,#e0f2fe,#f0f9ff);border-radius:12px;
                padding:28px 32px;margin-top:10px;border:1px solid #bae6fd;">
      <h3 style="margin-top:0;color:#0369a1;">🌊 How to use AquaWatch</h3>
      <ol style="line-height:2.0;color:#334155;">
        <li>Select a <b>Demo Site</b>, <b>Click on Map</b>, or <b>Enter Coordinates</b></li>
        <li>Click <b>Analyze</b> to fetch <b>real-time</b> weather data and run 6 bio-mathematical models</li>
        <li>View <b>satellite risk maps</b>, 7-day forecasts, growth kinetics, and WHO comparisons</li>
        <li>Download a <b>PDF Report</b> for field use or regulatory submissions</li>
      </ol>
      <p style="margin-bottom:0;color:#64748b;">
        Powered by real-time weather from Open-Meteo, NASA CyFi satellite ML,
        ESA land-use data, and Monod kinetics growth modelling.
        <b>100% free. 100% open data. Zero API keys.</b>
      </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")
    col1, col2, col3 = st.columns(3)
    for col, key in zip([col1, col2, col3], DEMO_SITES):
        site = DEMO_SITES[key]
        is_high = "HIGH" in site["expected_risk"]
        border_color = "#ef4444" if is_high else "#22c55e"
        badge_bg = "#fef2f2" if is_high else "#f0fdf4"
        badge_color = "#dc2626" if is_high else "#16a34a"
        col.markdown(f"""
        <div style="border:2px solid {border_color};border-radius:10px;padding:16px;
                    margin-top:8px;background:white;">
          <div style="font-weight:700;font-size:1.0rem;margin-bottom:6px;">{site['name']}</div>
          <div style="display:inline-block;background:{badge_bg};color:{badge_color};
                      padding:2px 10px;border-radius:4px;font-size:0.8rem;font-weight:600;
                      margin-bottom:8px;">{site['expected_risk']}</div>
          <div style="font-size:0.82rem;color:#64748b;line-height:1.5;">
            {site['description'][:120]}
          </div>
        </div>
        """, unsafe_allow_html=True)
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# ⓪ Analysis Pipeline
# ─────────────────────────────────────────────────────────────────────────────
with st.spinner(f"🔄 Fetching **real-time** data and computing risk for ({lat:.4f}, {lon:.4f})…"):
    try:
        result = run_full_pipeline(lat, lon)
    except Exception as e:
        st.error(f"⚠️ Pipeline error: {e}")
        st.stop()

raw         = result["raw"]
risk        = result["risk"]
gr          = result["growth_rate"]
forecast    = result["forecast"]
trend       = result["trend"]
heatmap_pts = result["heatmap_points"]
who_info    = result["who_info"]
fv          = result["feature_vector"]
wind_dir    = result["wind_dir"]
thermal_grid = result.get("thermal_grid", [])
dq          = raw["data_quality"]

risk_score  = risk["risk_score"]
risk_level  = risk["risk_level"]
risk_color  = risk["risk_color"]
risk_emoji  = risk["risk_emoji"]
who_sev     = risk["who_severity"]
cells       = risk["estimated_cells_per_ml"]
advisory    = risk["advisory"]
confidence  = risk["confidence"]
comp        = risk["component_scores"]

# Parse fetch time for freshness display
fetched_at_str = raw.get("fetched_at", "")
try:
    fetched_dt = datetime.fromisoformat(fetched_at_str)
    age_seconds = (datetime.now() - fetched_dt).total_seconds()
    if age_seconds < 60:
        freshness = f"🟢 {int(age_seconds)}s ago (real-time)"
    elif age_seconds < 300:
        freshness = f"🟢 {int(age_seconds//60)}m ago"
    elif age_seconds < 1800:
        freshness = f"🟡 {int(age_seconds//60)}m ago (cached)"
    else:
        freshness = f"🔴 {int(age_seconds//60)}m ago (stale — click Refresh)"
except Exception:
    freshness = "⚪ Unknown"

# ─────────────────────────────────────────────────────────────────────────────
# ① Real-time data banner
# ─────────────────────────────────────────────────────────────────────────────
banner_bg = {
    "SAFE": "#d5f5e3", "LOW": "#fef9e7",
    "WARNING": "#fdebd0", "CRITICAL": "#fadbd8",
}
st.markdown(f"""
<div style="background:{banner_bg.get(risk_level,'#f0f0f0')};border-left:6px solid {risk_color};
            border-radius:8px;padding:14px 20px;margin-bottom:8px;">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;">
    <div>
      {risk_emoji} <b style="font-size:1.1rem;">{risk_level}</b> &nbsp;·&nbsp;
      WHO: {who_sev.replace('_',' ').title()} &nbsp;·&nbsp;
      Est. {cells:,} cells/mL &nbsp;·&nbsp;
      Confidence: <b>{confidence}</b>
    </div>
    <div style="font-size:0.82rem;color:#555;">
      Data freshness: {freshness}
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ② Top metrics row
# ─────────────────────────────────────────────────────────────────────────────
m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    limiting = risk.get("limiting_driver", "")
    st.metric(
        "Risk Score", f"{risk_score:.0f}/100",
        delta=f"Limited by {limiting}" if risk_score < 40 else None,
        delta_color="off",
        help="0 = safe, 100 = critical bloom risk. "
             "Geometric mean of Temperature (35%), Nutrients (25%), "
             "Stagnation (22%), Light (18%). A near-zero component "
             "collapses the score — matching biological reality.",
    )
with m2:
    wt = fv.get("water_temp", 0)
    at = fv.get("air_temp", 0)
    wt_src = fv["temperature"].get("water_temp_source", "estimated")
    wt_icon = "🛰" if wt_src == "satellite" else "🔧"
    st.metric("Water Temp", f"{wt:.1f}°C", delta=f"{wt_icon} {wt_src.title()} · Air: {at:.1f}°C")
with m3:
    mu = gr.get("mu_per_day", 0)
    dbl = gr.get("doubling_time_hours")
    wt_for_growth = fv.get("water_temp", 20)
    if dbl:
        growth_delta = f"Doubling: {dbl:.0f}h"
    elif wt_for_growth < 12:
        growth_delta = f"❄ Water too cold ({wt_for_growth:.0f}°C < 12°C)"
    else:
        growth_delta = "No growth"
    st.metric(
        "Growth Rate (µ)", f"{mu:.3f}/day",
        delta=growth_delta,
        delta_color="off",
        help="Monod kinetics: µ = µ_max × f(T) × f(N) × f(L) × f(S). "
             "Cyanobacteria optimal growth at 28°C; near-zero below 12°C.",
    )
with m4:
    precip = fv["precipitation"].get("rainfall_7d", 0)
    days_dry = fv["precipitation"].get("days_since_significant_rain", 0)
    rain_delta_color = "inverse" if days_dry >= 7 else "normal"
    st.metric(
        "Rain (7d)", f"{precip:.0f} mm",
        delta=f"↑ {days_dry}d since ≥5 mm rain",
        delta_color="off",
        help="Significant rain = ≥ 5 mm/day. Dry spells increase stagnation "
             "and surface accumulation of cyanobacteria. Light drizzle "
             "(< 5 mm) does not flush nutrients or break stratification.",
    )
with m5:
    wind = fv["stagnation"].get("avg_wind_7d", 0)
    st.metric("Avg Wind", f"{wind:.0f} km/h")

# Context explanation when a single factor dominates the score
_wt = fv.get("water_temp", 20)
_limiting = risk.get("limiting_driver", "")
_scores = risk.get("component_scores", {})
if _wt < 12 and _limiting == "Temperature":
    st.info(
        f"🧊 **Water temperature ({_wt:.1f}°C) is suppressing all risk.** "
        f"Cyanobacteria require ≥15°C to grow and thrive at ~28°C. "
        f"At current temperature, biological growth is near zero regardless of "
        f"other factors (Stagnation {_scores.get('Stagnation', 0):.0f}/100, "
        f"Nutrients {_scores.get('Nutrients', 0):.0f}/100). "
        f"Risk will increase as water warms in spring/summer.",
        icon="❄️",
    )
elif days_dry >= 14 and risk_score < 40:
    st.info(
        f"🏜️ **{days_dry} days without significant rain (≥5 mm).** "
        f"Stagnation is elevated but overall risk remains {risk_level} "
        f"because temperature ({_wt:.1f}°C) limits cyanobacterial growth.",
        icon="💧",
    )

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# ③ Satellite Map + Risk Scores (two-column)
# ─────────────────────────────────────────────────────────────────────────────
map_col, score_col = st.columns([1.3, 1.0], gap="medium")

with map_col:
    st.subheader("🛰 Satellite Risk Map")
    m = build_risk_map(
        lat, lon, risk_score, heatmap_pts,
        wind_dir, risk_level, who_sev,
    )
    map_result = st_folium(m, height=450, width="100%", returned_objects=["last_clicked"])

    # Allow re-analysis by clicking on the risk map too
    if map_result and map_result.get("last_clicked"):
        new_click = map_result["last_clicked"]
        new_lat, new_lon = new_click["lat"], new_click["lng"]
        if abs(new_lat - lat) > 0.001 or abs(new_lon - lon) > 0.001:
            st.session_state["map_lat"] = new_lat
            st.session_state["map_lon"] = new_lon
            st.info(f"📍 New location clicked: {new_lat:.4f}, {new_lon:.4f} — Press **Analyze** to update")

    st.caption(
        f"🛰 Esri satellite imagery with bloom risk heatmap overlay. "
        f"Wind: {wind_dir:.0f}° — bloom plume modelled downwind via IDW interpolation. "
        f"Use layer control (top-right) to switch map styles."
    )

with score_col:
    st.subheader("📊 Overall Risk")
    st.plotly_chart(build_risk_gauge(risk_score), width='stretch', config={"displayModeBar": False})

    st.subheader("Component Scores")
    st.plotly_chart(build_component_bar(comp), width='stretch', config={"displayModeBar": False})

    # Factor tags
    all_factors = []
    for key in ["temperature", "nutrients", "stagnation", "light"]:
        all_factors.extend(fv[key].get("factors", []))
    if all_factors:
        tags_html = "".join(f'<span class="factor-tag">{f}</span>' for f in all_factors[:6])
        st.markdown(f"**Key Factors:**<br>{tags_html}", unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# ③b Surface Temperature Heat Map
# ─────────────────────────────────────────────────────────────────────────────
st.subheader("🌡 Surface Temperature Heat Map")

temp_info = fv.get("temperature", {})
wt_source = temp_info.get("water_temp_source", "estimated")
wt_source_detail = temp_info.get("water_temp_source_detail", "")
wt_confidence = temp_info.get("water_temp_confidence", "LOW")

# Source badge
src_badge_color = {"satellite": "#2ecc71", "estimated": "#e67e22"}.get(wt_source, "#aaa")
src_badge_icon = "🛰" if wt_source == "satellite" else "🔧"
st.markdown(f"""
<div style="display:flex;gap:12px;align-items:center;margin-bottom:8px;flex-wrap:wrap;">
  <div style="background:{src_badge_color}18;border:1px solid {src_badge_color};border-radius:6px;
              padding:4px 12px;font-size:0.85rem;font-weight:600;color:{src_badge_color};">
    {src_badge_icon} Water Temp Source: {wt_source.upper()}
  </div>
  <div style="font-size:0.82rem;color:#666;">
    {wt_source_detail} · Confidence: <b>{wt_confidence}</b>
  </div>
</div>
""", unsafe_allow_html=True)

heat_col, timeline_col = st.columns([1.4, 1.0], gap="medium")

with heat_col:
    thermal_map = build_surface_heatmap(
        thermal_grid, lat, lon,
        water_temp=fv.get("water_temp", 20.0),
        water_temp_source=wt_source,
        source_detail=wt_source_detail,
    )
    st_folium(thermal_map, height=420, width="100%", returned_objects=[])

with timeline_col:
    sat_7d = temp_info.get("satellite_skin_7d", [])
    sat_dates = temp_info.get("satellite_skin_dates", [])
    fig_timeline = build_temp_timeline(sat_7d, sat_dates, wt_source)
    if fig_timeline:
        st.plotly_chart(fig_timeline, width='stretch', config={"displayModeBar": False})
    else:
        st.info("📊 Insufficient 7-day satellite skin temperature data for timeline chart.")

    # Temperature comparison panel
    est_temp = fv["temperature"].get("water_temp", 0)
    air_temp_now = fv["temperature"].get("current_air_temp", 0)
    baseline = fv["temperature"].get("seasonal_baseline", 0)
    anomaly = fv["temperature"].get("temp_anomaly_c", 0)

    st.markdown(f"""
    <div style="background:#f0f9ff;border-radius:8px;padding:12px 16px;margin-top:8px;
                border:1px solid #bae6fd;font-size:0.85rem;line-height:1.8;">
      <b>🌡 Temperature Summary</b><br>
      Water Surface: <b>{est_temp:.1f}°C</b> ({wt_source})<br>
      Air Temperature: {air_temp_now:.1f}°C<br>
      Seasonal Baseline: {baseline:.1f}°C<br>
      Anomaly: <b style="color:{'#e74c3c' if anomaly > 2 else '#333'};">{anomaly:+.1f}°C</b><br>
      Bloom Threshold: 25.0°C {'⚠️ EXCEEDED' if est_temp >= 25 else '✅ Below'}
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# ④ Growth Rate + Component Gauges
# ─────────────────────────────────────────────────────────────────────────────
st.subheader("🔬 Biological Growth Rate (Monod Kinetics)")
gauge_col, monod_col = st.columns([1, 1.5], gap="medium")
with gauge_col:
    st.plotly_chart(build_component_gauges(comp), width='stretch', config={"displayModeBar": False})
with monod_col:
    st.plotly_chart(build_monod_factors_chart(gr), width='stretch', config={"displayModeBar": False})

lim = gr.get("limiting_factor", "Unknown")
bio_traj = gr.get("biomass_trajectory", [1.0])
st.caption(
    f"Primary growth limiting factor: **{lim}**. "
    f"Relative biomass after 7 days (starting at 1.0): "
    f"**{bio_traj[-1]:.2f}×** baseline if conditions persist."
)

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# ⑤ 7-Day Forecast
# ─────────────────────────────────────────────────────────────────────────────
st.subheader("📈 7-Day Risk Forecast")
st.plotly_chart(
    build_forecast_chart(forecast),
    width='stretch',
    config={"displayModeBar": False},
)

trend_col, mk_col = st.columns([1, 2])
with trend_col:
    trend_color = {"WORSENING": "#e74c3c", "STABLE": "#f1c40f", "IMPROVING": "#2ecc71"}.get(trend["trend"], "#aaa")
    st.markdown(f"""
    <div style="background:{trend_color}22;border-left:4px solid {trend_color};
                border-radius:6px;padding:10px 14px;">
      <b>30-Day Trend: {trend['direction_emoji']} {trend['trend']}</b><br>
      Slope: {trend['slope_per_day']:+.2f} pts/day · p={trend['p_value']:.3f}
    </div>
    """, unsafe_allow_html=True)
with mk_col:
    st.caption(trend["description"])

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# ⑥ WHO Comparison + Live Conditions
# ─────────────────────────────────────────────────────────────────────────────
who_col, cond_col = st.columns([1, 1], gap="medium")

with who_col:
    st.subheader("🏥 WHO Threshold Comparison")
    st.markdown(f"**Estimated concentration:** {who_info['estimated_cells_formatted']} cells/mL")
    st.markdown(f"{who_info['proximity_text']}")

    thresholds = who_info["thresholds"]
    fig_who = _build_who_bar(cells, thresholds, who_info["risk_color"])
    st.plotly_chart(fig_who, width='stretch', config={"displayModeBar": False})

with cond_col:
    st.subheader("🌡 Real-Time Conditions")
    current = (raw.get("weather") or {}).get("current", {})
    conditions = {
        "🌡 Air Temperature":   f"{current.get('temperature', 0):.1f}°C",
        "🌊 Water Temperature": f"{fv.get('water_temp', 0):.1f}°C ({wt_source})",
        "💧 Humidity":          f"{current.get('humidity', 0):.0f}%",
        "💨 Wind Speed":        f"{current.get('wind_speed', 0):.1f} km/h",
        "☀️ UV Index":          f"{current.get('uv_index', 0):.1f}",
        "☁️ Cloud Cover":       f"{current.get('cloud_cover', 0):.0f}%",
        "🌧 Rain (48h)":        f"{fv['precipitation'].get('rainfall_48h', 0):.1f} mm",
        "🏞 Stagnation Idx":    f"{fv['precipitation'].get('stagnation_index', 0):.2f}",
        "🌾 Agricultural %":    f"{fv['nutrients'].get('agricultural_pct', 0):.0f}%",
        "🏙 Urban %":           f"{fv['nutrients'].get('urban_pct', 0):.0f}%",
    }
    cond_df = pd.DataFrame({"Condition": list(conditions.keys()), "Value": list(conditions.values())})
    st.dataframe(cond_df, hide_index=True)
    st.caption(f"Fetched: {freshness}")

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# ⑥b Data Reliability Panel
# ─────────────────────────────────────────────────────────────────────────────
with st.expander("📋 Data Reliability & Source Details", expanded=False):
    r1, r2, r3, r4 = st.columns(4)
    data_errors = dq.get("errors", {})

    with r1:
        weather_ok = "weather" not in data_errors
        st.markdown(f"""
        **Open-Meteo Weather** {'🟢' if weather_ok else '🔴'}
        - Status: {'Live · Real-time' if weather_ok else 'Error: ' + data_errors.get('weather','')}
        - Coverage: Global (0.1° resolution)
        - Latency: <5 min
        - API: Free, no key required
        """)
    with r2:
        cyfi_ok = "cyfi" not in data_errors
        cyfi_src = (raw.get("cyfi") or {}).get("source", "unknown")
        st.markdown(f"""
        **CyFi Satellite ML** {'🟢' if cyfi_ok else '🟡'}
        - Status: {'Active' if cyfi_ok else 'Fallback'} · Source: {cyfi_src}
        - Model: Random Forest on Sentinel-2
        - Validated by: NASA / DrivenData
        - Note: Best for lakes >1 km²
        """)
    with r3:
        hist_ok = "historical_temp" not in data_errors
        land_ok = "land_use" not in data_errors
        st.markdown(f"""
        **Historical & Land Use** {'🟢' if (hist_ok and land_ok) else '🟡'}
        - Temperature history: {'5 years ✓' if hist_ok else '⚠️ Partial'}
        - Land use: {'ESA WorldCover ✓' if land_ok else '⚠️ Default'}
        - Rainfall history: {'30 days ✓' if 'rainfall_history' not in data_errors else '⚠️ Partial'}
        """)
    with r4:
        thermal_ok = "satellite_thermal" not in data_errors
        thermal_src = temp_info.get("water_temp_source_detail", "Unknown")
        st.markdown(f"""
        **Satellite Thermal** {'🟢' if thermal_ok and wt_source == 'satellite' else ('🟡' if thermal_ok else '🔴')}
        - Source: {thermal_src[:40]}
        - Water temp: {wt_source.title()} · {wt_confidence}
        - Resolution: {(raw.get('satellite_thermal') or {}).get('resolution', '~25 km')}
        - Fallback: Air→Water model (L&L 1998)
        """)

    if data_errors:
        st.warning(f"⚠️ Degraded sources: {', '.join(data_errors.keys())}. Results use scientifically-grounded fallback values.")
    else:
        st.success("✅ All data sources operational — maximum confidence.")

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# ⑦ Health Advisory
# ─────────────────────────────────────────────────────────────────────────────
st.subheader("🚨 Health Advisory")
adv_bg = banner_bg.get(risk_level, "#f0f0f0")
st.markdown(f"""
<div style="background:{adv_bg};border:1px solid {risk_color};border-radius:8px;padding:16px 20px;line-height:1.7;">
  {advisory}
</div>
""", unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# ⑧ PDF Download + Metadata
# ─────────────────────────────────────────────────────────────────────────────
st.subheader("📥 Download Report")
pdf_col, meta_col = st.columns([1, 2])
with pdf_col:
    with st.spinner("Generating PDF…"):
        try:
            pdf_bytes = generate_pdf_report(
                location={"lat": lat, "lon": lon},
                risk_result=risk,
                feature_vector=fv,
                growth_rate=gr,
                forecast=forecast,
                trend=trend,
                who_info=who_info,
            )
            st.download_button(
                label="📄 Download PDF Report",
                data=pdf_bytes,
                file_name=f"aquawatch_report_{lat:.2f}_{lon:.2f}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
            )
        except Exception as e:
            st.error(f"PDF generation error: {e}")

with meta_col:
    st.markdown(f"""
    <div style="background:#f8fafc;border-radius:8px;padding:14px 18px;font-size:0.85rem;line-height:1.8;">
      <b>📍 Location:</b> {lat:.4f}, {lon:.4f}<br>
      <b>🕐 Fetched:</b> {fetched_at_str[:19] if fetched_at_str else 'Unknown'} · {freshness}<br>
      <b>🎯 Confidence:</b> {confidence}<br>
      <b>🌦 Weather:</b> Open-Meteo API (real-time, free)<br>
      <b>🛰 Satellite:</b> CyFi (NASA/DrivenData)<br>
      <b>🌡 Water Temp:</b> {wt_source.title()} — {wt_source_detail}<br>
      <b>🗺 Land use:</b> ESA WorldCover v200<br>
      <b>🏥 Thresholds:</b> WHO 2003 Recreational Water Guidelines
    </div>
    """, unsafe_allow_html=True)


