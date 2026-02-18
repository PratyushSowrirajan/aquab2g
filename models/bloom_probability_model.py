"""
AquaWatch — Model 6: Bloom Probability (Final Risk Score)

Combines Models 1–5 via weighted geometric mean, maps to WHO severity,
estimates cells/mL, and produces the final plain-English advisory.

Geometric mean ensures that any single factor near zero collapses
the overall score — accurately reflecting biological reality.

Sources:
  WHO (2003) Guidelines for Safe Recreational Water Environments
  Paerl & Huisman (2008)
"""

import numpy as np
from typing import Dict, Optional
from config.constants import (
    WHO_CYANO_THRESHOLDS,
    WHO_SEVERITY_LABELS,
    RISK_LEVELS,
    RISK_WEIGHTS,
    CELLS_MAPPING,
    CYFI_SEVERITY_SCORES,
)


def compute_bloom_probability(
    temp_score: float,
    nutrient_score: float,
    stagnation_score: float,
    light_score: float,
    growth_rate: Dict,
    cyfi_data: Optional[Dict] = None,
    data_confidence: str = "MEDIUM",
) -> Dict:
    """
    Compute final bloom probability risk score (0–100).

    Parameters
    ----------
    temp_score, nutrient_score, stagnation_score, light_score : float
        0–100 scores from Models 1–4.
    growth_rate : dict
        Output of ``compute_growth_rate()`` (Model 5).
    cyfi_data : dict, optional
        CyFi satellite prediction. Used as a soft calibration anchor.
    data_confidence : str
        'HIGH' | 'MEDIUM' | 'LOW' — affects confidence interval width.

    Returns
    -------
    dict with keys: risk_score, who_severity, who_label,
                    estimated_cells_per_ml, risk_level, advisory,
                    confidence, component_scores, factors
    """
    # ---------------------------------------------------------------
    # 1. Weighted geometric mean of component scores
    # ---------------------------------------------------------------
    w = RISK_WEIGHTS
    scores = np.array([temp_score, nutrient_score, stagnation_score, light_score])
    weights = np.array([w["temperature"], w["nutrients"], w["stagnation"], w["light"]])

    # Protect against zero in log (floor at 1)
    scores_safe = np.maximum(scores, 1.0)
    log_weighted = np.sum(weights * np.log(scores_safe)) / np.sum(weights)
    geometric_mean = float(np.exp(log_weighted))
    geometric_mean = float(np.clip(geometric_mean, 0, 100))

    # ---------------------------------------------------------------
    # 2. Growth rate modifier
    # µ_max = 1.0/day → use µ to nudge score ±10 points
    # ---------------------------------------------------------------
    mu = growth_rate.get("mu_per_day", 0.0)
    growth_modifier = (mu - 0.35) * 20.0  # neutral at µ=0.35
    growth_modifier = float(np.clip(growth_modifier, -10.0, 15.0))

    # ---------------------------------------------------------------
    # 3. CyFi soft anchor (satellite validation)
    # If CyFi data is available and trusted, blend it at 20% weight
    # ---------------------------------------------------------------
    cyfi_blend = 0.0
    if cyfi_data and cyfi_data.get("source", "unavailable") != "unavailable":
        cyfi_score = float(cyfi_data.get("severity_score", 0))
        cyfi_blend = (cyfi_score - geometric_mean) * 0.20

    # ---------------------------------------------------------------
    # 4. Final risk score
    # ---------------------------------------------------------------
    risk_score = geometric_mean + growth_modifier + cyfi_blend
    risk_score = float(np.clip(risk_score, 0.0, 100.0))

    # ---------------------------------------------------------------
    # 5. WHO severity mapping
    # ---------------------------------------------------------------
    estimated_cells = _score_to_cells(risk_score)
    who_severity = _cells_to_who_severity(estimated_cells)
    who_label = WHO_SEVERITY_LABELS.get(who_severity, "Unknown")

    # ---------------------------------------------------------------
    # 6. Risk level for UI
    # ---------------------------------------------------------------
    risk_level = _score_to_risk_level(risk_score)

    # ---------------------------------------------------------------
    # 7. Confidence
    # ---------------------------------------------------------------
    confidence_map = {"HIGH": "HIGH", "MEDIUM": "MEDIUM", "LOW": "LOW"}
    confidence = confidence_map.get(data_confidence, "MEDIUM")

    # ---------------------------------------------------------------
    # 8. Primary driver
    # ---------------------------------------------------------------
    component_scores = {
        "Temperature": round(temp_score, 1),
        "Nutrients": round(nutrient_score, 1),
        "Stagnation": round(stagnation_score, 1),
        "Light": round(light_score, 1),
    }
    primary_driver = max(component_scores, key=component_scores.get)
    limiting_driver = min(component_scores, key=component_scores.get)

    # ---------------------------------------------------------------
    # 9. Plain-English advisory
    # ---------------------------------------------------------------
    advisory = _build_advisory(risk_level, who_severity, primary_driver,
                                limiting_driver, estimated_cells, confidence)

    return {
        "risk_score": round(risk_score, 1),
        "who_severity": who_severity,
        "who_label": who_label,
        "estimated_cells_per_ml": int(estimated_cells),
        "risk_level": risk_level,
        "risk_color": RISK_LEVELS[risk_level]["color"],
        "risk_emoji": RISK_LEVELS[risk_level]["emoji"],
        "advisory": advisory,
        "confidence": confidence,
        "component_scores": component_scores,
        "primary_driver": primary_driver,
        "limiting_driver": limiting_driver,
        "geometric_mean": round(geometric_mean, 1),
        "growth_modifier": round(growth_modifier, 2),
        "mu_per_day": mu,
    }


def _score_to_cells(score: float) -> float:
    """
    Log-linear mapping from risk score to estimated cells/mL.
    Calibrated: score=30 → ~20,000 cells/mL (WHO moderate threshold)
                score=85 → ~10,000,000 cells/mL (WHO very high threshold)
    """
    slope = CELLS_MAPPING["slope"]
    intercept = CELLS_MAPPING["intercept"]
    log_cells = slope * score + intercept
    return float(10 ** log_cells)


def _cells_to_who_severity(cells: float) -> str:
    """Map cells/mL to WHO recreational water severity category."""
    if cells >= WHO_CYANO_THRESHOLDS["high"]:
        return "very_high"
    elif cells >= WHO_CYANO_THRESHOLDS["moderate"]:
        return "high"
    elif cells >= WHO_CYANO_THRESHOLDS["low"]:
        return "moderate"
    else:
        return "low"


def _score_to_risk_level(score: float) -> str:
    for level, bounds in RISK_LEVELS.items():
        if bounds["min"] <= score < bounds["max"]:
            return level
    return "CRITICAL"  # score == 100


def _build_advisory(
    risk_level: str,
    who_severity: str,
    primary_driver: str,
    limiting_driver: str,
    cells: float,
    confidence: str,
) -> str:
    """Compose a plain-English health advisory string."""
    action_map = {
        "SAFE":     "The water body shows low cyanobacteria bloom risk. "
                    "Normal recreational use is considered safe under current conditions. "
                    "Continue routine monitoring.",
        "LOW":      "Low-to-moderate bloom risk detected. "
                    "Recreational use is generally safe but advisable to monitor over coming days. "
                    "Avoid swallowing water. Watch for surface scum or discolouration.",
        "WARNING":  "Elevated cyanobacteria bloom risk. "
                    "Avoid direct water contact, especially for children and pets. "
                    "Do not use for drinking without treatment. "
                    "Notify local environmental health authority.",
        "CRITICAL": "CRITICAL bloom risk. Acute danger. "
                    "DO NOT use this water for drinking, bathing, or livestock. "
                    "Immediately notify local health authority and post warning signs. "
                    "Seek alternative water sources.",
    }

    driver_text = {
        "Temperature": "abnormally warm water temperature",
        "Nutrients":   "high nutrient loading from agricultural or urban runoff",
        "Stagnation":  "stagnant water and low mixing conditions",
        "Light":       "high light availability and UV exposure",
    }

    base = action_map.get(risk_level, "Risk assessment unavailable.")
    driver_note = f"Primary driver: {driver_text.get(primary_driver, primary_driver)}."
    confidence_note = f"Confidence: {confidence} ({cells:,.0f} est. cells/mL)."

    return f"{base} {driver_note} {confidence_note}"
