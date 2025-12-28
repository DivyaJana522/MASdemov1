"""
Market Regime Detection Module

This module classifies the current market conditions based on index data
(typically NIFTY 50 for Indian markets). The regime classification helps
the Master Agent adjust agent weights appropriately for prevailing conditions.

Regime Types:
- High Volatility: Market experiencing elevated uncertainty/risk
- Bullish: Uptrending market with positive momentum
- Bearish: Downtrending or neutral market conditions

The detection uses simple, interpretable rules based on:
- Realized volatility (20-day rolling)
- Moving average trends (SMA 20 vs SMA 50)
- Short-term momentum (5-day slope)
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from io import StringIO

import numpy as np
import pandas as pd

from ..utils.logging_utils import get_logger


class MarketRegimeDetector:
    """
    Classify market regime using index trend and realized volatility.
    
    This detector provides a simple, rule-based classification that helps
    adjust investment strategy based on market conditions. No ML required.
    
    Classification Logic:
    1. If volatility exceeds threshold → High Volatility
    2. Else if SMA20 > SMA50 AND positive slope → Bullish
    3. Else → Bearish
    
    Attributes:
        vol_threshold: Annualized volatility threshold (e.g., 0.25 = 25% annual vol)
    """

    def __init__(self, vol_threshold: float = 0.25) -> None:
        """
        Initialize the Market Regime Detector.
        
        Args:
            vol_threshold: Annualized volatility threshold above which market is
                          classified as "High Volatility". Default 0.25 (25%).
                          Typical ranges:
                          - Low vol: < 15%
                          - Normal: 15-25%
                          - High: > 25%
        """
        self.vol_threshold = vol_threshold
        self.logger = get_logger(__name__)
        self.logger.info(f"MarketRegimeDetector initialized (vol_threshold={vol_threshold})")

    def detect(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect current market regime from index data.
        
        Args:
            market_data: Complete market snapshot containing:
                - macro.index.prices: OHLCV data for market index
                
        Returns:
            Dictionary containing:
            - regime: Classification string ('High Volatility', 'Bullish', 'Bearish', 'Unknown')
            - details: Diagnostic information about the classification:
                - vol_20_annualized: 20-day realized volatility (annualized)
                - sma20_gt_sma50: Whether SMA(20) > SMA(50)
                - sma20_slope5: 5-day slope of SMA(20)
        """
        # Extract index data from market snapshot
        macro = (market_data or {}).get("macro") or {}
        index_block = (macro.get("index") or {})
        prices_payload = index_block.get("prices")

        if not prices_payload:
            self.logger.warning("No index data available for regime detection")
            return {
                "regime": "Unknown",
                "details": {"reason": "No index data"},
            }

        # Parse index price data
        try:
            idx = pd.read_json(StringIO(prices_payload["data"]), orient="split")
        except Exception as e:
            self.logger.error(f"Failed to parse index data: {e}")
            return {"regime": "Unknown", "details": {"reason": "Index payload parse error"}}

        if idx is None or idx.empty:
            self.logger.warning("Empty index data received")
            return {"regime": "Unknown", "details": {"reason": "Empty index data"}}

        close = idx["Close"].astype(float).dropna()
        
        # Need sufficient history for reliable signals
        if len(close) < 60:
            self.logger.warning(f"Insufficient index history: {len(close)} days (need 60+)")
            return {"regime": "Unknown", "details": {"reason": "Insufficient index history"}}

        # Calculate 20-day realized volatility (annualized)
        ret = close.pct_change().dropna()
        if len(ret) >= 20:
            vol_20 = float(ret.rolling(20).std(ddof=0).iloc[-1] * np.sqrt(252))
        else:
            vol_20 = float(ret.std(ddof=0) * np.sqrt(252))
        
        self.logger.debug(f"20-day annualized volatility: {vol_20:.2%}")

        # Calculate moving averages for trend determination
        sma20 = close.rolling(20).mean()
        sma50 = close.rolling(50).mean()
        
        # Calculate short-term momentum: 5-day change in SMA(20)
        if len(sma20) >= 5:
            slope20 = float((sma20.iloc[-1] - sma20.iloc[-5]) / (abs(sma20.iloc[-5]) + 1e-9))
        else:
            slope20 = 0.0
        
        self.logger.debug(f"SMA(20)={sma20.iloc[-1]:.2f}, SMA(50)={sma50.iloc[-1]:.2f}, slope={slope20:.4f}")

        # Apply classification rules
        if vol_20 >= self.vol_threshold:
            regime = "High Volatility"
            self.logger.info(f"Regime: High Volatility (vol={vol_20:.2%} > {self.vol_threshold:.2%})")
        elif sma20.iloc[-1] > sma50.iloc[-1] and slope20 > 0:
            regime = "Bullish"
            self.logger.info("Regime: Bullish (SMA20 > SMA50, positive momentum)")
        else:
            regime = "Bearish"
            self.logger.info("Regime: Bearish (default classification)")

        return {
            "regime": regime,
            "details": {
                "vol_20_annualized": round(vol_20, 4),
                "sma20_gt_sma50": bool(sma20.iloc[-1] > sma50.iloc[-1]),
                "sma20_slope5": round(slope20, 4),
            },
        }
