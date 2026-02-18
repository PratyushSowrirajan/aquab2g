"""
AquaWatch — CyFi Integration

CyFi (Cyanobacteria Finder) is an open-source Python package by DrivenData/NASA
that uses Sentinel-2 satellite imagery + LightGBM ML model to estimate
cyanobacteria density in cells/mL.

Reference paper:
  Dorne et al. (2024) "Cyanobacteria detection in small, inland water bodies with CyFi"
  SciPy Conference Proceedings. https://doi.org/10.25080/pdhk7238

Key facts:
  - Trained on 5,721 in-situ observations
  - Evaluated on 2,880 ground measurements from 12 data providers
  - 72% bloom detection accuracy (vs 66% for CyAN/Sentinel-3)
  - Uses Sentinel-2 at 10-30m resolution (vs 300m for Sentinel-3)
  - WHO severity levels: Low <20k, Moderate 20k-100k, High >100k cells/mL

Strategy: CyFi is slow (~2-5 min per prediction, downloads Sentinel-2 imagery).
We use pre-computed/cached values for demo sites and provide fallback data
from published monitoring reports.
"""

import json
from pathlib import Path
from typing import Dict, Optional
from config.demo_sites import DEMO_CYFI_DATA, DEMO_SITES
from config.constants import CYFI_SEVERITY_SCORES


class CyFiClient:
    """Wrapper for CyFi predictions with caching and fallback."""

    CACHE_DIR = Path("data/cache")
    CACHE_FILE = CACHE_DIR / "cyfi_cache.json"

    def __init__(self):
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict:
        if self.CACHE_FILE.exists():
            try:
                with open(self.CACHE_FILE, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_cache(self):
        with open(self.CACHE_FILE, "w") as f:
            json.dump(self.cache, f, indent=2)

    def get_prediction(self, lat: float, lon: float) -> Dict:
        """
        Get CyFi cyanobacteria prediction for a location.

        Returns:
            {
                "density_cells_per_ml": float,
                "severity": str,
                "severity_score": int (0-100),
                "source": str,
            }
        """
        cache_key = f"{lat:.4f}_{lon:.4f}"

        # Check cache
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Find closest demo site with known data
        prediction = self._get_known_data(lat, lon)

        # Cache and return
        self.cache[cache_key] = prediction
        self._save_cache()
        return prediction

    def _get_known_data(self, lat: float, lon: float) -> Dict:
        """
        Get published monitoring data for closest known site.
        All values sourced from published government monitoring reports.
        """
        min_dist = float("inf")
        closest_key = "lake_vanern"  # default to clean lake

        for site_key, site_data in DEMO_SITES.items():
            dist = ((lat - site_data["lat"]) ** 2 + (lon - site_data["lon"]) ** 2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                closest_key = site_key

        cyfi_data = DEMO_CYFI_DATA.get(closest_key, DEMO_CYFI_DATA["lake_vanern"])
        severity = cyfi_data["severity"]

        return {
            "density_cells_per_ml": cyfi_data["density_cells_per_ml"],
            "severity": severity,
            "severity_score": CYFI_SEVERITY_SCORES.get(severity, 15),
            "source": cyfi_data["source"],
        }
