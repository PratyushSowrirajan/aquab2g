"""
AquaWatch — Mann-Kendall 30-Day Trend Analysis

Uses the pymannkendall library to test whether risk scores over the
past 30 days show a statistically significant monotonic trend.

Returns: WORSENING / STABLE / IMPROVING with slope (points/day) and p-value.

Reference: Mann (1945), Kendall (1975), Sen (1968).
"""

from typing import Dict, List
import numpy as np

try:
    import pymannkendall as mk
    _MK_AVAILABLE = True
except ImportError:
    _MK_AVAILABLE = False


def compute_trend(risk_scores_30d: List[float]) -> Dict:
    """
    Run Mann-Kendall trend test on a historical series of risk scores.

    Parameters
    ----------
    risk_scores_30d : list of float
        Daily risk scores, oldest first. Must have ≥ 4 values.

    Returns
    -------
    dict with keys: trend, slope_per_day, p_value, significant,
                    direction_emoji, description
    """
    if not risk_scores_30d or len(risk_scores_30d) < 4:
        return _no_data_result()

    scores = np.array(risk_scores_30d, dtype=float)
    scores = scores[~np.isnan(scores)]

    if len(scores) < 4:
        return _no_data_result()

    # Sen's slope (robust linear trend estimator)
    n = len(scores)
    slopes = []
    for i in range(n - 1):
        for j in range(i + 1, n):
            slopes.append((scores[j] - scores[i]) / (j - i))
    sen_slope = float(np.median(slopes)) if slopes else 0.0

    # Mann-Kendall test
    p_value = 1.0
    mk_trend = "no trend"
    if _MK_AVAILABLE:
        try:
            result = mk.original_test(scores)
            p_value = float(result.p)
            mk_trend = result.trend
        except Exception:
            pass
    else:
        # Fallback: simple linear regression significance
        from scipy import stats
        _, _, _, p_value, _ = stats.linregress(range(len(scores)), scores)

    significant = p_value < 0.05

    # Classify direction
    if significant:
        if sen_slope > 0.5:
            trend = "WORSENING"
            emoji = "↗️"
        elif sen_slope < -0.5:
            trend = "IMPROVING"
            emoji = "↘️"
        else:
            trend = "STABLE"
            emoji = "→"
    else:
        trend = "STABLE"
        emoji = "→"

    description = _build_description(trend, sen_slope, p_value, significant)

    return {
        "trend": trend,
        "slope_per_day": round(sen_slope, 3),
        "p_value": round(p_value, 4),
        "significant": significant,
        "direction_emoji": emoji,
        "description": description,
        "n_days": int(n),
    }


def _no_data_result() -> Dict:
    return {
        "trend": "STABLE",
        "slope_per_day": 0.0,
        "p_value": 1.0,
        "significant": False,
        "direction_emoji": "→",
        "description": "Insufficient historical data for trend analysis.",
        "n_days": 0,
    }


def _build_description(trend: str, slope: float, p_value: float, significant: bool) -> str:
    if not significant:
        return f"No statistically significant trend (p={p_value:.2f}). Conditions appear stable."
    abs_slope = abs(slope)
    strength = "strongly" if abs_slope > 2 else "gradually"
    if trend == "WORSENING":
        return (
            f"Risk is {strength} worsening at +{abs_slope:.1f} points/day "
            f"(Mann-Kendall p={p_value:.3f}). Bloom conditions are developing."
        )
    elif trend == "IMPROVING":
        return (
            f"Risk is {strength} improving at -{abs_slope:.1f} points/day "
            f"(Mann-Kendall p={p_value:.3f}). Conditions are recovering."
        )
    return f"No meaningful trend detected (slope={slope:.2f}, p={p_value:.2f})."
