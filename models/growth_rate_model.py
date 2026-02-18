"""
AquaWatch — Model 5: Biological Growth Rate (Monod Kinetics)

Implements:
  µ = µ_max × f(T) × f(N) × f(L) × f(S)

Where each f() is a limitation factor (0-1).

Computes:
  - Specific growth rate µ (per day)
  - Doubling time (hours)
  - 7-day forward biomass projection (relative units)

Sources:
  Reynolds (2006) The Ecology of Phytoplankton, Cambridge Univ. Press.
  Robarts & Zohary (1987) — Gaussian temperature response for Microcystis.
  Monod (1949) — half-saturation kinetics for nutrient limitation.
"""

import numpy as np
from typing import Dict, List
from config.constants import TEMP_RESPONSE, MONOD


def compute_growth_rate(
    temp_score: float,
    nutrient_score: float,
    light_score: float,
    stagnation_score: float,
    water_temp: float,
) -> Dict:
    """
    Compute cyanobacteria specific growth rate using Monod kinetics.

    Parameters
    ----------
    temp_score, nutrient_score, light_score, stagnation_score : float
        0–100 component scores from models 1–4.
    water_temp : float
        Estimated surface water temperature in °C.

    Returns
    -------
    dict with keys: mu_per_day, doubling_time_hours, biomass_trajectory,
                    f_temperature, f_nutrients, f_light, f_stagnation,
                    limiting_factor, factors
    """
    T_opt   = TEMP_RESPONSE["T_optimal"]
    sigma   = TEMP_RESPONSE["sigma"]
    mu_max  = TEMP_RESPONSE["mu_max"]
    K_N     = MONOD["K_N"]
    min_stag = MONOD["min_stagnation"]

    # ---------------------------------------------------------------
    # f(T) — Gaussian temperature response (Robarts & Zohary 1987)
    # Calibrated for Microcystis aeruginosa: optimal 28°C, σ=5°C
    # ---------------------------------------------------------------
    f_T = float(np.exp(-((water_temp - T_opt) ** 2) / (2 * sigma ** 2)))
    f_T = float(np.clip(f_T, 0.0, 1.0))

    # ---------------------------------------------------------------
    # f(N) — Monod nutrient limitation
    # ---------------------------------------------------------------
    N = nutrient_score  # 0-100 normalized scale
    f_N = N / (N + K_N)
    f_N = float(np.clip(f_N, 0.0, 1.0))

    # ---------------------------------------------------------------
    # f(L) — Light limitation (normalized)
    # ---------------------------------------------------------------
    f_L = float(np.clip(light_score / 100.0, 0.0, 1.0))

    # ---------------------------------------------------------------
    # f(S) — Stagnation factor
    # High stagnation = cyanobacteria can accumulate at surface (positive)
    # Minimum value prevents zero even in turbulent conditions
    # ---------------------------------------------------------------
    f_S = float(np.clip(
        min_stag + (stagnation_score / 100.0) * (1.0 - min_stag),
        min_stag, 1.0
    ))

    # ---------------------------------------------------------------
    # Net specific growth rate
    # ---------------------------------------------------------------
    mu = mu_max * f_T * f_N * f_L * f_S
    mu = round(float(np.clip(mu, 0.0, mu_max)), 4)

    # ---------------------------------------------------------------
    # Doubling time
    # ---------------------------------------------------------------
    if mu > 0.001:
        doubling_time_hours = round((np.log(2.0) / mu) * 24.0, 1)
    else:
        doubling_time_hours = None  # effectively no growth

    # ---------------------------------------------------------------
    # 7-day forward biomass projection (relative — starts at 1.0)
    # Discrete daily: B(t+1) = B(t) × e^µ
    # ---------------------------------------------------------------
    biomass_trajectory: List[float] = []
    B = 1.0
    for _ in range(8):  # day 0 … day 7
        biomass_trajectory.append(round(B, 4))
        B = B * np.exp(mu)

    # ---------------------------------------------------------------
    # Identify limiting factor
    # ---------------------------------------------------------------
    factors_map = {
        "Temperature": f_T,
        "Nutrients": f_N,
        "Light": f_L,
        "Stagnation": f_S,
    }
    limiting_factor = min(factors_map, key=factors_map.get)

    factors = []
    if f_T < 0.3:
        factors.append(f"Temperature limiting — f(T)={f_T:.2f} (water {water_temp}°C far from 28°C optimum)")
    if f_N < 0.3:
        factors.append(f"Nutrients limiting — f(N)={f_N:.2f} (low nutrient loading)")
    if f_L < 0.3:
        factors.append(f"Light limiting — f(L)={f_L:.2f} (low UV/cloud/short days)")
    if mu > 0.5:
        factors.append(f"Rapid growth: µ={mu:.2f}/day — doubling every {doubling_time_hours:.0f}h")
    elif mu > 0.3:
        factors.append(f"Moderate growth: µ={mu:.2f}/day")

    return {
        "mu_per_day": mu,
        "doubling_time_hours": doubling_time_hours,
        "biomass_trajectory": biomass_trajectory,
        "f_temperature": round(f_T, 3),
        "f_nutrients": round(f_N, 3),
        "f_light": round(f_L, 3),
        "f_stagnation": round(f_S, 3),
        "limiting_factor": limiting_factor,
        "factors": factors,
    }
