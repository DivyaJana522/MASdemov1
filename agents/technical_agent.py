from __future__ import annotations

from typing import Any, Dict, Optional
from io import StringIO

import numpy as np
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator
from ta.volatility import BollingerBands

from .base_agent import BaseAgent
from ..utils.logging_utils import get_logger
from ..utils.normalization import clip_signal


class TechnicalAgent(BaseAgent):
    def __init__(self) -> None:
        self.logger = get_logger(__name__)

    def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze with robust error handling and validation."""
        if not market_data:
            return self._neutral_response("Empty market data")
        
        price_block = market_data.get("price_data") or {}
        prices_payload = price_block.get("prices")
        
        if not prices_payload:
            return self._neutral_response("No price data available")

        try:
            df = pd.read_json(StringIO(prices_payload["data"]), orient="split")
        except Exception as e:
            self.logger.error("Failed to parse price data: %s", e)
            return self._neutral_response("Failed to parse price data payload")

        if df is None or df.empty:
            return self._neutral_response("Empty price series")
        
        if len(df) < 20:
            return self._neutral_response(f"Insufficient data points ({len(df)} < 20)")
        
        try:
            return self._compute_technical_signals(df)
        except Exception as e:
            self.logger.error("Technical analysis failed: %s", e)
            return self._neutral_response(f"Analysis error: {str(e)}")
    
    def _neutral_response(self, reason: str) -> Dict[str, Any]:
        """Return neutral signal with reason."""
        return {
            "signal": 0.0,
            "confidence": 0.0,
            "label": "Neutral",
            "rationale": reason,
        }
    
    def _compute_technical_signals(self, df: pd.DataFrame) -> Dict[str, Any]:

        """Compute technical indicators and aggregate signals."""
        df = df.copy()
        close = df["Close"].astype(float)
        high = df["High"].astype(float)
        low = df["Low"].astype(float)
        volume = df["Volume"].astype(float)

        # Indicators with safety checks
        try:
            rsi = RSIIndicator(close, window=14).rsi().iloc[-1]
            if not np.isfinite(rsi):
                rsi = 50.0  # Neutral default
        except Exception:
            rsi = 50.0
        
        try:
            macd_obj = MACD(close, window_slow=26, window_fast=12, window_sign=9)
            macd_hist = macd_obj.macd_diff()
            macd_hist_z = (macd_hist - macd_hist.rolling(50).mean()) / (macd_hist.rolling(50).std(ddof=0) + 1e-9)
            macd_val = macd_hist_z.iloc[-1]
            macd_score = float(np.tanh(macd_val / 2.0)) if np.isfinite(macd_val) else 0.0
        except Exception:
            macd_score = 0.0

        try:
            bb = BollingerBands(close, window=20, window_dev=2)
            bb_high = bb.bollinger_hband().iloc[-1]
            bb_low = bb.bollinger_lband().iloc[-1]
            if np.isfinite(bb_high) and np.isfinite(bb_low) and (bb_high - bb_low) > 0:
                pct_b = (close.iloc[-1] - bb_low) / (bb_high - bb_low)
                bb_score = float(2 * pct_b - 1.0)  # map [0,1] -> [-1,1]
            else:
                bb_score = 0.0
        except Exception:
            bb_score = 0.0

        try:
            sma20 = SMAIndicator(close, window=20).sma_indicator().iloc[-1]
            sma50 = SMAIndicator(close, window=50).sma_indicator().iloc[-1] if len(close) >= 50 else sma20
            sma200 = SMAIndicator(close, window=200).sma_indicator().iloc[-1] if len(close) >= 200 else sma50
            price = close.iloc[-1]

            # MA structure score: stacking and price vs. MAs
            if all(np.isfinite([sma20, sma50, sma200, price])):
                stack_score = (
                    np.sign((sma20 - sma50)) + np.sign((sma50 - sma200)) + np.sign((price - sma20))
                ) / 3.0
                stack_score = float(stack_score)
            else:
                stack_score = 0.0
        except Exception:
            stack_score = 0.0
            price = close.iloc[-1]

        # RSI normalization: 30 -> -1, 50 -> 0, 70 -> +1
        if rsi <= 30:
            rsi_score = -1.0
        elif rsi >= 70:
            rsi_score = 1.0
        elif rsi < 50:
            rsi_score = -1.0 + (rsi - 30) / 20.0
        else:
            rsi_score = (rsi - 50) / 20.0
        rsi_score = clip_signal(rsi_score)

        # Volume confirmation: volume vs. 20D average
        vol_avg = volume.rolling(20).mean().iloc[-1]
        vol_boost = 0.0
        try:
            if vol_avg and vol_avg > 0:
                vol_ratio = float(volume.iloc[-1] / vol_avg)
                # boost magnitude if >1.2x average; cap at +0.15
                vol_boost = float(min(0.15, max(0.0, (vol_ratio - 1.2) * 0.25)))
        except Exception:
            vol_boost = 0.0

        components = {
            "RSI": rsi_score,
            "MACD": macd_score,
            "Bollinger": bb_score,
            "MAs": stack_score,
        }

        weights = {"RSI": 0.2, "MACD": 0.3, "Bollinger": 0.2, "MAs": 0.3}
        base_signal = float(
            sum(components[k] * weights[k] for k in components if np.isfinite(components[k]))
        )
        signal = clip_signal(base_signal + np.sign(base_signal) * vol_boost)

        # Confidence: alignment of indicators with overall sign
        if signal == 0:
            align = 0
        else:
            align = sum(1 for v in components.values() if np.sign(v) == np.sign(signal) and abs(v) >= 0.35)
        confidence = 0.4 + 0.6 * (align / max(1, len(components)))
        confidence = float(max(0.0, min(1.0, confidence)))

        label = "Bullish" if signal > 0.15 else ("Bearish" if signal < -0.15 else "Neutral")

        rationale_parts = [
            f"RSI(14)={rsi:.1f} -> {rsi_score:+.2f}",
            f"MACD hist z-> {macd_hist_z.iloc[-1]:+.2f} -> {macd_score:+.2f}",
            f"BB pos -> {bb_score:+.2f}",
            f"MA stack -> {stack_score:+.2f}",
            f"Vol boost -> {vol_boost:+.2f}",
        ]
        rationale = "; ".join(rationale_parts)

        return {
            "signal": float(signal),
            "confidence": float(confidence),
            "label": label,
            "rationale": rationale,
        }
