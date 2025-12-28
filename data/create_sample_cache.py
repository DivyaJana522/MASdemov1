"""Generate sample data for testing when API is unavailable"""
import json
import sqlite3
import time
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

def generate_price_data(base_price, days=365):
    """Generate realistic looking price data"""
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    trend = np.arange(days) * (np.random.randn() * 0.5)  # Random trend
    noise = np.random.randn(days) * (base_price * 0.015)  # 1.5% noise
    
    close_prices = base_price + trend + noise
    
    data = pd.DataFrame({
        'Open': close_prices * (1 + np.random.randn(days) * 0.005),
        'High': close_prices * (1 + abs(np.random.randn(days)) * 0.008),
        'Low': close_prices * (1 - abs(np.random.randn(days)) * 0.008),
        'Close': close_prices,
        'Volume': np.random.randint(int(base_price * 1000), int(base_price * 10000), days),
        'Adj Close': close_prices,
    }, index=dates)
    
    return data

def create_sample_cache():
    """Create sample cached data for multiple popular Indian stocks"""
    
    # Create cache database
    cache_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(cache_dir, "cache.sqlite3")
    
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS cache ("
        "  key TEXT PRIMARY KEY,"
        "  value TEXT NOT NULL,"
        "  expiry INTEGER NOT NULL"
        ")"
    )
    
    # Sample stocks with base prices
    stocks = {
        "RELIANCE.NS": {"price": 2800, "pe": 28.5, "pb": 2.3, "roe": 0.15},
        "BHARTIARTL.NS": {"price": 1550, "pe": 22.3, "pb": 5.8, "roe": 0.18},
        "TCS.NS": {"price": 3900, "pe": 27.8, "pb": 12.5, "roe": 0.42},
        "INFY.NS": {"price": 1820, "pe": 25.6, "pb": 8.2, "roe": 0.31},
        "HDFCBANK.NS": {"price": 1750, "pe": 19.5, "pb": 2.8, "roe": 0.16},
        "ICICIBANK.NS": {"price": 1280, "pe": 18.2, "pb": 3.2, "roe": 0.18},
    }
    
    expiry = int(time.time()) + 86400 * 2  # 48 hours
    cache_entries = []
    
    for symbol, info in stocks.items():
        # Generate price data
        price_data = generate_price_data(info["price"], days=365)
        
        # Fundamentals
        fundamentals = {
            "pe": info["pe"],
            "pb": info["pb"],
            "roe": info["roe"],
            "debt_to_equity": np.random.uniform(0.3, 1.0),
            "fcf_yield": np.random.uniform(0.02, 0.06),
            "revenue_yoy": np.random.uniform(0.08, 0.20),
            "earnings_yoy": np.random.uniform(0.10, 0.25),
            "ebitda_margin": np.random.uniform(0.15, 0.30),
            "source": "sample_data"
        }
        
        # News
        news = [
            {
                "date": datetime.now().isoformat(),
                "headline": f"{symbol.split('.')[0]}: Strong quarterly performance beats analyst expectations",
                "summary": "Company reports robust growth with margin expansion across key business segments.",
                "source": "sample"
            },
            {
                "date": (datetime.now() - timedelta(days=2)).isoformat(),
                "headline": f"{symbol.split('.')[0]}: Management commentary suggests positive outlook",
                "summary": "Leadership team highlights strong demand trends and operational efficiency gains.",
                "source": "sample"
            }
        ]
        
        cache_entries.extend([
            (f"prices:{symbol}:1y:1d", 
             json.dumps({"data": price_data.to_json(orient="split", date_format="iso")}, ensure_ascii=False), 
             expiry),
            (f"fundamentals:{symbol}", 
             json.dumps(fundamentals, ensure_ascii=False), 
             expiry),
            (f"news:{symbol}", 
             json.dumps(news, ensure_ascii=False), 
             expiry)
        ])
    
    # Add NIFTY 50 index data
    nifty_data = generate_price_data(22000, days=365)
    cache_entries.append((
        "prices:^NSEI:1y:1d",
        json.dumps({"data": nifty_data.to_json(orient="split", date_format="iso")}, ensure_ascii=False),
        expiry
    ))
    
    for key, value, exp in cache_entries:
        conn.execute(
            "INSERT INTO cache(key, value, expiry) VALUES(?,?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, expiry=excluded.expiry",
            (key, value, exp)
        )
    
    conn.commit()
    conn.close()
    
    print(f"✓ Sample cache created at: {db_path}")
    print(f"  - {len(stocks)} stocks with 1 year of price data + fundamentals + news")
    print(f"  - Stocks: {', '.join(stocks.keys())}")
    print(f"  - ^NSEI index data included")
    print(f"  - Cache valid for 48 hours")

if __name__ == "__main__":
    create_sample_cache()
