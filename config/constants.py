"""
AquaWatch — Constants and Scientific Thresholds

All thresholds are from published, peer-reviewed sources:
- WHO (2003) Guidelines for Safe Recreational Water Environments
- Paerl & Huisman (2008) "Blooms Like It Hot" — Science
- Beaulac & Reckhow (1982) Nutrient Export Coefficients
- Robarts & Zohary (1987) Temperature response curves
"""

# =============================================================================
# WHO Cyanobacteria Thresholds (cells/mL)
# Source: WHO Guidelines for Safe Recreational Water Environments, Vol 1 (2003)
# =============================================================================
WHO_CYANO_THRESHOLDS = {
    "low": 20_000,           # Low probability of adverse health effects
    "moderate": 100_000,     # Moderate probability
    "high": 10_000_000,      # High probability, acute danger
}

WHO_SEVERITY_LABELS = {
    "low": "Low probability of adverse health effects",
    "moderate": "Moderate probability — advisory recommended",
    "high": "High probability — avoid direct contact",
    "very_high": "Acute danger — do not use water",
}

# =============================================================================
# Temperature Thresholds for Cyanobacteria Growth
# Source: Paerl & Huisman (2008), Robarts & Zohary (1987)
# =============================================================================
BLOOM_TEMP = {
    "minimum_growth": 15.0,   # °C — cyanobacteria start growing
    "accelerated": 20.0,      # °C — growth rate increases notably
    "optimal_min": 25.0,      # °C — optimal bloom range begins
    "peak": 28.0,             # °C — maximum growth for Microcystis
    "optimal_max": 35.0,      # °C — upper end of optimal range
    "stress": 40.0,           # °C — growth inhibited
}

# Gaussian response curve parameters (Robarts & Zohary 1987)
TEMP_RESPONSE = {
    "T_optimal": 28.0,       # °C — peak growth temperature
    "sigma": 5.0,            # °C — spread of temperature tolerance
    "mu_max": 1.0,           # per day — maximum specific growth rate
}

# =============================================================================
# Rainfall & Stagnation Thresholds
# =============================================================================
RAINFALL = {
    "significant_mm": 5.0,       # mm — counts as a rain event
    "heavy_mm": 20.0,            # mm — triggers runoff flush
    "stagnation_days": 7,        # days without rain = stagnation risk
    "first_flush_dry_days": 3,   # dry days before rain = first flush
    "first_flush_rain_mm": 10.0, # mm rain after dry period = flush event
}

# =============================================================================
# Nutrient Export Coefficients by Land Use
# Source: Beaulac & Reckhow (1982)
# =============================================================================
LAND_USE_NUTRIENT_EXPORT = {
    "cropland": 0.80,       # High fertilizer/manure runoff
    "urban": 0.50,           # Sewage + lawn fertilizer
    "grassland": 0.20,       # Moderate
    "forest": 0.10,          # Low nutrient export
    "wetland": 0.05,         # Wetlands absorb nutrients
    "water": 0.0,
    "bare": 0.05,
}

# =============================================================================
# Model Component Weights
# Geometric mean combination for final risk score
# =============================================================================
RISK_WEIGHTS = {
    "temperature": 0.35,     # Strongest driver (Paerl & Huisman 2008)
    "nutrients": 0.25,       # Essential fuel
    "stagnation": 0.22,      # Accumulation mechanism
    "light": 0.18,           # Photosynthesis driver
}

# =============================================================================
# Risk Level Classification
# =============================================================================
RISK_LEVELS = {
    "SAFE":     {"min": 0,  "max": 25,  "color": "#2ecc71", "emoji": "🟢"},
    "LOW":      {"min": 25, "max": 50,  "color": "#f1c40f", "emoji": "🟡"},
    "WARNING":  {"min": 50, "max": 75,  "color": "#e67e22", "emoji": "🟠"},
    "CRITICAL": {"min": 75, "max": 100, "color": "#e74c3c", "emoji": "🔴"},
}

# =============================================================================
# API Endpoints
# =============================================================================
OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_HISTORICAL = "https://archive-api.open-meteo.com/v1/archive"

# =============================================================================
# Monod Kinetics Parameters
# Source: Reynolds (2006) The Ecology of Phytoplankton
# =============================================================================
MONOD = {
    "K_N": 50.0,             # Half-saturation constant for nutrients (normalized)
    "min_stagnation": 0.3,   # Minimum stagnation factor (blooms can grow in flowing water)
}

# =============================================================================
# CyFi Severity to Score Mapping
# =============================================================================
CYFI_SEVERITY_SCORES = {
    "low": 15,
    "moderate": 45,
    "high": 75,
    "very_high": 95,
}

# Score to estimated cells/mL mapping (log-linear)
# Calibrated: score=30 → 20,000 cells/mL, score=85 → 10,000,000 cells/mL
CELLS_MAPPING = {
    "slope": 0.049,          # (7.0 - 4.3) / (85 - 30)
    "intercept": 2.83,       # 4.3 - 0.049 * 30
}
