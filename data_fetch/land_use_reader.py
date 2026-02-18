"""
AquaWatch — Land Use Reader

Uses pre-computed land-use percentages for demo sites.
In production, would read ESA WorldCover GeoTIFF files.

Land-use classes (ESA WorldCover 10m):
  10 = Tree cover      | 20 = Shrubland    | 30 = Grassland
  40 = Cropland (AG)   | 50 = Built-up     | 60 = Bare
  80 = Water           | 90 = Wetland       | 95 = Mangroves
"""

from typing import Dict
from config.demo_sites import DEMO_SITES


class LandUseReader:
    """Provides land-use classification percentages for locations."""

    def get_land_use(self, lat: float, lon: float) -> Dict[str, float]:
        """
        Get land-use percentages within ~5km radius of a point.
        Currently uses pre-computed values for demo sites.
        Falls back to closest known site for arbitrary coordinates.
        """
        # Find the closest demo site
        min_dist = float("inf")
        closest = self._default()

        for site_key, site_data in DEMO_SITES.items():
            dist = ((lat - site_data["lat"]) ** 2 + (lon - site_data["lon"]) ** 2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                closest = site_data.get("land_use", self._default())

        return closest

    @staticmethod
    def _default() -> Dict[str, float]:
        return {
            "agricultural_pct": 25.0,
            "urban_pct": 15.0,
            "industrial_pct": 5.0,
            "forest_pct": 35.0,
            "water_pct": 10.0,
            "wetland_pct": 5.0,
        }
