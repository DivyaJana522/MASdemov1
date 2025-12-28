"""
Cache warming script to pre-fetch data for common Indian stocks.
Run this periodically (e.g., once daily) to maintain fresh cache and avoid rate limits.
"""
from __future__ import annotations

import time
from typing import List

from multi_agent_stock_platform.data.data_fetcher import DataFetcher
from multi_agent_stock_platform.utils.logging_utils import get_logger

logger = get_logger(__name__)

# Popular NSE stocks to cache
POPULAR_STOCKS: List[str] = [
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS",
    "HINDUNILVR.NS",
    "ITC.NS",
    "SBIN.NS",
    "BHARTIARTL.NS",
    "KOTAKBANK.NS",
    "LT.NS",
    "AXISBANK.NS",
    "MARUTI.NS",
    "SUNPHARMA.NS",
    "TITAN.NS",
    "WIPRO.NS",
    "ULTRACEMCO.NS",
    "ONGC.NS",
    "NTPC.NS",
    "POWERGRID.NS",
]


def warm_cache(symbols: List[str] = None, delay: float = 2.0) -> None:
    """
    Warm cache for specified symbols.
    
    Args:
        symbols: List of stock symbols (default: POPULAR_STOCKS)
        delay: Delay in seconds between requests to avoid rate limits
    """
    if symbols is None:
        symbols = POPULAR_STOCKS
    
    fetcher = DataFetcher(cache_ttl_seconds=7200)  # 2 hour cache
    
    logger.info("Starting cache warming for %d symbols", len(symbols))
    success_count = 0
    fail_count = 0
    
    for i, symbol in enumerate(symbols, 1):
        try:
            logger.info("[%d/%d] Fetching data for %s...", i, len(symbols), symbol)
            snapshot = fetcher.build_snapshot(symbol, period="1y")
            
            has_prices = bool(snapshot.get("price_data", {}).get("prices"))
            has_fundamentals = bool(snapshot.get("fundamentals"))
            
            if has_prices or has_fundamentals:
                logger.info("✓ Successfully cached %s (prices: %s, fundamentals: %s)", 
                           symbol, has_prices, has_fundamentals)
                success_count += 1
            else:
                logger.warning("⚠ No data available for %s", symbol)
                fail_count += 1
            
            # Rate limiting: wait between requests
            if i < len(symbols):
                logger.debug("Waiting %.1f seconds before next request...", delay)
                time.sleep(delay)
                
        except Exception as e:
            logger.error("✗ Failed to cache %s: %s", symbol, e)
            fail_count += 1
            time.sleep(delay * 2)  # Wait longer after errors
    
    logger.info("Cache warming completed: %d success, %d failed", success_count, fail_count)


if __name__ == "__main__":
    import sys
    
    # Allow custom symbols via command line
    if len(sys.argv) > 1:
        custom_symbols = sys.argv[1:]
        logger.info("Warming cache for custom symbols: %s", custom_symbols)
        warm_cache(custom_symbols)
    else:
        warm_cache()
