from __future__ import annotations

import json
import os
import time
import ssl
import certifi
import urllib3
from dataclasses import dataclass
from datetime import datetime, timezone
from io import StringIO
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import pytz
import yfinance as yf
import requests
from functools import wraps

from ..utils.logging_utils import get_logger
from .cache_manager import CacheManager

# SSL Certificate workaround for yfinance
try:
    # Disable SSL warnings
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Configure SSL certificates
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
    os.environ['SSL_CERT_FILE'] = certifi.where()
    os.environ['CURL_CA_BUNDLE'] = certifi.where()
    
    # Try to use curl_cffi for better SSL handling
    try:
        from curl_cffi import requests as curl_requests
        _session = curl_requests.Session()
        _session.verify = False
    except ImportError:
        # Fallback: don't use custom session, let yfinance handle it
        _session = None
except Exception:
    _session = None


IST = pytz.timezone("Asia/Kolkata")


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator for retrying functions with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (backoff ** attempt)
                        time.sleep(wait_time)
            # All retries failed, return None or raise
            return None
        return wrapper
    return decorator


def _df_to_json(df: pd.DataFrame) -> str:
    return df.to_json(orient="split", date_format="iso")


def _df_from_json(s: str) -> pd.DataFrame:
    return pd.read_json(s, orient="split")


@dataclass
class PriceBundle:
    symbol: str
    prices: pd.DataFrame  # OHLCV, DatetimeIndex in IST


class DataFetcher:
    """Fetches market data for Indian equities with caching and graceful fallbacks.

    Provides:
      - price_data: OHLCV for the equity
      - fundamentals: key ratios and growth metrics (best-effort)
      - news: recent headlines (mock for now)
      - macro: index data for regime detection (NIFTY 50 by default)
    """

    def __init__(
        self,
        cache_path: Optional[str] = None,
        cache_ttl_seconds: int = 7200,
        index_ticker: str = "^NSEI",
    ) -> None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.cache_path = cache_path or os.path.join(base_dir, "cache.sqlite3")
        self.cache = CacheManager(self.cache_path, default_ttl=cache_ttl_seconds)
        self.index_ticker = index_ticker
        self.logger = get_logger(__name__)

    # ------------------------
    # Public API
    # ------------------------
    def build_snapshot(
        self, symbol: str, period: str = "1y", interval: str = "1d"
    ) -> Dict[str, Any]:
        self.logger.info("Building snapshot for %s", symbol)
        price_bundle = self._get_price_bundle(symbol, period, interval)
        fundamentals = self._get_fundamentals(symbol)
        news = self._get_news(symbol)
        index_bundle = self._get_price_bundle(self.index_ticker, period, interval)

        snapshot: Dict[str, Any] = {
            "price_data": self._bundle_to_dict(price_bundle),
            "fundamentals": fundamentals or {},
            "news": news or [],
            "macro": {
                "index": {
                    "ticker": self.index_ticker,
                    "prices": self._df_to_payload(index_bundle.prices) if index_bundle else None,
                }
            },
        }
        return snapshot

    # ------------------------
    # Internal helpers
    # ------------------------
    def _bundle_to_dict(self, bundle: Optional[PriceBundle]) -> Dict[str, Any]:
        if not bundle:
            return {}
        return {"symbol": bundle.symbol, "prices": self._df_to_payload(bundle.prices)}

    def _df_to_payload(self, df: Optional[pd.DataFrame]) -> Optional[Dict[str, Any]]:
        if df is None:
            return None
        try:
            return {"orient": "split", "data": df.to_json(orient="split", date_format="iso")}
        except Exception:
            return None

    def _payload_to_df(self, payload: Dict[str, Any]) -> Optional[pd.DataFrame]:
        try:
            return pd.read_json(StringIO(payload["data"]), orient="split")
        except Exception:
            return None

    def _get_price_bundle(self, symbol: str, period: str, interval: str) -> Optional[PriceBundle]:
        key = f"prices:{symbol}:{period}:{interval}"
        
        # Try cache first
        cached = self.cache.get(key)
        if cached and isinstance(cached, dict) and "data" in cached:
            try:
                df = pd.read_json(StringIO(cached["data"]), orient="split")
                df = self._ensure_ist(df)
                self.logger.debug("Cache hit for prices: %s", symbol)
                return PriceBundle(symbol=symbol, prices=df)
            except Exception as e:
                self.logger.warning("Cache parse failed for %s: %s", symbol, e)
        
        # Attempt fetch with retries
        df = self._fetch_prices_with_retry(symbol, period, interval)
        if df is not None and not df.empty:
            try:
                df = self._ensure_ist(df)
                self.cache.set(key, {"data": df.to_json(orient="split", date_format="iso")})
                self.logger.info("Successfully fetched and cached prices for %s", symbol)
                return PriceBundle(symbol=symbol, prices=df)
            except Exception as e:
                self.logger.error("Failed to cache prices for %s: %s", symbol, e)
                return PriceBundle(symbol=symbol, prices=df) if df is not None else None
        
        # Fetch failed, try to use stale cache (even if expired)
        self.logger.warning("Price fetch failed for %s, trying stale cache", symbol)
        stale_cached = self.cache.get(key, allow_stale=True)
        if stale_cached and isinstance(stale_cached, dict) and "data" in stale_cached:
            try:
                df = pd.read_json(StringIO(stale_cached["data"]), orient="split")
                df = self._ensure_ist(df)
                self.logger.info("Using stale cached data for %s", symbol)
                return PriceBundle(symbol=symbol, prices=df)
            except Exception as e:
                self.logger.error("Failed to load stale cached data for %s: %s", symbol, e)
        
        return None
    
    @retry_on_failure(max_retries=2, delay=3.0, backoff=2.5)
    def _fetch_prices_with_retry(self, symbol: str, period: str, interval: str) -> Optional[pd.DataFrame]:
        """Fetch prices with retry logic."""
        try:
            if _session:
                df = yf.download(symbol, period=period, interval=interval, auto_adjust=True, progress=False, session=_session)
            else:
                df = yf.download(symbol, period=period, interval=interval, auto_adjust=True, progress=False)
            
            if df is None or df.empty:
                raise ValueError("Empty price data")
            return df
        except Exception as e:
            self.logger.debug("Fetch attempt failed for %s: %s", symbol, e)
            raise

    def _ensure_ist(self, df: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(df.index, pd.DatetimeIndex):
            return df
        if df.index.tz is None:
            # yfinance daily often returns tz-naive; assume UTC then convert to IST midnight alignment
            df = df.tz_localize(timezone.utc)
        return df.tz_convert(IST)

    def _get_fundamentals(self, symbol: str) -> Optional[Dict[str, Any]]:
        key = f"fundamentals:{symbol}"
        
        # Check cache first
        cached = self.cache.get(key)
        if cached:
            self.logger.debug("Cache hit for fundamentals: %s", symbol)
            return cached
        
        # Attempt fetch with retry
        fundamentals = self._fetch_fundamentals_with_retry(symbol)
        if fundamentals:
            try:
                self.cache.set(key, fundamentals, ttl=48 * 3600)
                self.logger.info("Successfully fetched and cached fundamentals for %s", symbol)
                return fundamentals
            except Exception as e:
                self.logger.error("Failed to cache fundamentals for %s: %s", symbol, e)
                return fundamentals
        
        # Fetch failed, use stale cache if available
        self.logger.warning("Fundamentals fetch failed for %s, trying stale cache", symbol)
        stale_cached = self.cache.get(key, allow_stale=True)
        if stale_cached:
            self.logger.info("Using stale cached fundamentals for %s", symbol)
            return stale_cached
        
        return None
    
    @retry_on_failure(max_retries=2, delay=3.0, backoff=2.5)
    def _fetch_fundamentals_with_retry(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch fundamentals with retry logic."""
        try:
            # Use custom session to handle SSL issues
            if _session:
                t = yf.Ticker(symbol, session=_session)
            else:
                t = yf.Ticker(symbol)
            info = getattr(t, "info", {}) or {}
            financials = getattr(t, "financials", None)
            balance = getattr(t, "balance_sheet", None)
            cashflow = getattr(t, "cashflow", None)
            earnings = getattr(t, "earnings", None)

            # Initialize values with None; fill best-effort
            pe = info.get("trailingPE") or info.get("forwardPE")
            pb = info.get("priceToBook")
            roe = info.get("returnOnEquity")
            debt_to_equity = info.get("debtToEquity")
            ebitda_margin = info.get("ebitdaMargins") or info.get("ebitdaMargin")

            fcf_yield = None
            revenue_yoy = None
            earnings_yoy = None

            try:
                if cashflow is not None and not cashflow.empty and "Free Cash Flow" in cashflow.index:
                    fcf_series = cashflow.loc["Free Cash Flow"].dropna()
                    fcf = float(fcf_series.iloc[0]) if len(fcf_series) else None
                    market_cap = info.get("marketCap")
                    if fcf is not None and market_cap:
                        fcf_yield = float(fcf) / float(market_cap)
            except Exception:
                pass

            try:
                if financials is not None and not financials.empty and "Total Revenue" in financials.index:
                    rev = financials.loc["Total Revenue"].dropna()
                    if len(rev) >= 2:
                        revenue_yoy = (float(rev.iloc[0]) - float(rev.iloc[1])) / abs(float(rev.iloc[1]))
            except Exception:
                pass

            try:
                if earnings is not None and not earnings.empty and "Earnings" in earnings.columns:
                    e = earnings["Earnings"].dropna()
                    if len(e) >= 2:
                        earnings_yoy = (float(e.iloc[-1]) - float(e.iloc[-2])) / (abs(float(e.iloc[-2])) or 1.0)
            except Exception:
                pass

            fundamentals = {
                "pe": pe,
                "pb": pb,
                "roe": roe,
                "debt_to_equity": debt_to_equity,
                "fcf_yield": fcf_yield,
                "revenue_yoy": revenue_yoy,
                "earnings_yoy": earnings_yoy,
                "ebitda_margin": ebitda_margin,
                "source": "yfinance",
            }
            return fundamentals
        except Exception as e:
            self.logger.debug("Fetch attempt failed for fundamentals %s: %s", symbol, e)
            raise

    def warm_cache(self, symbols: List[str], period: str = "1y") -> Dict[str, bool]:
        """Pre-fetch and cache data for multiple symbols.
        
        Returns dict mapping symbol to success status.
        """
        results = {}
        for symbol in symbols:
            try:
                self.logger.info("Warming cache for %s", symbol)
                snapshot = self.build_snapshot(symbol, period=period)
                has_data = bool(
                    snapshot.get("price_data", {}).get("prices") or 
                    snapshot.get("fundamentals")
                )
                results[symbol] = has_data
                time.sleep(1)  # Rate limit friendly
            except Exception as e:
                self.logger.error("Cache warming failed for %s: %s", symbol, e)
                results[symbol] = False
        return results
    
    def _get_news(self, symbol: str) -> List[Dict[str, Any]]:
        key = f"news:{symbol}"
        cached = self.cache.get(key)
        if cached:
            self.logger.debug("Cache hit for news: %s", symbol)
            return cached
        # Mock news as placeholder; structure API-ready
        now_iso = datetime.now(timezone.utc).isoformat()
        news = [
            {
                "date": now_iso,
                "headline": f"{symbol}: Analyst commentary and sector update",
                "summary": "Mixed analyst views; watch earnings guidance and input costs.",
                "source": "mock",
            },
            {
                "date": now_iso,
                "headline": f"{symbol}: New product/contract win chatter",
                "summary": "Market buzz suggests incremental orders; impact TBD.",
                "source": "mock",
            },
        ]
        self.cache.set(key, news, ttl=6 * 3600)
        return news
