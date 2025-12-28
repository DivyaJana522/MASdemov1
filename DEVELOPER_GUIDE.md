# Developer Guide - Multi-Agent Stock Analysis Platform

**Last Updated**: December 24, 2025  
**Version**: 1.0.0  
**Target Audience**: Developers, Contributors, Technical Architects  

---

## 📑 Table of Contents

1. [Project Overview](#-project-overview)
2. [Architecture Deep Dive](#-architecture-deep-dive)
3. [Code Structure](#-code-structure)
4. [Data Flow](#-data-flow)
5. [Component Details](#-component-details)
6. [Known Issues & Solutions](#-known-issues--solutions)
7. [Development Setup](#-development-setup)
8. [Testing](#-testing)
9. [Contributing Guidelines](#-contributing-guidelines)

---

## 🎯 Project Overview

### Purpose
A production-ready multi-agent stock analysis platform for Indian equity markets (NSE/BSE) that combines Technical, Fundamental, and Sentiment analysis through intelligent coordination and market regime adaptation.

### Key Technologies
- **Language**: Python 3.14+
- **Data Source**: Yahoo Finance API (via `yfinance`)
- **Caching**: SQLite with TTL-based expiration
- **Web Framework**: Streamlit
- **Data Processing**: pandas, numpy
- **Technical Analysis**: ta (Technical Analysis Library)
- **Sentiment Analysis**: vaderSentiment
- **Testing**: Custom test framework with 18 comprehensive tests

### Design Philosophy
- **Modularity**: Each agent is independent and can be used standalone
- **Fault Tolerance**: Graceful degradation with stale cache fallback
- **Extensibility**: Easy to add new agents or modify existing ones
- **Production-First**: Error handling, logging, and monitoring built-in
- **Performance**: Parallel agent execution, efficient caching

---

## 🏗️ Architecture Deep Dive

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Streamlit UI   │  │   CLI (main)    │  │   Python API    │ │
│  │  (ui/app.py)    │  │  (main.py)      │  │  (Direct Import)│ │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘ │
└───────────┼──────────────────────┼──────────────────────┼─────────┘
            │                      │                      │
            └──────────────────────┴──────────────────────┘
                                   │
┌───────────────────────────────────▼──────────────────────────────┐
│                       COORDINATION LAYER                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              MasterAgent (master_agent.py)               │   │
│  │  ┌────────────────────┐  ┌─────────────────────────┐    │   │
│  │  │ Market Regime      │  │ Dynamic Weighting       │    │   │
│  │  │ Detection          │  │ & Cross-Verification    │    │   │
│  │  └────────────────────┘  └─────────────────────────┘    │   │
│  │             Orchestrates parallel agent execution         │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────────────┬──────────────────────────────┘
                                    │
            ┌───────────────────────┴───────────────────────┐
            │                                                │
┌───────────▼────────┐  ┌───────────▼────────┐  ┌─────────▼──────┐
│   AGENT LAYER      │  │   AGENT LAYER      │  │  AGENT LAYER   │
│                    │  │                    │  │                │
│  TechnicalAgent    │  │  FundamentalAgent  │  │ SentimentAgent │
│  ─────────────     │  │  ─────────────     │  │ ─────────────  │
│  • RSI             │  │  • P/E Ratio       │  │ • VADER        │
│  • MACD            │  │  • P/B Ratio       │  │ • News         │
│  • Bollinger Bands │  │  • ROE             │  │   Headlines    │
│  • Moving Averages │  │  • Growth Metrics  │  │ • Polarity     │
│                    │  │                    │  │   Thresholds   │
└──────────┬─────────┘  └──────────┬─────────┘  └────────┬───────┘
           │                       │                      │
           └───────────────────────┴──────────────────────┘
                                   │
┌───────────────────────────────────▼──────────────────────────────┐
│                          DATA LAYER                               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │               DataFetcher (data_fetcher.py)              │   │
│  │  ┌────────────────────┐  ┌─────────────────────────┐    │   │
│  │  │ Price Data Bundle  │  │ Fundamental Data        │    │   │
│  │  │ (OHLCV + Tech)     │  │ (P/E, P/B, ROE, etc.)   │    │   │
│  │  │ TTL: 2 hours       │  │ TTL: 48 hours           │    │   │
│  │  └────────┬───────────┘  └────────┬────────────────┘    │   │
│  └───────────┼──────────────────────────┼───────────────────┘   │
│              │                          │                        │
│  ┌───────────▼──────────────────────────▼───────────────────┐   │
│  │          CacheManager (cache_manager.py)                 │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │         SQLite Database (cache.sqlite3)         │    │   │
│  │  │  • Primary cache with TTL enforcement           │    │   │
│  │  │  • Stale cache fallback for rate limit recovery │    │   │
│  │  │  • Structured schema with timestamps            │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                               │                                   │
│  ┌────────────────────────────▼────────────────────────────┐    │
│  │           Yahoo Finance API (yfinance library)          │    │
│  │  • Primary data source for NSE/BSE stocks              │    │
│  │  • Rate limited (handled gracefully)                   │    │
│  └─────────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────┐
│                        UTILITY LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ ResultStorage│  │ Logging      │  │ Normalization│           │
│  │ (timestamps) │  │ (structured) │  │ (signals)    │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└───────────────────────────────────────────────────────────────────┘
```

### Design Patterns Used

1. **Strategy Pattern**: Each agent implements a common interface
2. **Facade Pattern**: MasterAgent provides unified interface to agents
3. **Singleton Pattern**: CacheManager ensures single DB connection
4. **Observer Pattern**: Agents notify MasterAgent of their signals
5. **Factory Pattern**: DataFetcher creates appropriate data bundles

---

## 📂 Code Structure

### Directory Layout

```
multi_agent_stock_platform/
│
├── agents/                      # Specialized analysis agents
│   ├── __init__.py             # Package initialization
│   ├── base_agent.py           # Abstract base class for agents
│   ├── technical_agent.py      # Technical analysis (RSI, MACD, etc.)
│   ├── fundamental_agent.py    # Fundamental analysis (P/E, ROE, etc.)
│   └── sentiment_agent.py      # Sentiment analysis (VADER)
│
├── coordination/                # Agent coordination and orchestration
│   ├── __init__.py             # Package initialization
│   ├── master_agent.py         # Main orchestrator (parallel execution)
│   └── market_regime.py        # Market regime detection logic
│
├── data/                        # Data management and caching
│   ├── __init__.py             # Package initialization
│   ├── data_fetcher.py         # Yahoo Finance data retrieval
│   ├── cache_manager.py        # SQLite cache with TTL
│   ├── create_sample_cache.py  # Pre-populate cache utility
│   ├── warm_cache.py           # Cache warming for popular stocks
│   └── cache.sqlite3           # SQLite database file (generated)
│
├── ui/                          # User interface
│   ├── __init__.py             # Package initialization
│   └── app.py                  # Streamlit web application
│
├── utils/                       # Utility functions
│   ├── __init__.py             # Package initialization
│   ├── result_storage.py       # Result persistence with timestamps
│   ├── logging_utils.py        # Structured logging setup
│   └── normalization.py        # Signal normalization functions
│
├── results/                     # Stored analysis results (git-ignored)
│   └── (JSON files)            # Format: SYMBOL_YYYYMMDD_HHMMSS.json
│
├── myenv/                       # Virtual environment (git-ignored)
│   └── (Python packages)       # Isolated dependencies
│
├── main.py                      # CLI entry point
├── test_system.py              # Comprehensive test suite (18 tests)
├── health_check.py             # System health check utility
├── smoke_test.py               # Quick smoke test
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git exclusions
├── README.md                   # User documentation (YOU ARE HERE in dev guide)
└── DEVELOPER_GUIDE.md          # This file - Technical documentation
```

### File-by-File Breakdown

#### Core Application Files

**`main.py`** (287 lines)
- **Purpose**: CLI entry point for stock analysis
- **Key Functions**:
  - `main()`: Argument parsing and orchestration
  - Progress indicators with colored output
  - Result saving with `--save` flag
  - Verbose JSON output with `--verbose` flag
- **Dependencies**: argparse, MasterAgent, DataFetcher, ResultStorage
- **Error Handling**: Comprehensive try-catch with user-friendly messages

**`test_system.py`** (520 lines)
- **Purpose**: Automated testing suite
- **Test Categories**:
  1. Dependency tests (1 test)
  2. Import tests (4 tests)
  3. Functionality tests (7 tests)
  4. Integration tests (1 test)
  5. File structure tests (4 tests)
  6. Documentation tests (1 test)
- **Features**: Color-coded output, detailed failure reporting, pass rate calculation
- **Usage**: `python -m multi_agent_stock_platform.test_system`

#### Agent Layer

**`agents/base_agent.py`** (50 lines)
- **Purpose**: Abstract base class defining agent interface
- **Key Methods**:
  - `analyze(symbol, data)`: Must be implemented by subclasses
- **Returns**: Dictionary with `signal`, `confidence`, `reasoning`

**`agents/technical_agent.py`** (180 lines)
- **Purpose**: Technical indicator analysis
- **Indicators Calculated**:
  - RSI (Relative Strength Index): 14-period
  - MACD (Moving Average Convergence Divergence): 12/26/9 periods
  - Bollinger Bands: 20-period SMA ± 2 std dev
  - SMA50/SMA200: 50-day and 200-day simple moving averages
- **Signal Logic**:
  ```
  BUY:  RSI < 40 AND (MACD bullish OR price < lower Bollinger Band) AND SMA50 > SMA200
  SELL: RSI > 60 AND (MACD bearish OR price > upper Bollinger Band) AND SMA50 < SMA200
  HOLD: Otherwise
  ```
- **Confidence Calculation**: Based on indicator strength and agreement

**`agents/fundamental_agent.py`** (165 lines)
- **Purpose**: Financial metrics analysis
- **Metrics Used**:
  - P/E Ratio (Price-to-Earnings): Valuation metric
  - P/B Ratio (Price-to-Book): Book value comparison
  - ROE (Return on Equity): Profitability metric
  - Revenue Growth: Year-over-year growth rate
  - Profit Growth: Earnings growth rate
- **Signal Logic**:
  ```
  BUY:  (P/E < 15 OR P/B < 1.5) AND ROE > 15% AND Growth > 10%
  SELL: (P/E > 25 OR P/B > 3) AND ROE < 10%
  HOLD: Otherwise
  ```
- **Fallback**: Returns NEUTRAL with 0.5 confidence if data unavailable

**`agents/sentiment_agent.py`** (120 lines)
- **Purpose**: News sentiment analysis
- **Technology**: VADER (Valence Aware Dictionary and sEntiment Reasoner)
- **Data Sources**: Recent news headlines for the stock
- **Signal Logic**:
  ```
  POSITIVE: Compound score > 0.05
  NEGATIVE: Compound score < -0.05
  NEUTRAL: Between -0.05 and 0.05
  ```
- **Confidence**: Absolute value of compound score
- **Fallback**: Returns NEUTRAL if no news available

#### Coordination Layer

**`coordination/master_agent.py`** (320 lines)
- **Purpose**: Orchestrates all agents and makes final decision
- **Key Methods**:
  - `analyze(symbol)`: Main entry point
  - `_detect_market_regime(data)`: Determines market condition
  - `_adjust_weights_for_regime(regime)`: Dynamic weight adjustment
  - `_cross_verify_signals(signals)`: Validates agent agreement
  - `_calculate_final_confidence(signals, weights)`: Confidence scoring
- **Process Flow**:
  1. Fetch data via DataFetcher
  2. Detect market regime
  3. Execute agents in parallel (using concurrent.futures)
  4. Adjust weights based on regime
  5. Cross-verify signals
  6. Calculate final confidence
  7. Return unified decision
- **Regime-Based Weighting**:
  ```python
  BULLISH:          technical *= 1.2 (favor momentum)
  BEARISH:          fundamental *= 1.3 (favor value)
  HIGH_VOLATILITY:  sentiment *= 0.8 (discount noise)
  ```

**`coordination/market_regime.py`** (95 lines)
- **Purpose**: Market condition detection
- **Regime Types**:
  - **BULLISH**: SMA50 > SMA200 (Golden Cross) AND volatility < 3%
  - **BEARISH**: SMA50 < SMA200 (Death Cross) AND declining prices
  - **HIGH_VOLATILITY**: 20-day volatility > 3%
- **Algorithm**:
  ```python
  1. Calculate 20-day volatility (standard deviation of returns)
  2. Check SMA50 vs SMA200 (trend direction)
  3. Check recent price momentum (last 5 days)
  4. Return regime classification
  ```

#### Data Layer

**`data/data_fetcher.py`** (285 lines)
- **Purpose**: Central data retrieval with caching
- **Key Methods**:
  - `get_price_data(symbol, period)`: OHLCV data with technical indicators
  - `get_fundamental_data(symbol)`: Financial metrics
  - `get_news(symbol, max_items)`: Recent news headlines
  - `_get_price_bundle(symbol)`: Complete price + technical data
  - `_get_fundamentals(symbol)`: Cached fundamental metrics
- **Caching Strategy**:
  - Price data: 2-hour TTL (7200 seconds)
  - Fundamental data: 48-hour TTL (172800 seconds)
  - Stale fallback: Uses expired cache if API fails
- **Error Handling**:
  - Retry logic with 3-second delays
  - Graceful degradation to stale cache
  - Comprehensive logging

**`data/cache_manager.py`** (210 lines)
- **Purpose**: SQLite-based caching with TTL
- **Database Schema**:
  ```sql
  CREATE TABLE cache (
      key TEXT PRIMARY KEY,
      data BLOB,          -- Pickled Python object
      timestamp REAL,     -- Unix timestamp
      ttl INTEGER         -- Time-to-live in seconds
  );
  ```
- **Key Methods**:
  - `get(key, allow_stale=False)`: Retrieve cached data
  - `set(key, data, ttl)`: Store data with expiration
  - `is_expired(key)`: Check if cache entry is stale
  - `clear()`: Delete all cache entries
- **Features**:
  - Atomic operations with context manager
  - Automatic expiration checking
  - Stale cache fallback mode
  - Thread-safe operations

**`data/create_sample_cache.py`** (145 lines)
- **Purpose**: Pre-populate cache with sample data
- **Stocks Cached**: RELIANCE.NS, BHARTIARTL.NS, TCS.NS, INFY.NS, HDFCBANK.NS, ICICIBANK.NS
- **Data Cached**: Price bundles + Fundamental data
- **Usage**: Run before first use to avoid rate limiting

**`data/warm_cache.py`** (120 lines)
- **Purpose**: Refresh cache for popular stocks
- **Scheduling**: Can be run as cron job for production
- **Benefit**: Reduces API calls during peak usage

#### Utility Layer

**`utils/result_storage.py`** (195 lines)
- **Purpose**: Timestamped result persistence
- **File Format**: `results/{SYMBOL}_{YYYYMMDD_HHMMSS}.json`
- **Key Methods**:
  - `save_result(symbol, result)`: Save analysis to JSON
  - `get_latest_result(symbol)`: Load most recent result
  - `list_results(symbol)`: List all results for a symbol
  - `cleanup_old_results(days)`: Delete results older than X days
- **Features**:
  - Automatic directory creation
  - Metadata inclusion (timestamp, symbol)
  - Safe file operations with error handling

**`utils/logging_utils.py`** (75 lines)
- **Purpose**: Structured logging configuration
- **Format**: `[%(asctime)s] %(levelname)s - %(name)s - %(message)s`
- **Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Output**: Console (can be extended to file)

**`utils/normalization.py`** (60 lines)
- **Purpose**: Signal standardization functions
- **Functions**:
  - `normalize_signal(signal)`: Convert to BUY/SELL/HOLD
  - `normalize_confidence(confidence)`: Ensure 0.0-1.0 range
- **Usage**: Ensures consistent output across agents

#### UI Layer

**`ui/app.py`** (245 lines)
- **Purpose**: Streamlit web interface
- **Features**:
  - Stock symbol input with validation
  - Analysis button with loading spinner
  - Market regime indicator (color-coded)
  - Individual agent signals with reasoning
  - Overall recommendation with confidence bar
  - Historical price chart (last 30 days)
  - Result auto-save notification
- **Layout**:
  ```
  [Title]
  [Stock Symbol Input] [Analyze Button]
  ─────────────────────────────────
  [Market Regime Badge]
  [Overall Decision Card]
    - Signal: BUY/SELL/HOLD
    - Confidence: Progress bar
  ─────────────────────────────────
  [Agent Signals (3 expandable sections)]
    - Technical Agent
    - Fundamental Agent
    - Sentiment Agent
  ─────────────────────────────────
  [Price Chart (Plotly)]
  ```

---

## 🔄 Data Flow

### Complete Analysis Flow (Step-by-Step)

```
1. USER INPUT
   ↓
   Stock symbol (e.g., "RELIANCE.NS")
   ↓
   
2. ENTRY POINT
   ↓
   CLI (main.py) OR Web UI (app.py) OR Python API
   ↓
   
3. MASTER AGENT INITIALIZATION
   ↓
   MasterAgent.analyze(symbol)
   ↓
   
4. DATA FETCHING
   ↓
   DataFetcher.get_price_data(symbol)
   ├─→ Check CacheManager
   │   ├─→ Cache HIT (< 2 hours old) → Return cached data
   │   └─→ Cache MISS or EXPIRED
   │       ├─→ Fetch from Yahoo Finance API
   │       │   ├─→ SUCCESS → Cache and return
   │       │   └─→ FAIL (rate limit)
   │       │       └─→ Stale cache fallback (allow_stale=True)
   ↓
   DataFetcher.get_fundamental_data(symbol)
   ├─→ Check CacheManager (48-hour TTL)
   │   ├─→ Cache HIT → Return cached data
   │   └─→ Cache MISS or EXPIRED → Fetch from API with fallback
   ↓
   
5. MARKET REGIME DETECTION
   ↓
   MarketRegimeDetector.detect(data)
   ├─→ Calculate 20-day volatility
   ├─→ Check SMA50 vs SMA200
   ├─→ Analyze recent momentum
   └─→ Return: BULLISH / BEARISH / HIGH_VOLATILITY
   ↓
   
6. PARALLEL AGENT EXECUTION
   ↓
   ┌────────────────┬────────────────┬────────────────┐
   │                │                │                │
   ▼                ▼                ▼                ▼
   TechnicalAgent   FundamentalAgent SentimentAgent
   │                │                │
   │ Calculate:     │ Calculate:     │ Fetch & Analyze:
   │ • RSI          │ • P/E Ratio    │ • News headlines
   │ • MACD         │ • P/B Ratio    │ • VADER sentiment
   │ • Bollinger    │ • ROE          │
   │ • Moving Avg   │ • Growth       │
   │                │                │
   │ → Signal       │ → Signal       │ → Signal
   │ → Confidence   │ → Confidence   │ → Confidence
   │ → Reasoning    │ → Reasoning    │ → Reasoning
   │                │                │
   └────────────────┴────────────────┴────────────────┘
                           │
                           ▼
   
7. WEIGHT ADJUSTMENT (Regime-Based)
   ↓
   IF BULLISH:       technical_weight *= 1.2
   IF BEARISH:       fundamental_weight *= 1.3
   IF HIGH_VOL:      sentiment_weight *= 0.8
   ↓
   
8. CROSS-VERIFICATION
   ↓
   Check agent agreement:
   ├─→ All BUY → High confidence
   ├─→ All SELL → High confidence
   ├─→ Mixed signals → Adjust confidence down
   └─→ Majority rule with weighted voting
   ↓
   
9. FINAL DECISION CALCULATION
   ↓
   Weighted average of signals
   ├─→ Signal: BUY / SELL / HOLD
   ├─→ Confidence: 0.0 - 1.0
   └─→ Reasoning: Aggregated from agents
   ↓
   
10. RESULT PACKAGING
    ↓
    {
      "decision": "BUY",
      "confidence": 0.78,
      "market_regime": "BULLISH",
      "agent_signals": {
        "technical": {...},
        "fundamental": {...},
        "sentiment": {...}
      },
      "timestamp": "2025-12-24T18:30:00"
    }
    ↓
    
11. RESULT STORAGE (Optional)
    ↓
    IF --save flag:
      ResultStorage.save_result(symbol, result)
      ↓
      Save to: results/RELIANCE_NS_20251224_183000.json
    ↓
    
12. OUTPUT
    ↓
    ├─→ CLI: Colored text output
    ├─→ Web UI: Formatted dashboard
    └─→ Python API: Dictionary return
```

### Caching Flow (Detailed)

```
REQUEST: Get price data for RELIANCE.NS
  ↓
  DataFetcher.get_price_data("RELIANCE.NS")
  ↓
  Check cache: cache_key = "price_bundle_RELIANCE.NS"
  ↓
  CacheManager.get("price_bundle_RELIANCE.NS")
  ↓
  ┌─────────────────────────────────────┐
  │  Check if key exists in SQLite DB   │
  └─────────────────┬───────────────────┘
                    │
        ┌───────────┴───────────┐
        │ EXISTS?               │
        │                       │
     NO │                       │ YES
        ▼                       ▼
   Return None          Check timestamp
                               │
                    ┌──────────┴───────────┐
                    │ Age < TTL (2 hours)? │
                    │                      │
                 NO │                      │ YES
                    ▼                      ▼
              Check allow_stale     Return cached data
                    │                      │
         ┌──────────┴──────────┐          │
         │ allow_stale=True?   │          │
         │                     │          │
      NO │                     │ YES      │
         ▼                     ▼          │
    Return None        Return stale      │
         │             cached data        │
         │                  │             │
         └──────────────────┴─────────────┘
                            │
                  ┌─────────▼─────────┐
                  │ Cached data found?│
                  │                   │
               NO │                   │ YES
                  ▼                   ▼
         Fetch from Yahoo     Return to caller
         Finance API               ↓
                  │              USE DATA
                  ▼
         ┌───────────────┐
         │ API SUCCESS?  │
         │               │
      NO │               │ YES
         ▼               ▼
    Try stale     Store in cache
    fallback      (CacheManager.set)
         │               │
         │        TTL = 7200 seconds
         │               │
         └───────────────┘
                 │
                 ▼
         Return to caller
```

---

## 🔍 Component Details

### Technical Agent - Deep Dive

**Indicator Calculations**:

```python
# RSI (Relative Strength Index)
def calculate_rsi(prices, period=14):
    """
    RSI = 100 - (100 / (1 + RS))
    where RS = Average Gain / Average Loss over period
    """
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

# MACD (Moving Average Convergence Divergence)
def calculate_macd(prices):
    """
    MACD Line = 12-day EMA - 26-day EMA
    Signal Line = 9-day EMA of MACD Line
    Histogram = MACD Line - Signal Line
    """
    ema12 = prices.ewm(span=12, adjust=False).mean()
    ema26 = prices.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    histogram = macd_line - signal_line
    return {
        'macd': macd_line.iloc[-1],
        'signal': signal_line.iloc[-1],
        'histogram': histogram.iloc[-1]
    }

# Bollinger Bands
def calculate_bollinger(prices, period=20, std_dev=2):
    """
    Middle Band = 20-day SMA
    Upper Band = Middle Band + (2 * standard deviation)
    Lower Band = Middle Band - (2 * standard deviation)
    """
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    return {
        'upper': upper.iloc[-1],
        'middle': sma.iloc[-1],
        'lower': lower.iloc[-1],
        'current': prices.iloc[-1]
    }
```

**Signal Generation Logic**:

```python
def generate_signal(rsi, macd, bollinger, sma50, sma200, current_price):
    """
    Decision tree for technical signal generation
    """
    # Strong BUY conditions
    if (rsi < 30 and  # Oversold
        macd['histogram'] > 0 and  # Bullish momentum
        current_price < bollinger['lower'] and  # Below lower band
        sma50 > sma200):  # Golden cross
        return {"signal": "BUY", "confidence": 0.9, "reasoning": "Strong technical buy signals"}
    
    # Moderate BUY conditions
    elif (rsi < 40 and
          (macd['histogram'] > 0 or current_price < bollinger['middle']) and
          sma50 > sma200):
        return {"signal": "BUY", "confidence": 0.7, "reasoning": "Moderate technical buy signals"}
    
    # Strong SELL conditions
    elif (rsi > 70 and  # Overbought
          macd['histogram'] < 0 and  # Bearish momentum
          current_price > bollinger['upper'] and  # Above upper band
          sma50 < sma200):  # Death cross
        return {"signal": "SELL", "confidence": 0.9, "reasoning": "Strong technical sell signals"}
    
    # Moderate SELL conditions
    elif (rsi > 60 and
          (macd['histogram'] < 0 or current_price > bollinger['middle']) and
          sma50 < sma200):
        return {"signal": "SELL", "confidence": 0.7, "reasoning": "Moderate technical sell signals"}
    
    # Default HOLD
    else:
        return {"signal": "HOLD", "confidence": 0.5, "reasoning": "No clear technical signals"}
```

### Master Agent - Decision Algorithm

**Weighted Voting System**:

```python
def calculate_final_decision(agent_signals, weights, regime):
    """
    Weighted voting with regime adjustment
    """
    # Convert signals to numeric scores
    signal_scores = {
        "BUY": 1.0,
        "HOLD": 0.0,
        "SELL": -1.0,
        "POSITIVE": 0.5,
        "NEGATIVE": -0.5,
        "NEUTRAL": 0.0
    }
    
    # Calculate weighted average
    total_weight = 0
    weighted_sum = 0
    
    for agent_name, agent_data in agent_signals.items():
        signal = agent_data['signal']
        confidence = agent_data['confidence']
        weight = weights.get(agent_name, 1.0)
        
        score = signal_scores.get(signal, 0.0)
        weighted_sum += score * confidence * weight
        total_weight += weight * confidence
    
    # Normalize to [-1, 1]
    if total_weight > 0:
        final_score = weighted_sum / total_weight
    else:
        final_score = 0.0
    
    # Convert back to signal
    if final_score > 0.2:
        decision = "BUY"
        confidence = min(final_score, 1.0)
    elif final_score < -0.2:
        decision = "SELL"
        confidence = min(abs(final_score), 1.0)
    else:
        decision = "HOLD"
        confidence = 0.5
    
    # Regime-based confidence adjustment
    if regime == "HIGH_VOLATILITY":
        confidence *= 0.9  # Reduce confidence in volatile markets
    
    return {
        "decision": decision,
        "confidence": confidence,
        "regime": regime
    }
```

---

## 🐛 Known Issues & Solutions

### Issue #1: Yahoo Finance Rate Limiting

**Problem**:
- Yahoo Finance API limits requests to prevent abuse
- Repeated calls for same stock result in "Too Many Requests" (429 error)
- Symptom: `yfinance` returns empty DataFrame or raises exception

**Root Cause**:
- No official rate limit documentation
- Appears to be ~2000 requests per hour per IP
- Triggered easily during development/testing

**Solution Implemented**:

1. **Primary Cache with TTL**:
   ```python
   # data/data_fetcher.py
   PRICE_CACHE_TTL = 7200  # 2 hours
   FUNDAMENTAL_CACHE_TTL = 172800  # 48 hours
   ```

2. **Stale Cache Fallback**:
   ```python
   # Try fresh API call first
   data = self._fetch_from_api(symbol)
   
   if data is None or data.empty:
       # Fall back to stale cache
       data = self.cache.get(cache_key, allow_stale=True)
       if data is not None:
           print(f"Using stale cache for {symbol}")
   ```

3. **Pre-Population Strategy**:
   ```bash
   # Run before first use
   python -m multi_agent_stock_platform.data.create_sample_cache
   ```

**How to Monitor**:
```python
# Check cache hit rate
from multi_agent_stock_platform.data.cache_manager import CacheManager
cm = CacheManager()
# Add logging to track hits/misses
```

**Future Improvements**:
- Implement exponential backoff on rate limit detection
- Add request queue with rate limiting
- Consider alternative data sources (Alpha Vantage, Polygon.io)

---

### Issue #2: PowerShell Execution Policy (Windows)

**Problem**:
- Windows PowerShell blocks script execution by default
- Prevents virtual environment activation
- Error: "cannot be loaded because running scripts is disabled"

**Root Cause**:
- Windows security policy restricts unsigned scripts
- Virtual environment activation scripts are unsigned

**Solution Implemented**:

1. **Bypass Activation** (Use full Python path):
   ```bash
   # Instead of activating venv
   cd c:\Users\djana\masdemov1
   multi_agent_stock_platform\myenv\Scripts\python.exe -m multi_agent_stock_platform.main RELIANCE.NS
   ```

2. **Alternative** (Change execution policy - requires admin):
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

**Why Our Approach Works**:
- Directly calls Python executable (no script execution needed)
- Works in both CMD and PowerShell
- No admin privileges required
- Portable across Windows systems

---

### Issue #3: Cache File Locking (Windows)

**Problem**:
- SQLite database locks prevent concurrent access
- Error: "database is locked"
- Occurs during testing or when multiple processes access cache

**Root Cause**:
- Windows file locking more aggressive than Linux
- SQLite uses file-level locks
- Python may not release locks immediately

**Solution Implemented**:

1. **Context Manager Pattern**:
   ```python
   # data/cache_manager.py
   def get(self, key, allow_stale=False):
       with sqlite3.connect(self.db_path) as conn:
           # Auto-closes connection
           cursor = conn.cursor()
           # ... query logic ...
       # Connection closed here
   ```

2. **Test-Specific Fix**:
   ```python
   # test_system.py - test_cache_manager()
   import os
   test_cache_path = os.path.join(temp_dir, f"test_cache_{os.getpid()}.db")
   # Use PID to avoid conflicts
   
   # Add delay for Windows file release
   time.sleep(0.5)
   ```

3. **Graceful Error Handling**:
   ```python
   try:
       os.remove(cache_path)
   except PermissionError:
       print(f"Warning: Could not delete {cache_path} (file locked)")
   ```

**Best Practices**:
- Always use context managers for DB connections
- Close connections explicitly when done
- Use unique filenames for test databases
- Add small delays after file operations on Windows

---

### Issue #4: Missing scipy Dependency

**Problem**:
- `scipy` required by some technical analysis functions
- Not automatically installed despite being in `requirements.txt`
- Test failure: `ModuleNotFoundError: No module named 'scipy'`

**Root Cause**:
- Large binary package (~40MB)
- May fail to install in constrained environments
- Not used directly in code, but required by `ta` library

**Solution**:
```bash
cd c:\Users\djana\masdemov1
multi_agent_stock_platform\myenv\Scripts\pip.exe install scipy
```

**Prevention**:
- Verify all requirements installed: `pip install -r requirements.txt`
- Run `test_system.py` to catch missing dependencies
- Add dependency check in health_check.py

**Related Dependencies**:
```
scipy (1.16.3)       - Scientific computing
numpy (1.26+)        - Array operations (required by scipy)
pandas (2.0+)        - Data structures (required by ta)
ta (0.11.0)          - Technical analysis (requires scipy)
```

---

### Issue #5: Streamlit Port Already in Use

**Problem**:
- Port 8501 already occupied by previous Streamlit instance
- Error: "Address already in use"

**Solution**:

1. **Specify Different Port**:
   ```bash
   multi_agent_stock_platform\myenv\Scripts\python.exe -m streamlit run multi_agent_stock_platform/ui/app.py --server.port 8502
   ```

2. **Kill Existing Process** (Windows):
   ```bash
   # Find process using port 8501
   netstat -ano | findstr :8501
   # Kill process by PID
   taskkill /PID <process_id> /F
   ```

3. **Kill Existing Process** (Linux/Mac):
   ```bash
   lsof -ti:8501 | xargs kill -9
   ```

---

### Issue #6: Empty DataFrame from yfinance

**Problem**:
- `yfinance` returns empty DataFrame for some stock symbols
- No error raised, just empty data

**Possible Causes**:
1. Invalid stock symbol (not listed on NSE/BSE)
2. Symbol format incorrect (missing `.NS` suffix)
3. Stock delisted or suspended
4. Temporary Yahoo Finance API issue

**Solution**:

1. **Validation**:
   ```python
   if data.empty:
       # Try stale cache
       data = cache.get(key, allow_stale=True)
       if data is None or data.empty:
           raise ValueError(f"No data available for {symbol}")
   ```

2. **User Guidance**:
   - Verify symbol on NSE website: https://www.nseindia.com/
   - Check for correct suffix (`.NS` for NSE, `.BO` for BSE)
   - Try with pre-cached symbols first (RELIANCE.NS, TCS.NS)

---

### Issue #7: News Headlines Not Available

**Problem**:
- Sentiment agent fails if no news headlines found
- Some stocks have limited news coverage

**Solution**:

```python
# agents/sentiment_agent.py
def analyze(self, symbol, data):
    try:
        news = self.data_fetcher.get_news(symbol)
        if not news or len(news) == 0:
            return {
                "signal": "NEUTRAL",
                "confidence": 0.5,
                "reasoning": "No news headlines available"
            }
        # ... rest of analysis ...
    except Exception as e:
        return {
            "signal": "NEUTRAL",
            "confidence": 0.5,
            "reasoning": f"Sentiment analysis failed: {str(e)}"
        }
```

**Fallback Strategy**:
- Always return NEUTRAL signal
- Confidence set to 0.5 (neutral impact)
- Master Agent reduces sentiment weight accordingly

---

## 🛠️ Development Setup

### Local Development Environment

1. **Clone Repository**:
   ```bash
   git clone <repository_url>
   cd multi_agent_stock_platform
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv myenv
   
   # Windows
   myenv\Scripts\activate
   
   # Linux/Mac
   source myenv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify Installation**:
   ```bash
   python -m multi_agent_stock_platform.test_system
   ```
   Expected: 18/18 tests passing

5. **Initialize Cache**:
   ```bash
   python -m multi_agent_stock_platform.data.create_sample_cache
   ```

6. **Run Application**:
   ```bash
   # CLI
   python -m multi_agent_stock_platform.main RELIANCE.NS
   
   # Web UI
   python -m streamlit run multi_agent_stock_platform/ui/app.py
   ```

### Development Tools

**Recommended IDE**: VS Code with extensions:
- Python (Microsoft)
- Pylance (Microsoft)
- Python Debugger (Microsoft)
- SQLite Viewer (alexcvzz)

**Linting/Formatting** (optional):
```bash
pip install black flake8 mypy
black multi_agent_stock_platform/  # Format code
flake8 multi_agent_stock_platform/  # Lint code
mypy multi_agent_stock_platform/    # Type checking
```

**Git Configuration**:
```bash
# .gitignore already includes:
# - myenv/
# - __pycache__/
# - *.pyc
# - cache.sqlite3
# - results/
```

---

## 🧪 Testing

### Running Tests

**Full Test Suite**:
```bash
cd c:\Users\djana\masdemov1
multi_agent_stock_platform\myenv\Scripts\python.exe -m multi_agent_stock_platform.test_system
```

**Expected Output**:
```
============================================================
Multi-Agent Stock Analysis Platform - System Test
============================================================

1. DEPENDENCY TESTS
   ✓ All required packages installed

2. IMPORT TESTS (4 tests)
   ✓ Agent modules import correctly
   ✓ Coordination modules import correctly
   ✓ Data modules import correctly
   ✓ Utility modules import correctly

3. FUNCTIONALITY TESTS (7 tests)
   ✓ DataFetcher initializes correctly
   ✓ CacheManager operations work
   ✓ Agent initialization successful
   ✓ MasterAgent initializes correctly
   ✓ ResultStorage operations work
   ✓ Signal normalization functions work
   ✓ MarketRegimeDetector initializes correctly

4. INTEGRATION TESTS (1 test)
   ✓ End-to-end analysis workflow

5. FILE STRUCTURE TESTS (4 tests)
   ✓ Required directories exist
   ✓ Required files exist
   ✓ Cache file present
   ✓ Results directory writable

6. DOCUMENTATION TESTS (1 test)
   ✓ All documentation files exist

TEST SUMMARY
Total Tests: 18
Passed: 18
Failed: 0
Warnings: 0
Pass Rate: 100.0%

✓ ALL TESTS PASSED - SYSTEM IS PRODUCTION READY!
```

### Test Categories Explained

**1. Dependency Tests**:
- Verifies all packages from `requirements.txt` are installed
- Catches missing dependencies early
- Critical for production deployment

**2. Import Tests**:
- Tests that all modules can be imported without errors
- Validates Python path and module structure
- Detects syntax errors and circular imports

**3. Functionality Tests**:
- Tests individual components in isolation
- Validates core functionality without external dependencies
- Fast feedback for development

**4. Integration Tests**:
- Tests complete workflow from input to output
- Uses real (cached) data when available
- Validates component interaction

**5. File Structure Tests**:
- Verifies required directories and files exist
- Checks file permissions (write access)
- Ensures runtime environment is correct

**6. Documentation Tests**:
- Confirms all documentation files are present
- Helps maintain documentation quality

### Writing New Tests

**Template for New Test**:
```python
def test_new_feature(self):
    """Test description"""
    try:
        # Setup
        test_data = {...}
        
        # Execute
        result = some_function(test_data)
        
        # Verify
        assert result is not None, "Result should not be None"
        assert result['key'] == expected_value, "Value mismatch"
        
        # Report success
        return {"status": "PASS", "message": "Test successful"}
        
    except Exception as e:
        # Report failure
        return {"status": "FAIL", "error": str(e)}
```

**Add to SystemTester Class**:
```python
class SystemTester:
    def run_all_tests(self):
        # ... existing categories ...
        
        # Add new category
        self.print_section("7. NEW FEATURE TESTS")
        tests['new_feature'] = [
            self.test_new_feature()
        ]
```

---

## 🤝 Contributing Guidelines

### Code Style

**Follow PEP 8**:
- 4 spaces for indentation
- Max line length: 100 characters
- Snake_case for functions and variables
- PascalCase for classes

**Docstring Format**:
```python
def function_name(param1, param2):
    """
    Brief description of function.
    
    Longer description if needed, explaining the algorithm
    or business logic.
    
    Args:
        param1 (type): Description of param1
        param2 (type): Description of param2
    
    Returns:
        type: Description of return value
    
    Raises:
        ExceptionType: When this exception is raised
    
    Example:
        >>> result = function_name(val1, val2)
        >>> print(result)
        Expected output
    """
    # Implementation
    pass
```

### Adding New Agents

**Steps**:

1. **Create Agent File**:
   ```python
   # agents/new_agent.py
   from agents.base_agent import BaseAgent
   
   class NewAgent(BaseAgent):
       def __init__(self, data_fetcher):
           super().__init__(data_fetcher)
           self.name = "New Agent"
       
       def analyze(self, symbol, data):
           """
           Implement custom analysis logic
           """
           try:
               # Your analysis code
               signal = "BUY"  # or "SELL" or "HOLD"
               confidence = 0.75
               reasoning = "Because..."
               
               return {
                   "signal": signal,
                   "confidence": confidence,
                   "reasoning": reasoning
               }
           except Exception as e:
               # Fallback
               return {
                   "signal": "NEUTRAL",
                   "confidence": 0.5,
                   "reasoning": f"Analysis failed: {str(e)}"
               }
   ```

2. **Register in Master Agent**:
   ```python
   # coordination/master_agent.py
   from agents.new_agent import NewAgent
   
   class MasterAgent:
       def __init__(self, data_fetcher):
           # ... existing agents ...
           self.new_agent = NewAgent(data_fetcher)
       
       def analyze(self, symbol):
           # ... existing code ...
           agent_signals['new_agent'] = self.new_agent.analyze(symbol, data)
   ```

3. **Update Weights**:
   ```python
   def _adjust_weights_for_regime(self, regime):
       weights = {
           "technical": 1.0,
           "fundamental": 1.0,
           "sentiment": 1.0,
           "new_agent": 1.0  # Add default weight
       }
       # ... regime adjustments ...
   ```

4. **Add Tests**:
   ```python
   # test_system.py
   def test_new_agent_initialization(self):
       try:
           from agents.new_agent import NewAgent
           agent = NewAgent(self.data_fetcher)
           return {"status": "PASS"}
       except Exception as e:
           return {"status": "FAIL", "error": str(e)}
   ```

### Pull Request Process

1. **Fork and Branch**:
   ```bash
   git checkout -b feature/new-agent
   ```

2. **Make Changes**:
   - Write code
   - Add tests
   - Update documentation

3. **Run Tests**:
   ```bash
   python -m multi_agent_stock_platform.test_system
   ```
   Ensure 100% pass rate

4. **Commit**:
   ```bash
   git add .
   git commit -m "Add: New agent for XYZ analysis"
   ```

5. **Push and PR**:
   ```bash
   git push origin feature/new-agent
   ```
   Create pull request on GitHub

**PR Checklist**:
- [ ] All tests passing
- [ ] Code follows PEP 8
- [ ] Docstrings added
- [ ] README updated if needed
- [ ] No breaking changes (or documented)

---

## 📚 Additional Resources

### External Documentation

- **Yahoo Finance API**: https://github.com/ranaroussi/yfinance
- **Streamlit Docs**: https://docs.streamlit.io/
- **pandas Documentation**: https://pandas.pydata.org/docs/
- **Technical Analysis Library**: https://technical-analysis-library-in-python.readthedocs.io/
- **VADER Sentiment**: https://github.com/cjhutto/vaderSentiment

### Related Projects

- **QuantConnect**: https://www.quantconnect.com/ (Algorithmic trading)
- **Backtrader**: https://www.backtrader.com/ (Backtesting framework)
- **TA-Lib**: https://mrjbq7.github.io/ta-lib/ (Technical analysis C library)

---

## 📞 Support & Troubleshooting

### Getting Help

1. **Check README.md**: User-facing documentation with common issues
2. **Check this file**: Technical deep-dive and known issues
3. **Run test_system.py**: Diagnose system health
4. **Check logs**: Look for error messages in console output

### Reporting Issues

When reporting an issue, include:

1. **Environment**:
   - OS and version
   - Python version (`python --version`)
   - Package versions (`pip list`)

2. **Steps to Reproduce**:
   - Exact command run
   - Stock symbol used
   - Expected vs actual behavior

3. **Error Output**:
   - Full error traceback
   - Relevant log messages

4. **Context**:
   - Cache status (does cache.sqlite3 exist?)
   - Recent actions (was system working before?)
   - Any modifications made to code

---

## 🔐 Security Considerations

### Data Privacy

- **No user authentication**: Currently single-user system
- **No sensitive data storage**: All data is public market data
- **Local execution**: No data sent to external servers (except Yahoo Finance API)

### API Keys

- **Yahoo Finance**: No API key required (free tier)
- **Future enhancements**: If adding paid APIs, store keys in `.env` file (git-ignored)

### Production Deployment

- **HTTPS**: Use reverse proxy (nginx) for web UI in production
- **Rate Limiting**: Implement request throttling for public deployments
- **Input Validation**: Validate stock symbols to prevent injection attacks
- **Error Messages**: Don't expose internal paths in production errors

---

## 🗺️ Future Roadmap

### Planned Features

1. **Backtesting Framework**: Historical performance analysis
2. **Portfolio Management**: Track multiple stocks
3. **Alerting System**: Email/SMS notifications for signals
4. **Advanced Charting**: Interactive candlestick charts
5. **Machine Learning**: Train models on historical data
6. **Options Analysis**: Support for options strategies
7. **Real-time Streaming**: WebSocket for live updates
8. **API Server**: REST API for programmatic access

### Known Limitations

1. **No real-time data**: Relies on Yahoo Finance delayed data
2. **No order execution**: Analysis only, not trading platform
3. **Limited to Indian markets**: NSE/BSE focus (extensible)
4. **No portfolio tracking**: Single-stock analysis only
5. **No user management**: Single-user system

---

**Document Version**: 1.0.0  
**Last Updated**: December 24, 2025  
**Maintained By**: Development Team  
**Next Review Date**: March 24, 2026
