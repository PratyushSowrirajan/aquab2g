# AquaWatch — Complete Project Plan
## Cyanobacteria Detection & Water Contamination Risk Early Warning System

**Last Updated:** 18 February 2026  
**Status:** Planning Phase  

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [The Problem](#2-the-problem)
3. [The Solution](#3-the-solution)
4. [Scientific Foundation](#4-scientific-foundation)
5. [Data Sources](#5-data-sources)
6. [Mathematical & Statistical Models](#6-mathematical--statistical-models)
7. [System Architecture](#7-system-architecture)
8. [Tech Stack](#8-tech-stack)
9. [Project Structure](#9-project-structure)
10. [Implementation Phases](#10-implementation-phases)
11. [Demo Sites](#11-demo-sites)
12. [Validation Strategy](#12-validation-strategy)
13. [Dashboard Design](#13-dashboard-design)
14. [Risk & Mitigation](#14-risk--mitigation)
15. [References](#15-references)

---

## 1. Project Overview

**AquaWatch** is a water contamination risk early warning platform focused on **cyanobacteria bloom detection and prediction**. It uses satellite-derived data, live weather APIs, land-use classification, and biologically-grounded mathematical models to predict the probability of harmful algal blooms — **24 to 72 hours before they're detectable on the ground**.

**Core Input:** Latitude + Longitude  
**Core Output:** Risk score (0–100) with WHO severity level, 7-day forecast trajectory, spatial risk heatmap, and plain-English health advisory.

**Cost to run:** $0. Every data source is free and open.

---

## 2. The Problem

- Over **2 billion people** drink contaminated water globally.
- Traditional water quality testing requires physical samples, lab equipment ($1000s), and 48–72 hours of processing.
- This system **completely breaks down** in rural areas, developing regions, and disaster zones.
- Governments monitoring large water bodies rely on **spot checks at fixed points**, missing bloom events between stations.
- **Gap:** No free, accessible, globally usable tool gives health workers an early warning before contamination becomes an outbreak.

### Cyanobacteria Specifically

- Cyanobacteria (blue-green algae) produce **microcystins, cylindrospermopsins, anatoxins** — toxins that cause:
  - Liver damage
  - Skin rashes
  - Gastrointestinal illness
  - Neurological effects
  - Death in extreme cases (livestock, pets, humans)
- Blooms are **increasing worldwide** due to climate change (warmer water) and agricultural intensification (more nutrient runoff).
- WHO estimates harmful algal blooms affect **every continent**.

---

## 3. The Solution

### What AquaWatch Does

1. User enters a **latitude and longitude** (or selects a demo site)
2. System fetches **live weather data** (temperature, rainfall, wind, UV)
3. System loads **land-use classification** (agricultural %, urban %, forest %)
4. System loads **CyFi cyanobacteria prediction** (pre-computed, NASA-validated)
5. System computes **6 mathematical models** to produce:
   - Current cyanobacteria risk score (0–100)
   - 7-day forecast trajectory with confidence bands
   - 30-day trend analysis (worsening / stable / improving)
   - Spatial risk heatmap over the water body
   - WHO alert level classification
   - Plain-English health advisory

### What AquaWatch Does NOT Do

- It does NOT see bacteria from space (impossible)
- It does NOT replace lab testing (it supplements it)
- It DOES detect the **environmental conditions** that are **strongly correlated** with bloom formation — and that IS scientifically validated

---

## 4. Scientific Foundation

### The Causal Chain

```
SUNLIGHT + WARM WATER + NUTRIENTS + STAGNATION
              ↓
    Cyanobacteria Multiply Exponentially
              ↓
    Bloom Forms (visible from satellite)
              ↓
    Toxins Released (microcystins, anatoxins)
              ↓
    HEALTH RISK
```

### Why Temperature Is the Primary Driver

| Temperature Range | Biological Effect | Source |
|---|---|---|
| < 15°C | Minimal cyanobacteria growth | Robarts & Zohary (1987) |
| 15–20°C | Slow growth, low risk | Paerl & Huisman (2008) |
| 20–25°C | Moderate growth, rising risk | Reynolds (2006) |
| **25–30°C** | **Rapid growth — optimal bloom range** | Paerl & Huisman (2008) |
| 30–35°C | Peak bloom, some species stressed | O'Neil et al. (2012) |
| > 35°C | Growth inhibited for most species | Robarts & Zohary (1987) |

### Why Nutrients Matter

- **Nitrogen (N)** and **Phosphorus (P)** are the primary fuel for cyanobacteria.
- Agricultural fertilizer runoff is the #1 source globally.
- We CANNOT measure N/P from satellite or weather APIs.
- We CAN estimate nutrient loading through a **proxy model**: `land_use × rainfall × season`.

### Why Stagnation Matters

- Cyanobacteria regulate **buoyancy** — they float to the surface for light.
- In calm, stratified water, they accumulate at the surface → visible bloom / scum.
- Wind mixing disrupts this → disperses cells → reduces surface concentration.
- Rainfall flushes water bodies → reduces residence time → dilutes nutrients.

### Published Literature Supporting This Approach

| Paper | Finding | Relevance |
|---|---|---|
| Paerl & Huisman (2008) "Blooms Like It Hot" — *Science* | Climate warming directly promotes cyanobacteria dominance | Temperature as primary predictor |
| Downing et al. (2001) — *Can J Fish Aquat Sci* | Cyanobacteria dominance predictable from total phosphorus + temperature | Multi-parameter prediction |
| Beaulac & Reckhow (1982) | Nutrient export coefficients by land-use type | Nutrient proxy from land use |
| Robarts & Zohary (1987) — *Can J Fish Aquat Sci* | Temperature response curves for cyanobacteria species | Growth rate model calibration |
| Reynolds (2006) — *Cambridge Univ Press* | Ecology of phytoplankton — comprehensive growth models | Monod kinetics application |
| Huisman et al. (2004) — *Ecology* | Turbulent mixing shifts competition for light | Stagnation → bloom mechanism |

---

## 5. Data Sources

### 5.1 Open-Meteo API (LIVE — Primary Input)

| Field | What We Use It For | Endpoint |
|---|---|---|
| Air temperature (current) | Water temperature proxy, absolute bloom threshold | `/v1/forecast` |
| Air temperature (7-day history) | Temperature trend, anomaly detection | `/v1/forecast?past_days=7` |
| Air temperature (10-year history) | Seasonal baseline, z-score calculation | `/v1/archive` |
| Air temperature (7-day forecast) | Forward bloom trajectory prediction | `/v1/forecast` |
| Precipitation (30-day history) | Stagnation index, runoff events, nutrient flush | `/v1/archive` |
| Precipitation (7-day forecast) | Predicted nutrient flush events | `/v1/forecast` |
| Wind speed + direction | Mixing index, bloom accumulation shore | `/v1/forecast` |
| UV index | Light availability for photosynthesis | `/v1/forecast` |
| Cloud cover | Photosynthesis suppression factor | `/v1/forecast` |
| Humidity | Evaporation rate, concentration effect | `/v1/forecast` |

**Cost:** Free, no API key, no rate limits for basic use.  
**Latency:** Real-time for current; historical archive available.

### 5.2 ESA WorldCover (STATIC — Pre-downloaded)

| Class Code | Class Name | Our Use |
|---|---|---|
| 10 | Tree cover | Forest % (low nutrient export) |
| 20 | Shrubland | Combined with forest |
| 30 | Grassland | Moderate nutrient export |
| **40** | **Cropland** | **Agricultural % → HIGH nutrient export** |
| **50** | **Built-up** | **Urban % → sewage/fertilizer runoff** |
| 60 | Bare / sparse vegetation | Minimal |
| 80 | Permanent water bodies | Water body identification |
| 90 | Herbaceous wetland | Nutrient absorption buffer |

**Resolution:** 10 meters globally.  
**Cost:** Free download from ESA.  
**Processing:** Download GeoTIFF tiles for demo regions, sample within 5km radius of each point.

### 5.3 CyFi — Cyanobacteria Finder (NASA-validated ML)

| Property | Detail |
|---|---|
| What it does | Predicts cyanobacteria density (cells/mL) + WHO severity level |
| Input | Latitude, longitude, date |
| Satellite source | Sentinel-2 MSI (10m resolution) |
| Training data | 8,979 in-situ observations from across the US |
| Validation data | 4,035 independent observations |
| Output | cells/mL estimate + severity (low/moderate/high/very_high) |
| Developed by | DrivenData for NASA, with NOAA, EPA, USGS, Microsoft |

**Strategy for our project:**
- CyFi is SLOW (~2-5 min per point, downloads Sentinel-2 imagery).
- **Pre-compute** predictions for demo sites across multiple dates.
- **Cache** results in JSON files.
- Use cached values in live dashboard.
- Use as **validation benchmark** for our own temperature-based model.

### 5.4 USGS Water Quality Portal (Training + Validation)

| Parameter | USGS Name | Records Available | Our Use |
|---|---|---|---|
| Chlorophyll-a | "Chlorophyll a" | Millions (US) | Ground truth for bloom presence |
| Water temperature | "Temperature, water" | Millions | Validate our air→water temp proxy |
| E. coli | "Escherichia coli" | Millions | Organic contamination reference |
| Turbidity | "Turbidity" | Millions | Suspended solids proxy |
| Nitrate | "Nitrate" | Hundreds of thousands | Validate nutrient proxy model |
| Phosphorus | "Phosphorus" | Hundreds of thousands | Validate nutrient proxy model |

**URL:** `https://www.waterqualitydata.us/`  
**Cost:** Free, REST API, bulk CSV download.  
**Our use:** Pull historical data for Lake Erie region → train/validate models.

### 5.5 Calculated / Derived Inputs

| Input | Calculation Method |
|---|---|
| Day length (photoperiod) | Astronomical formula from latitude + date |
| Solar declination | `23.45 × sin(360/365 × (day_of_year - 81))` |
| Season classification | Day of year + hemisphere |
| Water temperature estimate | `0.65 × T_air_current + 0.35 × T_air_7day_avg - wind_cooling + humidity_correction` |

---

## 6. Mathematical & Statistical Models

### Overview: 6 Models Feeding into 1 Final Score

```
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│ MODEL 1             │  │ MODEL 2             │  │ MODEL 3             │
│ Temperature Anomaly │  │ Nutrient Loading     │  │ Stagnation Index    │
│ Z-score + absolute  │  │ Land use × rainfall  │  │ Wind + rain deficit │
│ threshold           │  │ × season proxy       │  │ + stratification    │
└────────┬────────────┘  └────────┬────────────┘  └────────┬────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────────┐  ┌─────────────────────────────────────────────┐
│ MODEL 4             │  │ MODEL 5: GROWTH RATE (Monod Kinetics)      │
│ Light / UV Score    │  │ µ = µ_max × f(T) × f(N) × f(L) × f(S)    │
│ UV + photoperiod    │  │ Combines all 4 input models biologically   │
│ + cloud cover       │  │ Projects biomass over 7 days               │
└────────┬────────────┘  └────────────────────┬────────────────────────┘
         │                                     │
         └──────────────┬──────────────────────┘
                        ▼
         ┌──────────────────────────────┐
         │ MODEL 6: BLOOM PROBABILITY   │
         │ Logistic / geometric mean    │
         │ → Risk Score (0-100)         │
         │ → WHO Severity Level         │
         │ → 7-Day Forecast             │
         │ → Confidence Interval        │
         └──────────────────────────────┘
```

---

### MODEL 1: Temperature Anomaly Score

**Question:** Is this water body abnormally warm right now?

**Inputs:**
- `T_current` — today's air temperature (Open-Meteo live)
- `T_historical[]` — temperatures for same calendar week, last 5-10 years (Open-Meteo archive)

**Calculations:**

1. **Seasonal baseline** using harmonic regression:
   ```
   T_baseline(t) = a + b × sin(2π × day_of_year / 365) + c × cos(2π × day_of_year / 365)
   ```
   Coefficients a, b, c fitted via least-squares on 5-10 years of historical data.

2. **Z-score anomaly:**
   ```
   μ = mean(T_historical for same month)
   σ = std(T_historical for same month)
   Z = (T_current - μ) / σ
   ```

3. **Absolute biological threshold overlay:**
   - < 15°C → inherently LOW (score 5)
   - 15–20°C → moderate baseline (score 20–40)
   - 20–25°C → elevated (score 40–65)
   - 25–30°C → HIGH — optimal bloom range (score 65–90)
   - 30–35°C → VERY HIGH but some species stressed (score 85–95)
   - > 35°C → slight decrease (score 80)

4. **Combined temperature risk:**
   ```
   temp_risk = sigmoid(α × Z_score + β × absolute_bracket) × 100
   ```
   Uses sigmoid to combine both signals smoothly.

5. **Warming trend bonus:**
   ```
   7-day trend = linear regression slope on last 7 daily temps
   If slope > +0.3°C/day → add 10-20 bonus points (bloom accelerating)
   ```

6. **Temperature percentile:**
   ```
   percentile = percentileofscore(historical_same_month, T_current)
   If percentile > 90 → "unusually warm"
   If percentile > 95 → "extremely warm"
   ```

**Output:** Temperature Risk Score (0–100) + contributing factors list

**Statistical techniques used:**
- Z-score anomaly detection
- Harmonic regression (sinusoidal seasonal fit)
- Sigmoid combination function
- Linear regression (trend)
- Percentile ranking

---

### MODEL 2: Nutrient Loading Estimation

**Question:** How much nitrogen/phosphorus is likely entering this water body right now?

**Inputs:**
- `agricultural_pct` — % cropland within 5km (ESA WorldCover)
- `urban_pct` — % built-up within 5km (ESA WorldCover)
- `forest_pct` — % tree cover within 5km (ESA WorldCover)
- `wetland_pct` — % wetland within 5km (ESA WorldCover)
- `rainfall_48h` — precipitation in last 48 hours (Open-Meteo)
- `rainfall_7d` — precipitation in last 7 days (Open-Meteo)
- `days_since_significant_rain` — days since last >5mm event
- `season` — current season / growing season status

**Calculations:**

1. **Land-use nutrient export coefficient** (from Beaulac & Reckhow, 1982):
   ```
   land_coeff = (ag_pct × 0.80 + urban_pct × 0.50 + grassland_pct × 0.20 
                 + forest_pct × 0.10 + wetland_pct × 0.05) / 100
   ```

2. **Rainfall delivery mechanism:**
   - Dry period → rain = "first flush" (highest nutrient concentration in runoff)
   ```
   If days_since_rain > 5 AND rainfall_48h > 10mm:
       delivery_score = 0.90  (classic first flush)
   Elif rainfall_48h > 20mm:
       delivery_score = 0.70  (heavy runoff)
   Elif rainfall_7d > 30mm:
       delivery_score = 0.50  (sustained loading)
   Elif rainfall_48h > 5mm:
       delivery_score = 0.30  (moderate)
   Else:
       delivery_score = 0.15  (dry — existing nutrients only)
   ```

3. **Seasonal weight:**
   ```
   Growing season (Apr-Sep NH): weight = 1.0
   Post-harvest (Oct-Nov):      weight = 0.8
   Winter (Dec-Mar):            weight = 0.3
   
   For Southern Hemisphere: shift by 6 months
   ```

4. **Nutrient loading score:**
   ```
   N_score = land_coeff × delivery_score × seasonal_weight × 100
   ```

**Output:** Nutrient Loading Score (0–100) + contributing factors list

**Key insight:** We don't need exact mg/L of nitrogen. We need a RELATIVE score — is nutrient loading HIGH, MEDIUM, or LOW right now? The proxy model gives us that.

---

### MODEL 3: Stagnation Index

**Question:** Is the water body stagnant enough for surface bloom accumulation?

**Inputs:**
- `avg_wind_7d` — average wind speed over last 7 days (Open-Meteo)
- `current_wind` — current wind speed (Open-Meteo)
- `rainfall_deficit` — actual vs expected 30-day rainfall (Open-Meteo)
- `temp_max - temp_min` — diurnal temperature range (Open-Meteo)
- `water_temp_estimate` — from Model 1

**Calculations:**

1. **Wind mixing score:**
   ```
   If avg_wind_7d > 20 km/h → 0.10 (well-mixed)
   If avg_wind_7d 10-20      → 0.40 (moderate mixing)
   If avg_wind_7d 5-10       → 0.70 (poor mixing)
   If avg_wind_7d < 5        → 1.00 (stagnant)
   ```

2. **Hydrological stagnation:**
   ```
   expected_rain_30d = median of historical 30-day rainfall totals
   actual_rain_30d = sum of last 30 days rainfall
   
   hydro_stagnation = max(0, 1 - actual_rain_30d / expected_rain_30d)
   ```

3. **Thermal stratification proxy:**
   ```
   If diurnal_range > 10°C AND avg_wind < 10 km/h:
       stratification = 0.80 (strong stratification likely)
   Elif water_temp > 25°C AND avg_wind < 15 km/h:
       stratification = 0.60 (moderate stratification)
   Else:
       stratification = 0.20 (well-mixed)
   ```

4. **Combined stagnation index:**
   ```
   S = 0.40 × wind_mixing + 0.40 × hydro_stagnation + 0.20 × stratification
   S = clip(S, 0, 1) → then scale to 0-100
   ```

**Output:** Stagnation Index (0–100) + contributing factors list

---

### MODEL 4: Light / UV Score

**Question:** Is there enough light to fuel rapid cyanobacteria photosynthesis?

**Inputs:**
- `uv_index` — current UV index (Open-Meteo)
- `cloud_cover` — current cloud cover % (Open-Meteo)
- `latitude` — for photoperiod calculation
- `day_of_year` — for photoperiod + seasonal cycle

**Calculations:**

1. **UV component:**
   ```
   uv_score = min(uv_index / 11.0, 1.0)  (normalized to max UV ≈ 11)
   ```

2. **Photoperiod (day length) calculation:**
   ```
   declination = 23.45 × sin(2π/365 × (day_of_year - 81))
   hour_angle = arccos(-tan(latitude_rad) × tan(declination_rad))
   day_length_hours = 2 × hour_angle / 15
   
   photoperiod_score = min(day_length_hours / 16.0, 1.0)
   ```

3. **Cloud suppression:**
   ```
   cloud_factor = 1 - (cloud_cover_pct / 100 × 0.60)
   (Clouds reduce but don't eliminate photosynthesis — cyanobacteria are shade-adapted)
   ```

4. **Combined light score:**
   ```
   L = (0.50 × uv_score + 0.30 × photoperiod_score + 0.20 × cloud_factor) × 100
   ```

**Output:** Light Availability Score (0–100)

---

### MODEL 5: Growth Rate Estimation (Biological Core)

**Question:** Given all environmental conditions, how fast are cyanobacteria likely growing?

**This is the heart of the system.** It uses **Monod kinetics** — the standard model for microbial growth rates used in ecology for 80+ years.

**Inputs:** Output scores from Models 1–4

**Calculations:**

1. **Maximum growth rate:**
   ```
   µ_max = 1.0 per day (published value for Microcystis aeruginosa)
   ```

2. **Temperature limitation function** (Gaussian response curve):
   ```
   f(T) = exp(-((T_water - T_optimal)² / (2 × σ_T²)))
   
   Where:
     T_optimal = 28°C (optimal for Microcystis)
     σ_T = 5°C (spread of tolerance)
   
   Result:
     At 15°C → f(T) = 0.07 (almost no growth)
     At 20°C → f(T) = 0.33 (slow)
     At 25°C → f(T) = 0.73 (rapid)
     At 28°C → f(T) = 1.00 (maximum)
     At 33°C → f(T) = 0.61 (heat stress)
   ```

3. **Nutrient limitation function** (Monod form):
   ```
   f(N) = N_score / (N_score + K_N)
   
   Where K_N = 50 (half-saturation constant, normalized)
   
   When nutrients abundant (N_score=90): f(N) = 0.64
   When nutrients scarce (N_score=10):   f(N) = 0.17
   When nutrients extreme (N_score=100): f(N) = 0.67
   ```

4. **Stagnation benefit function:**
   ```
   f(S) = 0.3 + 0.7 × (stagnation_score / 100)
   
   Minimum 0.3 because blooms can still grow in flowing water, just slower
   Maximum 1.0 in perfectly stagnant conditions
   ```

5. **Light limitation function:**
   ```
   f(L) = light_score / 100
   ```

6. **Daily growth rate:**
   ```
   µ_daily = µ_max × f(T) × f(N) × f(L) × f(S)
   ```

7. **Doubling time:**
   ```
   T_double = ln(2) / µ_daily (in days)
   
   At µ=1.0: doubling every 16.6 hours (EXPLOSIVE)
   At µ=0.5: doubling every 1.4 days
   At µ=0.1: doubling every 6.9 days (slow)
   At µ=0.01: doubling every 69 days (negligible)
   ```

8. **7-day biomass projection:**
   ```
   B(t) = B_0 × exp(µ_daily × t)
   
   Where B_0 = estimated current biomass
   t = 1 to 7 days
   
   For each forecast day, recalculate µ using weather forecast inputs
   ```

**Output:**
- Daily growth rate (µ)
- Doubling time
- 7-day projected biomass trajectory
- Each limitation factor value (for explainability)

---

### MODEL 6: Bloom Probability — Final Risk Score

**Question:** What is the overall probability of a harmful bloom?

**Approach: Weighted geometric mean**

```
RISK = 100 × (temp_risk^w₁ × nutrient_risk^w₂ × stagnation_risk^w₃ × light_risk^w₄)^(1/Σw)

Where:
  w₁ = 0.35 (temperature — strongest driver)
  w₂ = 0.25 (nutrients — essential fuel)
  w₃ = 0.22 (stagnation — accumulation mechanism)
  w₄ = 0.18 (light — photosynthesis driver)
```

**Why geometric mean, NOT arithmetic mean?**
- If ANY factor is near zero (e.g., temperature is 5°C), overall score drops dramatically.
- This reflects biological reality: cyanobacteria NEED ALL conditions to align.
- Arithmetic mean would show moderate risk even if temperature is freezing — that's wrong.

**Interaction amplification:**
```
Count factors where score > 70:
  If 3 or 4 factors > 70 → multiply final score by 1.15 (synergistic amplification)
  If 2 factors > 70       → multiply by 1.05
  If 0 or 1              → no amplification

Why: Warm water + high nutrients simultaneously = EXPLOSIVE risk
     The interaction is super-additive, not just additive
```

**Risk-to-cells mapping (log-linear):**
```
estimated_cells_per_mL = 10^(0.049 × risk_score + 2.83)

Calibrated so:
  Score 30 → ~20,000 cells/mL (WHO low threshold)
  Score 60 → ~100,000 cells/mL (WHO moderate threshold)  
  Score 85 → ~10,000,000 cells/mL (WHO high threshold)
```

**WHO severity classification:**
```
< 20,000 cells/mL      → LOW        → "Low probability of adverse health effects"
20,000–100,000          → MODERATE   → "Moderate probability, advisory recommended"
100,000–10,000,000      → HIGH       → "High probability, avoid direct contact"
> 10,000,000            → VERY HIGH  → "Acute danger, do not use water"
```

**Confidence estimation:**
```
HIGH confidence:   All data sources available AND data < 24hrs old AND CyFi available
MEDIUM confidence: Weather live but satellite data > 48hrs old OR CyFi unavailable
LOW confidence:    Only weather + land use available (still useful but less precise)
```

**Output:**
- Risk Score (0–100)
- Estimated cyanobacteria density (cells/mL)
- WHO Severity Level (LOW / MODERATE / HIGH / VERY HIGH)
- Confidence Level
- Primary risk driver (which component contributes most)
- Contributing factors (plain English list)

---

## 6.5 Advanced Statistical Features

### 7-Day Forward Prediction

```
Method:
  Open-Meteo provides 7-day weather FORECAST (free)
  
  For each forecast day (t+1 through t+7):
    1. Get forecast temperature, precipitation, wind, UV
    2. Recompute Models 1-4 with forecast inputs
    3. Feed into Model 5 (growth rate)
    4. Project biomass: B(t+1) = B(t) × exp(µ(t))
    5. Convert to risk score via Model 6
    
  Result: 7-point risk trajectory with trend direction

Uncertainty quantification (Monte Carlo):
  Weather forecasts degrade over time:
    Day 1: ±1°C uncertainty
    Day 3: ±2°C uncertainty
    Day 7: ±4°C uncertainty
  
  Method:
    For each forecast day, sample 100 temperature scenarios 
    from Normal(forecast_temp, uncertainty_σ)
    Run full model pipeline for each sample
    Report: median risk + 10th/90th percentile confidence band
    
  Display: "Day 5 risk: 72 (range: 58–84)"
```

### 30-Day Trend Analysis (Mann-Kendall Test)

```
Method:
  Compute daily risk scores retroactively for last 30 days
  (using historical weather from Open-Meteo archive)
  
  Apply Mann-Kendall trend test:
    S = Σᵢ Σⱼ sign(score_j - score_i) for all i < j
    
    If S >> 0 → WORSENING (risk increasing over time)
    If S ≈ 0  → STABLE (no significant trend)
    If S << 0 → IMPROVING (risk decreasing over time)
    
    p-value determines statistical significance
  
  Sen's slope estimator:
    slope = median of all (score_j - score_i) / (j - i)
    "Risk is increasing by approximately X points per day"

Why Mann-Kendall (not linear regression)?
  - Non-parametric — doesn't assume normal distribution
  - Robust to outliers (one weird weather day doesn't skew result)
  - Standard method in environmental science for trend detection
```

### Spatial Risk Mapping

```
Method: Inverse Distance Weighting (IDW) interpolation

  1. Define grid of points over water body surface
  2. For each grid point, compute micro-adjustments:
     - Distance to agricultural land (closer = higher nutrient input)
     - Distance to urban discharge points (closer = higher organic load)
     - Shallow vs deep areas (shallow warms faster = higher risk)
     - Wind direction (downwind shores accumulate surface scum)
  
  3. IDW interpolation:
     Risk(x,y) = Σ(Risk_i × w_i) / Σ(w_i)
     Where w_i = 1 / distance(x,y to point_i)²
  
  4. Wind direction adjustment:
     Cyanobacteria scum accumulates on DOWNWIND shore
     If wind blows NW → SE shore risk amplified by 20-40%
  
  5. Render as Folium heatmap overlay:
     Green (safe) → Yellow (moderate) → Red (critical)
```

### Water Temperature Estimation from Air Temperature

```
Published empirical model:
  Livingstone & Lotter (1998), Boreal Environment Research

  T_water = 0.65 × T_air_current + 0.35 × T_air_7day_avg 
            - wind_cooling + humidity_correction

  wind_cooling = max(0, (wind_speed - 5) × 0.08)
  humidity_correction = (humidity - 50) / 100 × 1.5

  Water temp typically 1-3°C below air temp in summer
  Water temp above air temp in autumn (thermal inertia)
```

---

## 7. System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    USER INPUT                           │
│              Latitude + Longitude                       │
│              (or select demo site)                      │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│                  DATA FETCH LAYER                       │
│                                                         │
│  Open-Meteo API (LIVE)                                  │
│  → Current temperature, wind, UV, humidity              │
│  → 7-day history                                        │
│  → 7-day forecast                                       │
│  → 5-10 year historical archive                         │
│                                                         │
│  ESA WorldCover (STATIC — pre-loaded GeoTIFF)          │
│  → Agricultural %, urban %, forest % within 5km        │
│                                                         │
│  CyFi Predictions (CACHED — pre-computed)              │
│  → Cyanobacteria density + WHO severity                │
│                                                         │
│  USGS WQP (FOR VALIDATION — historical CSV)            │
│  → Chlorophyll-a, temperature, nutrients ground truth  │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│               FEATURE ENGINEERING LAYER                 │
│                                                         │
│  Temperature Features:                                  │
│  → Z-score anomaly, seasonal baseline, percentile      │
│  → Warming trend (7-day slope)                         │
│  → Water temp estimate from air temp                   │
│                                                         │
│  Precipitation Features:                                │
│  → Stagnation index, days since rain                   │
│  → Runoff event detection (first flush)                │
│  → 30-day rainfall deficit                             │
│                                                         │
│  Nutrient Features:                                     │
│  → Land-use export coefficient                         │
│  → Rainfall × land-use delivery score                  │
│  → Seasonal weighting                                  │
│                                                         │
│  Light Features:                                        │
│  → UV score, photoperiod, cloud suppression            │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│                  MODEL LAYER                            │
│                                                         │
│  Model 1: Temperature Anomaly Score (0–100)            │
│  Model 2: Nutrient Loading Score (0–100)               │
│  Model 3: Stagnation Index (0–100)                     │
│  Model 4: Light Availability Score (0–100)             │
│  Model 5: Growth Rate (Monod kinetics) → µ per day    │
│  Model 6: Final Bloom Probability (geometric mean)     │
│                                                         │
│  + Monte Carlo uncertainty for 7-day forecast          │
│  + Mann-Kendall trend test on 30-day history           │
│  + IDW spatial interpolation for heatmap               │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│                  OUTPUT LAYER                           │
│                                                         │
│  Overall Risk Score: 0–100                             │
│  WHO Severity: LOW / MODERATE / HIGH / VERY HIGH       │
│  Estimated cells/mL                                    │
│  Confidence: LOW / MEDIUM / HIGH                       │
│  Primary driver + contributing factors                 │
│  7-day trajectory with confidence bands                │
│  30-day trend: WORSENING / STABLE / IMPROVING          │
│  Spatial risk heatmap                                  │
│  Plain English alert + recommended action              │
│  Downloadable PDF report                               │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│                  STREAMLIT DASHBOARD                    │
│                                                         │
│  Location selector + coordinates input                 │
│  Interactive Folium map with risk heatmap              │
│  Risk gauge charts (Plotly)                            │
│  7-day forecast line chart with uncertainty bands      │
│  Component breakdown cards                             │
│  Growth rate indicator + doubling time                 │
│  WHO alert banner                                      │
│  Health advisory text                                  │
│  PDF download button                                   │
└─────────────────────────────────────────────────────────┘
```

---

## 8. Tech Stack

| Layer | Tool | Version | Why |
|---|---|---|---|
| **Language** | Python | 3.10+ | Scientific computing ecosystem |
| **UI Framework** | Streamlit | Latest | Fastest for data dashboards, free deployment |
| **Maps** | Folium | Latest | Free Leaflet-based maps, heatmap plugin |
| **Charts** | Plotly | Latest | Interactive, confidence bands, gauges |
| **Weather API** | Open-Meteo | - | Free, no key, real-time + historical |
| **Satellite ML** | CyFi | Latest | NASA-validated cyanobacteria detection |
| **Ground Truth** | USGS WQP | - | Millions of free observations via REST API |
| **Land Use** | ESA WorldCover | v200 | 10m global land classification |
| **Geospatial** | Rasterio | Latest | GeoTIFF reading for WorldCover |
| **Geospatial** | Shapely | Latest | Spatial queries (buffer, distance) |
| **Math** | NumPy | Latest | Core numerical computation |
| **Statistics** | SciPy | Latest | Z-scores, regressions, distributions |
| **Data** | Pandas | Latest | DataFrame operations, time series |
| **Trend Test** | pyMannKendall | Latest | Mann-Kendall trend analysis |
| **ML (optional)** | Scikit-learn | Latest | RandomForest if training on USGS data |
| **PDF** | FPDF2 | Latest | Report generation |
| **Deployment** | Streamlit Cloud | - | Free hosting |
| **Version Control** | GitHub | - | Code repository |

### requirements.txt

```
streamlit>=1.30.0
folium>=0.15.0
streamlit-folium>=0.17.0
plotly>=5.18.0
pandas>=2.1.0
numpy>=1.26.0
scipy>=1.12.0
requests>=2.31.0
rasterio>=1.3.0
shapely>=2.0.0
pymannkendall>=1.4.3
scikit-learn>=1.4.0
fpdf2>=2.7.0
joblib>=1.3.0
```

---

## 9. Project Structure

```
aquawatch/
│
├── app.py                              # Main Streamlit dashboard entry point
├── requirements.txt                    # Python dependencies
├── README.md                           # Project documentation
├── .streamlit/
│   └── config.toml                     # Streamlit theme configuration
│
├── config/
│   ├── __init__.py
│   ├── constants.py                    # WHO thresholds, weights, API URLs
│   ├── demo_sites.py                   # Pre-configured demo locations
│   └── settings.py                     # App-level settings
│
├── data/
│   ├── raw/                            # Downloaded CSV data from USGS
│   ├── processed/                      # Cleaned training/validation sets
│   ├── geospatial/                     # ESA WorldCover GeoTIFF clips
│   └── cache/                          # Cached CyFi + weather results
│
├── data_fetch/
│   ├── __init__.py
│   ├── weather_client.py              # Open-Meteo API integration
│   ├── usgs_client.py                 # USGS Water Quality Portal
│   ├── cyfi_runner.py                 # CyFi prediction wrapper + cache
│   ├── land_use_reader.py             # ESA WorldCover GeoTIFF reader
│   └── data_pipeline.py              # Orchestrator — fetches all data
│
├── features/
│   ├── __init__.py
│   ├── temperature_features.py        # Anomaly, baseline, trend, percentile
│   ├── precipitation_features.py      # Stagnation, runoff, deficit
│   ├── nutrient_features.py           # Land-use proxy, delivery scoring
│   ├── light_features.py             # UV, photoperiod, cloud
│   ├── water_temp_estimator.py        # Air → water temperature model
│   └── feature_pipeline.py           # Combines all features into vector
│
├── models/
│   ├── __init__.py
│   ├── temperature_model.py           # Model 1: Temperature anomaly score
│   ├── nutrient_model.py             # Model 2: Nutrient loading score
│   ├── stagnation_model.py           # Model 3: Stagnation index
│   ├── light_model.py                # Model 4: Light/UV score
│   ├── growth_rate_model.py          # Model 5: Monod kinetics
│   ├── bloom_probability_model.py     # Model 6: Final risk score
│   └── saved/                         # Trained model files (if using ML)
│
├── analysis/
│   ├── __init__.py
│   ├── trend_analysis.py             # Mann-Kendall 30-day trend
│   ├── forecast_engine.py            # 7-day forward prediction
│   ├── uncertainty.py                # Monte Carlo confidence bands
│   ├── spatial_risk.py               # IDW interpolation for heatmap
│   ├── who_comparison.py             # WHO threshold comparison
│   └── hindcast_validation.py        # Validate against known events
│
├── visualization/
│   ├── __init__.py
│   ├── risk_map.py                   # Folium heatmap generation
│   ├── trend_chart.py                # Plotly 7-day trajectory
│   ├── risk_gauge.py                 # Plotly gauge / speedometer
│   ├── component_breakdown.py        # Factor contribution chart
│   ├── growth_rate_display.py        # Doubling time visual
│   └── report_generator.py           # PDF report
│
├── pages/                             # Streamlit multi-page support
│   ├── 1_Dashboard.py                # Main risk dashboard
│   ├── 2_Trends.py                   # Historical trend analysis
│   ├── 3_Methodology.py             # How it works (for judges)
│   └── 4_Validation.py              # Model validation results
│
└── tests/
    ├── test_weather_client.py
    ├── test_features.py
    ├── test_models.py
    ├── test_growth_rate.py
    └── test_analysis.py
```

---

## 10. Implementation Phases

### Phase 1: Foundation (Day 1, Hours 1–4)

**Goal:** Project skeleton, dependencies, configuration

| Task | Deliverable | Time |
|---|---|---|
| Create project structure | All folders + `__init__.py` files | 30 min |
| Write `requirements.txt` | All dependencies listed | 15 min |
| Write `config/constants.py` | WHO thresholds, API URLs, weights | 30 min |
| Write `config/demo_sites.py` | 3 demo site configurations | 15 min |
| Set up basic `app.py` | Streamlit app that runs with placeholder | 30 min |
| Write `data_fetch/weather_client.py` | Open-Meteo integration — test with real API call | 60 min |
| Test: Confirm weather data fetches correctly | Terminal output showing real data | 30 min |

### Phase 2: Data Layer (Day 1, Hours 5–8)

**Goal:** All data sources connected and returning real data

| Task | Deliverable | Time |
|---|---|---|
| Write `data_fetch/land_use_reader.py` | ESA WorldCover reader OR fallback known values | 60 min |
| Write `data_fetch/cyfi_runner.py` | CyFi wrapper with cache + fallback | 60 min |
| Write `data_fetch/data_pipeline.py` | Master orchestrator — fetch all for a location | 30 min |
| Pre-compute CyFi for 3 demo sites | Cached JSON with predictions | 30 min |
| Download USGS data for Lake Erie | CSV files in `data/raw/` | 30 min |
| Test: Full data pipeline for Lake Erie | All data returned in a dict | 30 min |

### Phase 3: Feature Engineering (Day 2, Hours 1–4)

**Goal:** All computed indices working

| Task | Deliverable | Time |
|---|---|---|
| Write `features/temperature_features.py` | Z-score, baseline, trend, percentile, water temp estimate | 60 min |
| Write `features/precipitation_features.py` | Stagnation index, runoff detection, days since rain | 45 min |
| Write `features/nutrient_features.py` | Land-use coefficient, delivery score, seasonal weight | 45 min |
| Write `features/light_features.py` | UV score, photoperiod calculation, cloud factor | 30 min |
| Write `features/feature_pipeline.py` | Combines all features into single feature vector | 30 min |
| Test: Feature vector for all 3 demo sites | Print feature vectors, verify sensibility | 30 min |

### Phase 4: Models (Day 2, Hours 5–8)

**Goal:** All 6 models producing scores

| Task | Deliverable | Time |
|---|---|---|
| Write `models/temperature_model.py` | Model 1 — temp anomaly score 0-100 | 30 min |
| Write `models/nutrient_model.py` | Model 2 — nutrient loading score 0-100 | 30 min |
| Write `models/stagnation_model.py` | Model 3 — stagnation index 0-100 | 20 min |
| Write `models/light_model.py` | Model 4 — light score 0-100 | 20 min |
| Write `models/growth_rate_model.py` | Model 5 — Monod kinetics, doubling time | 45 min |
| Write `models/bloom_probability_model.py` | Model 6 — geometric mean, WHO mapping, confidence | 45 min |
| Test: Full pipeline for all 3 sites | Lake Erie=HIGH, Yamuna=HIGH organic, Vänern=LOW | 30 min |

### Phase 5: Analysis Layer (Day 3, Hours 1–3)

**Goal:** Advanced statistical features working

| Task | Deliverable | Time |
|---|---|---|
| Write `analysis/forecast_engine.py` | 7-day forward prediction using weather forecast | 45 min |
| Write `analysis/uncertainty.py` | Monte Carlo confidence bands | 30 min |
| Write `analysis/trend_analysis.py` | Mann-Kendall 30-day trend test | 30 min |
| Write `analysis/spatial_risk.py` | IDW interpolation for heatmap | 30 min |
| Write `analysis/who_comparison.py` | WHO threshold comparison formatting | 15 min |
| Test: 7-day forecast for Lake Erie | Chart data with confidence bands | 15 min |

### Phase 6: Dashboard UI (Day 3, Hours 4–8)

**Goal:** Complete, polished Streamlit dashboard

| Task | Deliverable | Time |
|---|---|---|
| Write `visualization/risk_map.py` | Folium heatmap with color overlay | 45 min |
| Write `visualization/trend_chart.py` | Plotly 7-day chart with WHO threshold line | 30 min |
| Write `visualization/risk_gauge.py` | Plotly gauge for each risk score | 30 min |
| Write `visualization/component_breakdown.py` | Factor contribution bar chart | 20 min |
| Write `visualization/report_generator.py` | PDF report download | 45 min |
| Write `app.py` — full dashboard layout | Complete UI matching design spec | 90 min |
| Write `pages/3_Methodology.py` | How it works page (for judges) | 30 min |

### Phase 7: Validation & Polish (Day 4)

**Goal:** Proof that it works, final polish

| Task | Deliverable | Time |
|---|---|---|
| Hindcast validation: Lake Erie August 2019 bloom | "Model correctly flags known bloom event" | 60 min |
| Negative validation: Lake Vänern winter | "Model correctly shows LOW risk for clean lake" | 30 min |
| USGS correlation analysis | "Risk score correlates with chlorophyll-a at r=X" | 60 min |
| Write `pages/4_Validation.py` | Validation results page | 45 min |
| UI polish: colors, spacing, responsiveness | Professional-looking dashboard | 60 min |
| Deploy to Streamlit Cloud | Live URL that judges can open | 30 min |
| Write README.md | Complete documentation | 45 min |

---

## 11. Demo Sites

### Site 1: Lake Erie, Ohio, USA 🔴

| Property | Value |
|---|---|
| Coordinates | 41.6833°N, 82.8833°W |
| Why chosen | Known annual cyanobacteria bloom zone (western basin) |
| Expected output | **HIGH** cyanobacteria risk during summer months |
| Validates | Core cyanobacteria detection capability |
| Ground truth available | Yes — USGS WQP, NOAA Great Lakes monitoring, EPA CyAN |
| Notable event | August 2014: Toledo, Ohio drinking water crisis — 500,000 people without water due to microcystin contamination from Lake Erie bloom |

### Site 2: Yamuna River, Delhi, India 🔴

| Property | Value |
|---|---|
| Coordinates | 28.6903°N, 77.2164°E |
| Why chosen | One of the most polluted urban rivers globally |
| Expected output | **HIGH** organic load / sewage contamination |
| Validates | Urban contamination detection, nutrient loading from urban land use |
| Ground truth | India Central Pollution Control Board (CPCB) monitoring |
| Context | 58% of Delhi's sewage enters Yamuna untreated |

### Site 3: Lake Vänern, Sweden 🟢

| Property | Value |
|---|---|
| Coordinates | 58.5500°N, 13.2500°E |
| Why chosen | Large, clean Scandinavian freshwater lake |
| Expected output | **LOW** risk across all categories |
| Validates | Model doesn't just show red everywhere — critical for credibility |
| Ground truth | Swedish EPA / EEA Waterbase monitoring |
| Context | Surrounded by forest, low agricultural pressure, cold climate |

---

## 12. Validation Strategy

### Validation Method 1: Hindcast on Known Bloom Events

```
Take well-documented bloom events:
  - Lake Erie, August 2014 (Toledo water crisis)
  - Lake Erie, August 2019 (massive bloom documented by NOAA)
  - Lake Okeechobee, 2016, 2018 (Florida blooms)

For each event:
  1. Pull historical weather from Open-Meteo for that date/location
  2. Run our full model pipeline
  3. Check: Does it output HIGH risk?
  4. Report: "Model correctly flagged X out of Y known bloom events"
```

### Validation Method 2: Negative Validation

```
Take known CLEAN water bodies during LOW-risk periods:
  - Lake Vänern, Sweden in January
  - Lake Superior in December
  - Mountain lakes in winter

Check: Model MUST output LOW risk.
A model that says everything is dangerous is useless.
```

### Validation Method 3: USGS Ground Truth Correlation

```
1. Pull 1,000+ chlorophyll-a measurements from USGS WQP for Lake Erie
2. For each measurement, compute our risk score retroactively using historical weather
3. Calculate Pearson correlation between our score and actual chlorophyll-a
4. Calculate Spearman rank correlation (non-parametric)
5. Report: "Risk score correlates with measured chlorophyll-a at r=X, p<0.001"
6. Build confusion matrix: our HIGH/LOW vs actual HIGH/LOW chlorophyll-a
7. Report precision, recall, F1 score
```

### Validation Method 4: Cross-reference with CyFi

```
For locations where CyFi can produce predictions:
  1. Run CyFi → get cells/mL and severity
  2. Run our model → get risk score
  3. Compare: Does our HIGH match CyFi's HIGH?
  4. CyFi is NASA-validated, so agreement = credibility
```

---

## 13. Dashboard Design

```
┌─────────────────────────────────────────────────────────────┐
│  💧 AquaWatch — Water Contamination Risk Monitor             │
│  ──────────────────────────────────────────────────────────  │
│                                                              │
│  📍 Location: [Lat ____] [Lng ____]   [🔍 Analyze]          │
│                                                              │
│  ── or select demo site: ──                                  │
│  [Lake Erie 🔴] [Yamuna River 🔴] [Lake Vänern 🟢]          │
│                                                              │
│  Data freshness: Weather ✅ Live | CyFi ⏱ 4hrs ago          │
│                                                              │
├──────────────────────────┬───────────────────────────────────┤
│                          │  🌡️ CURRENT CONDITIONS             │
│                          │  ─────────────────────            │
│   🗺️ RISK MAP            │  Water Temp: 28.4°C (+3° anomaly) │
│                          │  Rainfall 7d: 2mm — STAGNANT     │
│   [Folium map with       │  UV Index: 8 — HIGH              │
│    color-coded heatmap   │  Wind: 4 km/h — CALM             │
│    overlay — green to    │  Land use: 62% agricultural      │
│    red risk zones]       │                                   │
│                          │  📊 GROWTH RATE                   │
│                          │  ─────────────────────            │
│                          │  µ = 0.72/day                     │
│                          │  Doubling time: 23 hours ⚠️       │
│                          │  "Bloom is actively growing"      │
│                          │                                   │
├──────────────────────────┼───────────────────────────────────┤
│                          │                                   │
│  ⚠️ RISK SCORES           │  🔬 COMPONENT BREAKDOWN           │
│  ─────────────            │  ─────────────────────            │
│  Overall: 🔴 82/100 HIGH │                                   │
│  WHO: MODERATE-HIGH      │  [Horizontal bar chart]           │
│  Est. 320,000 cells/mL   │  Temperature:  ████████░░ 82     │
│                          │  Nutrients:    ██████░░░░ 65     │
│  🔴 Cyano Risk   82/100  │  Stagnation:   ███████░░░ 74     │
│  🟡 Organic Load 54/100  │  Light/UV:     ██████░░░░ 68     │
│  🟡 Agri Runoff  61/100  │                                   │
│  🟢 Thermal      23/100  │  Primary driver: TEMPERATURE     │
│                          │  "Water temperature 3°C above     │
│                          │   seasonal baseline"              │
│                          │                                   │
├──────────────────────────┴───────────────────────────────────┤
│                                                              │
│  📈 7-DAY FORECAST                                           │
│  ──────────────                                              │
│  [Plotly line chart]                                         │
│  - Blue line: predicted risk score trajectory                │
│  - Light blue shading: confidence band (10th-90th pctile)   │
│  - Red dashed line: WHO HIGH threshold                       │
│  - Orange dashed line: WHO MODERATE threshold                │
│                                                              │
│  30-Day Trend: ↗️ WORSENING (slope: +2.1 points/day, p<0.01)│
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  🚨 HEALTH ADVISORY                                          │
│  ─────────────────                                           │
│  ⚠️ WARNING: Cyanobacteria bloom risk is HIGH.                │
│  AVOID direct water contact. Do not allow livestock to drink.│
│  Notify local health authority.                              │
│  Risk is primarily driven by elevated water temperature      │
│  (+3°C above seasonal baseline) combined with agricultural   │
│  nutrient loading and stagnant conditions.                   │
│  Recheck in 24 hours.                                        │
│                                                              │
│  Confidence: MEDIUM (weather: live, satellite: 4hrs ago)     │
│                                                              │
│  [📥 Download PDF Report]                                    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 14. Risk & Mitigation

| Risk | Impact | Probability | Mitigation |
|---|---|---|---|
| **CyFi fails to install or run** | Lose satellite-derived bloom data | Medium | Fallback to cached known values for demo sites |
| **Open-Meteo rate limiting** | Can't fetch live weather | Low | Cache responses aggressively, 1 call per analysis |
| **ESA WorldCover files too large** | Can't deploy on Streamlit Cloud | Medium | Pre-clip GeoTIFFs to demo regions OR use fallback known values |
| **USGS API slow/down** | Can't fetch training/validation data | Low | Pre-download CSVs during development, bundle in repo |
| **Model produces unrealistic scores** | Credibility loss at demo | Medium | Extensive testing on all 3 demo sites + known events |
| **Streamlit Cloud memory limits** | App crashes on deploy | Medium | Optimize data loading, use caching (`@st.cache_data`) |
| **Judges test location with no data** | Model returns garbage | High | Graceful fallback: "Limited data for this location" message |
| **Monte Carlo too slow for UI** | Dashboard feels laggy | Medium | Pre-compute, reduce to 50 samples instead of 100 |

---

## 15. References

### Peer-Reviewed Literature

1. **Paerl, H.W. & Huisman, J.** (2008). "Blooms Like It Hot." *Science*, 320(5872), 57-58. doi:10.1126/science.1155398
2. **Downing, J.A. et al.** (2001). "Predicting Cyanobacteria Dominance in Lakes." *Canadian Journal of Fisheries and Aquatic Sciences*, 58(10), 1905-1908.
3. **Robarts, R.D. & Zohary, T.** (1987). "Temperature effects on photosynthetic capacity, respiration, and growth rates of bloom-forming cyanobacteria." *New Zealand Journal of Marine and Freshwater Research*, 21(3), 391-399.
4. **Reynolds, C.S.** (2006). *The Ecology of Phytoplankton*. Cambridge University Press.
5. **Huisman, J. et al.** (2004). "Changes in Turbulent Mixing Shift Competition for Light between Phytoplankton Species." *Ecology*, 85(11), 2960-2970.
6. **Beaulac, M.N. & Reckhow, K.H.** (1982). "An Examination of Land Use - Nutrient Export Relationships." *Journal of the American Water Resources Association*, 18(6), 1013-1024.
7. **O'Neil, J.M. et al.** (2012). "The rise of harmful cyanobacteria blooms: The potential roles of eutrophication and climate change." *Harmful Algae*, 14, 313-334.
8. **Livingstone, D.M. & Lotter, A.F.** (1998). "The relationship between air and water temperatures in lakes of the Swiss Plateau." *Boreal Environment Research*, 3, 29-39.

### Data Sources

- **USGS Water Quality Portal**: https://www.waterqualitydata.us/
- **Open-Meteo API**: https://open-meteo.com/
- **ESA WorldCover**: https://esa-worldcover.org/
- **CyFi (Cyanobacteria Finder)**: https://github.com/drivendataorg/cyfi
- **WHO Recreational Water Guidelines**: https://www.who.int/publications/i/item/9241545801
- **EPA CyAN**: https://www.epa.gov/water-research/cyanobacteria-assessment-network-cyan
- **NASA Earthdata — CyFi Blog**: https://www.earthdata.nasa.gov/news/applying-machine-learning-to-harmful-algal-blooms

### WHO Threshold Standards

- **WHO** (2003). *Guidelines for Safe Recreational Water Environments. Volume 1: Coastal and Fresh Waters*. World Health Organization, Geneva.
  - Low risk: < 20,000 cells/mL
  - Moderate risk: 20,000–100,000 cells/mL
  - High risk: 100,000–10,000,000 cells/mL
  - Very high risk: > 10,000,000 cells/mL

---

## Summary: What a Judge Sees

> *"This team built a tool that takes a latitude and longitude, pulls live weather data, computes a biologically-grounded cyanobacteria growth rate model using Monod kinetics and published temperature response curves, estimates nutrient loading from satellite-derived land use data, projects bloom risk 7 days forward with Monte Carlo uncertainty bounds, detects trends using Mann-Kendall statistical tests, validates against real USGS ground truth measurements, and displays it all on an interactive map with WHO-calibrated alert levels — using entirely free NASA and ESA data."*

---

**End of Plan**
