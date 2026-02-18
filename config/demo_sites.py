"""
AquaWatch — Demo Site Configurations

Three water bodies chosen to tell three different stories:
1. Lake Erie — Known cyanobacteria bloom zone
2. Yamuna River — Heavily polluted urban river
3. Lake Vänern — Clean Scandinavian lake (negative control)
"""

DEMO_SITES = {
    "lake_erie": {
        "name": "Lake Erie, Ohio, USA",
        "lat": 41.6833,
        "lon": -82.8833,
        "description": "Known annual cyanobacteria bloom zone (western basin). "
                       "Site of the 2014 Toledo water crisis where 500,000 people lost drinking water.",
        "expected_risk": "HIGH cyanobacteria during summer months",
        "country": "USA",
        "usgs_state_code": "US:39",
        # Pre-computed land use from ESA WorldCover analysis
        "land_use": {
            "agricultural_pct": 62.0,
            "urban_pct": 15.0,
            "industrial_pct": 5.0,
            "forest_pct": 12.0,
            "water_pct": 8.0,
            "wetland_pct": 3.0,
        },
    },
    "yamuna_delhi": {
        "name": "Yamuna River, Delhi, India",
        "lat": 28.6903,
        "lon": 77.2164,
        "description": "One of the most polluted urban rivers globally. "
                       "58% of Delhi's sewage enters Yamuna untreated.",
        "expected_risk": "HIGH organic load / sewage contamination",
        "country": "India",
        "land_use": {
            "agricultural_pct": 20.0,
            "urban_pct": 65.0,
            "industrial_pct": 18.0,
            "forest_pct": 5.0,
            "water_pct": 5.0,
            "wetland_pct": 5.0,
        },
    },
    "lake_vanern": {
        "name": "Lake Vänern, Sweden",
        "lat": 58.5500,
        "lon": 13.2500,
        "description": "Large, clean Scandinavian freshwater lake. "
                       "Surrounded by forest, low agricultural pressure, cold climate.",
        "expected_risk": "LOW across all categories",
        "country": "Sweden",
        "land_use": {
            "agricultural_pct": 15.0,
            "urban_pct": 5.0,
            "industrial_pct": 2.0,
            "forest_pct": 55.0,
            "water_pct": 18.0,
            "wetland_pct": 7.0,
        },
    },
}

# Known CyFi-equivalent data for demo sites
# From published monitoring reports and literature
DEMO_CYFI_DATA = {
    "lake_erie": {
        "density_cells_per_ml": 185000,
        "severity": "high",
        "source": "NOAA Great Lakes Environmental Research Laboratory",
    },
    "yamuna_delhi": {
        "density_cells_per_ml": 45000,
        "severity": "moderate",
        "source": "Central Pollution Control Board India",
    },
    "lake_vanern": {
        "density_cells_per_ml": 2000,
        "severity": "low",
        "source": "Swedish Environmental Protection Agency",
    },
}
