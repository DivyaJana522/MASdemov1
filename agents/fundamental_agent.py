from __future__ import annotations

from typing import Any, Dict, List, Tuple

import math

from .base_agent import BaseAgent
from ..utils.logging_utils import get_logger
from ..utils.normalization import clip_signal


def _score_pe(pe: float) -> float:
    if pe is None or not math.isfinite(pe):
        return 0.0
    if pe <= 10:
        return 1.0
    if pe >= 40:
        return -1.0
    if pe <= 20:
        return 1.0 - (pe - 10) / 10.0  # 10->1, 20->0
    if pe <= 30:
        return -0.25 * (pe - 20)  # 20->0, 30->-2.5 -> cap later
    return -0.5 - 0.5 * (pe - 30) / 10.0  # 30->-0.5, 40->-1


def _score_pb(pb: float) -> float:
    if pb is None or not math.isfinite(pb):
        return 0.0
    if pb <= 1.0:
        return 0.6  # cheap but might be value trap
    if pb >= 6.0:
        return -1.0
    if pb <= 3.0:
        return 0.6 - 0.6 * (pb - 1.0) / 2.0  # 1->0.6, 3->0
    return -0.1 - 0.9 * (pb - 3.0) / 3.0  # 3->-0.1, 6->-1


def _score_roe(roe: float) -> float:
    if roe is None or not math.isfinite(roe):
        return 0.0
    roe *= 100 if roe < 1 and roe > -1 else 1  # handle if in fraction
    if roe <= 0:
        return -1.0
    if roe >= 20:
        return 1.0
    return -1.0 + (roe / 20.0) * 2.0  # 0->-1, 20->+1


def _score_de(de: float) -> float:
    if de is None or not math.isfinite(de):
        return 0.0
    if de <= 0.2:
        return 1.0
    if de >= 2.0:
        return -1.0
    return 1.0 - (de - 0.2) / (2.0 - 0.2) * 2.0  # 0.2->1, 2->-1


def _score_fcf_yield(y: float) -> float:
    if y is None or not math.isfinite(y):
        return 0.0
    y *= 100 if abs(y) < 1 else 1  # expect percent sometimes in fraction
    if y <= -2:
        return -1.0
    if y >= 8:
        return 1.0
    return -1.0 + (y + 2) / 10.0 * 2.0  # -2->-1, 8->+1


def _score_growth(g: float, neg_full: float, pos_full: float) -> float:
    if g is None or not math.isfinite(g):
        return 0.0
    g *= 100 if abs(g) < 1 else 1
    if g <= neg_full:
        return -1.0
    if g >= pos_full:
        return 1.0
    return -1.0 + (g - neg_full) / (pos_full - neg_full) * 2.0


def _score_margin(m: float) -> float:
    if m is None or not math.isfinite(m):
        return 0.0
    m *= 100 if abs(m) < 1 else 1
    if m <= 0:
        return -1.0
    if m >= 30:
        return 1.0
    return -1.0 + (m / 30.0) * 2.0


class FundamentalAgent(BaseAgent):
    def __init__(self) -> None:
        self.logger = get_logger(__name__)

    def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze with input validation and error handling."""
        if not market_data:
            return self._neutral_response("Empty market data")
        
        fundamentals = market_data.get("fundamentals") or {}
        if not fundamentals:
            return self._neutral_response("No fundamentals available")
        
        try:
            return self._compute_fundamental_signals(fundamentals)
        except Exception as e:
            self.logger.error("Fundamental analysis failed: %s", e)
            return self._neutral_response(f"Analysis error: {str(e)}")
    
    def _neutral_response(self, reason: str) -> Dict[str, Any]:
        """Return neutral signal with reason."""
        return {
            "signal": 0.0,
            "confidence": 0.0,
            "label": "Neutral",
            "rationale": reason,
        }
    
    def _compute_fundamental_signals(self, fundamentals: Dict[str, Any]) -> Dict[str, Any]:

        pe = fundamentals.get("pe")
        pb = fundamentals.get("pb")
        roe = fundamentals.get("roe")
        de = fundamentals.get("debt_to_equity")
        fcf_yield = fundamentals.get("fcf_yield")
        revenue_yoy = fundamentals.get("revenue_yoy")
        earnings_yoy = fundamentals.get("earnings_yoy")
        ebitda_margin = fundamentals.get("ebitda_margin")

        parts = {
            "P/E": clip_signal(_score_pe(pe)),
            "P/B": clip_signal(_score_pb(pb)),
            "ROE": clip_signal(_score_roe(roe)),
            "D/E": clip_signal(_score_de(de)),
            "FCF Yield": clip_signal(_score_fcf_yield(fcf_yield)),
            "Revenue YoY": clip_signal(_score_growth(revenue_yoy, neg_full=-20, pos_full=20)),
            "Earnings YoY": clip_signal(_score_growth(earnings_yoy, neg_full=-30, pos_full=20)),
            "EBITDA Margin": clip_signal(_score_margin(ebitda_margin)),
        }

        available = [v for v in parts.values() if v is not None]
        if not available:
            return {
                "signal": 0.0,
                "confidence": 0.0,
                "label": "Neutral",
                "rationale": "No usable fundamental fields; returning neutral.",
            }

        signal = float(sum(available) / len(available))

        # Confidence: coverage and consistency (lower dispersion => higher confidence)
        coverage = len(available) / len(parts)
        mean = signal
        variance = sum((v - mean) ** 2 for v in available) / max(1, len(available))
        dispersion = min(1.0, variance)  # cap
        confidence = 0.3 + 0.5 * coverage + 0.2 * (1 - dispersion)
        confidence = float(max(0.0, min(1.0, confidence)))

        label = "Attractive" if signal > 0.15 else ("Weak" if signal < -0.15 else "Neutral")

        # Rationale: top drivers
        sorted_parts: List[Tuple[str, float]] = sorted(parts.items(), key=lambda kv: kv[1])
        worst = ", ".join(f"{k} {v:+.2f}" for k, v in sorted_parts[:2])
        best = ", ".join(f"{k} {v:+.2f}" for k, v in sorted_parts[-2:])
        rationale = f"Drivers -> {best}; Headwinds -> {worst}. Coverage={coverage:.0%}."

        return {
            "signal": signal,
            "confidence": confidence,
            "label": label,
            "rationale": rationale,
        }
