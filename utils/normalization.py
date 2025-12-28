from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


def clip_signal(x: float, low: float = -1.0, high: float = 1.0) -> float:
    return float(max(low, min(high, x)))


def to_unit_interval(x: float, xmin: float, xmax: float) -> float:
    if xmin == xmax:
        return 0.5
    v = (x - xmin) / (xmax - xmin)
    return float(max(0.0, min(1.0, v)))


def to_negpos_one(x: float, center: float, low: float, high: float) -> float:
    if high == center and x >= center:
        return 1.0
    if center == low and x < center:
        return -1.0
    if x >= center:
        denom = (high - center) if high != center else 1.0
        return clip_signal((x - center) / denom)
    else:
        denom = (center - low) if center != low else 1.0
        return -clip_signal((center - x) / denom)


def safe_ratio(numerator: Optional[float], denominator: Optional[float], default: Optional[float] = None) -> Optional[float]:
    if numerator is None or denominator in (None, 0):
        return default
    try:
        return float(numerator) / float(denominator)
    except Exception:
        return default


def zscore_cap(series: pd.Series, cap: float = 3.0) -> pd.Series:
    if series is None or len(series) == 0:
        return series
    std = series.std(ddof=0)
    if std == 0 or pd.isna(std):
        return pd.Series(np.zeros(len(series)), index=series.index)
    s = (series - series.mean()) / std
    return s.clip(lower=-cap, upper=cap)


def rescale_by_thresholds(x: float, neg_full: float, neg_zero: float, pos_zero: float, pos_full: float) -> float:
    """Piecewise linear rescale to [-1, 1] with four thresholds.

    Regions: (-inf, neg_full] -> -1; [neg_full, neg_zero] -> (-1,0);
             [neg_zero, pos_zero] -> 0; [pos_zero, pos_full] -> (0,1);
             [pos_full, +inf) -> 1
    Assumes neg_full < neg_zero <= pos_zero < pos_full.
    """
    if x <= neg_full:
        return -1.0
    if x < neg_zero:
        return -1.0 + (x - neg_full) / (neg_zero - neg_full)
    if x <= pos_zero:
        return 0.0
    if x < pos_full:
        return (x - pos_zero) / (pos_full - pos_zero)
    return 1.0
