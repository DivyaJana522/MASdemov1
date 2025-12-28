# Multi-Agent Stock Analysis Platform

[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![Production Ready](https://img.shields.io/badge/status-production%20ready-brightgreen.svg)]()
[![Test Coverage](https://img.shields.io/badge/tests-18%2F18%20passing-success.svg)]()

A sophisticated, production-ready stock analysis platform for Indian equity markets (NSE/BSE) using multiple specialized AI agents with intelligent coordination and market regime adaptation.

---

## 📑 Table of Contents

- [Quick Start](#-quick-start)
- [Features](#-features)
- [Usage](#-usage)
- [Architecture](#-architecture)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)
- [Production Deployment](#-production-deployment)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.14+ installed
- Windows OS (tested on Windows 10/11)
- Virtual environment already set up at `myenv/`

### Running the Platform

**Option 1: Web Interface (Recommended)**
```bash
# Navigate to project root
cd c:\Users\djana\masdemov1

# Start Streamlit UI
multi_agent_stock_platform\myenv\Scripts\python.exe -m streamlit run multi_agent_stock_platform/ui/app.py
```
Access at: `http://localhost:8501`

**Option 2: Command Line**
```bash
# Navigate to project root
cd c:\Users\djana\masdemov1

# Basic analysis
multi_agent_stock_platform\myenv\Scripts\python.exe -m multi_agent_stock_platform.main RELIANCE.NS

# Save results to file
multi_agent_stock_platform\myenv\Scripts\python.exe -m multi_agent_stock_platform.main RELIANCE.NS --save

# Verbose JSON output
multi_agent_stock_platform\myenv\Scripts\python.exe -m multi_agent_stock_platform.main RELIANCE.NS --save --verbose
```

**Option 3: Python API**
```python
from multi_agent_stock_platform.coordination.master_agent import MasterAgent
from multi_agent_stock_platform.data.data_fetcher import DataFetcher

# Initialize
fetcher = DataFetcher()
master = MasterAgent(fetcher)

# Analyze stock
result = master.analyze("RELIANCE.NS")
print(f"Decision: {result['decision']}")
print(f"Confidence: {result['confidence']}")
```

### Supported Stocks
Indian NSE/BSE stocks with `.NS` suffix:
- `RELIANCE.NS`, `BHARTIARTL.NS`, `TCS.NS`, `INFY.NS`
- `HDFCBANK.NS`, `ICICIBANK.NS`, `SBIN.NS`, `ITC.NS`
- Any valid NSE stock symbol

---

## 🌟 Features

### Core Capabilities
- ✅ **Multi-Agent Analysis**: Three specialized agents (Technical, Fundamental, Sentiment)
- ✅ **Market Regime Detection**: Automatically adapts to market conditions
- ✅ **Intelligent Coordination**: Dynamic weighting and cross-verification
- ✅ **Result Persistence**: Timestamped JSON files with audit trail
- ✅ **Smart Caching**: SQLite-based with TTL and stale fallback
- ✅ **Rate Limit Protection**: Graceful degradation when API limits hit
- ✅ **Production-Grade Error Handling**: Try-catch blocks throughout
- ✅ **Comprehensive Testing**: 18 automated tests (100% pass rate)

### Technical Features
- **Caching System**: 2-hour TTL for prices, 48-hour for fundamentals
- **Stale Cache Fallback**: Uses expired cache when API unavailable
- **Parallel Agent Execution**: Faster analysis with concurrent processing
- **Confidence Scoring**: Regime-aware confidence adjustment
- **Progress Indicators**: Real-time feedback in CLI
- **Color-Coded Output**: Easy-to-read terminal output

---

## 💻 Usage

### Web Interface

1. **Start the app**:
   ```bash
   cd c:\Users\djana\masdemov1
   multi_agent_stock_platform\myenv\Scripts\python.exe -m streamlit run multi_agent_stock_platform/ui/app.py
   ```

2. **Analyze a stock**:
   - Enter stock symbol (e.g., `RELIANCE.NS`)
   - Click "Analyze Stock"
   - View comprehensive results with agent breakdowns

3. **Features**:
   - Market regime indicator
   - Individual agent signals and reasoning
   - Overall recommendation with confidence
   - Historical price chart
   - Results automatically saved to `results/` directory

### Command Line Interface

**Basic Usage**:
```bash
cd c:\Users\djana\masdemov1
multi_agent_stock_platform\myenv\Scripts\python.exe -m multi_agent_stock_platform.main SYMBOL
```

**Options**:
- `--save`: Save results to `results/SYMBOL_YYYYMMDD_HHMMSS.json`
- `--verbose`: Output full JSON result to console
- `-h, --help`: Show help message

**Examples**:
```bash
# Quick analysis
multi_agent_stock_platform\myenv\Scripts\python.exe -m multi_agent_stock_platform.main TCS.NS

# Save with verbose output
multi_agent_stock_platform\myenv\Scripts\python.exe -m multi_agent_stock_platform.main INFY.NS --save --verbose

# Analyze multiple stocks (manual loop)
for %s in (RELIANCE.NS TCS.NS INFY.NS) do multi_agent_stock_platform\myenv\Scripts\python.exe -m multi_agent_stock_platform.main %s --save
```

### Python API

**Direct Integration**:
```python
from multi_agent_stock_platform.coordination.master_agent import MasterAgent
from multi_agent_stock_platform.data.data_fetcher import DataFetcher

# Initialize components
data_fetcher = DataFetcher()
master_agent = MasterAgent(data_fetcher)

# Analyze stock
result = master_agent.analyze("RELIANCE.NS")

# Access results
print(f"Decision: {result['decision']}")  # BUY/SELL/HOLD
print(f"Confidence: {result['confidence']:.2f}")
print(f"Market Regime: {result['market_regime']}")

# Agent-specific signals
for agent_name, agent_data in result['agent_signals'].items():
    print(f"{agent_name}: {agent_data['signal']} ({agent_data['reasoning']})")
```

**Result Storage**:
```python
from multi_agent_stock_platform.utils.result_storage import ResultStorage

storage = ResultStorage()

# Save analysis result
file_path = storage.save_result("RELIANCE.NS", result)
print(f"Saved to: {file_path}")

# Load latest result
latest = storage.get_latest_result("RELIANCE.NS")

# List all results for a symbol
all_results = storage.list_results("RELIANCE.NS")

# Cleanup old results (keep last 30 days)
storage.cleanup_old_results(days=30)
```

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interfaces                         │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Streamlit  │  │  CLI (main)  │  │  Python API  │      │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼─────────────────┼──────────────────┼──────────────┘
          │                 │                  │
          └─────────────────┴──────────────────┘
                           │
          ┌────────────────▼────────────────┐
          │      Master Agent               │
          │  (Coordination Layer)           │
          │  - Market Regime Detection      │
          │  - Dynamic Weighting            │
          │  - Cross-verification           │
          │  - Confidence Adjustment        │
          └────────────────┬────────────────┘
                           │
          ┌────────────────┴────────────────┐
          │                                  │
    ┌─────▼─────┐  ┌─────▼─────┐  ┌────▼────┐
    │ Technical │  │Fundamental│  │Sentiment│
    │   Agent   │  │   Agent   │  │  Agent  │
    └─────┬─────┘  └─────┬─────┘  └────┬────┘
          │              │              │
          └──────────────┴──────────────┘
                       │
          ┌────────────▼────────────┐
          │     Data Layer          │
          │  - DataFetcher          │
          │  - CacheManager         │
          │  - Yahoo Finance API    │
          └─────────────────────────┘
```

### Component Breakdown

**1. Master Agent** (`coordination/master_agent.py`)
- Orchestrates all specialist agents
- Detects market regime (Bullish/Bearish/High Volatility)
- Applies dynamic weighting based on regime
- Cross-verifies agent signals
- Adjusts confidence scores
- Returns unified decision

**2. Technical Agent** (`agents/technical_agent.py`)
- **Indicators**: RSI, MACD, Bollinger Bands, Moving Averages (SMA50, SMA200)
- **Signal Logic**: Trend-based with momentum confirmation
- **Output**: BUY/SELL/HOLD with confidence and reasoning

**3. Fundamental Agent** (`agents/fundamental_agent.py`)
- **Metrics**: P/E ratio, P/B ratio, ROE, Revenue/Profit growth
- **Signal Logic**: Value-based with growth consideration
- **Output**: BUY/SELL/HOLD with confidence and reasoning

**4. Sentiment Agent** (`agents/sentiment_agent.py`)
- **Analysis**: VADER sentiment on news headlines
- **Signal Logic**: Sentiment polarity thresholds
- **Output**: POSITIVE/NEGATIVE/NEUTRAL with confidence

**5. Data Layer** (`data/`)
- **DataFetcher**: Retrieves market data from Yahoo Finance
- **CacheManager**: SQLite-based caching with TTL (2hr prices, 48hr fundamentals)
- **Stale Fallback**: Uses expired cache when API rate limited

**6. Utilities** (`utils/`)
- **ResultStorage**: Timestamped JSON file management
- **Logging**: Structured logging throughout
- **Normalization**: Signal standardization

---

## ⚙️ Configuration

### Cache Settings

Edit `data/data_fetcher.py` to adjust cache TTL:
```python
# Current settings
PRICE_CACHE_TTL = 7200  # 2 hours
FUNDAMENTAL_CACHE_TTL = 172800  # 48 hours
```

### Market Regime Thresholds

Edit `coordination/market_regime.py`:
```python
# Volatility thresholds
if volatility > 0.03:  # 3% threshold
    regime = "HIGH_VOLATILITY"
```

### Agent Weights

Edit `coordination/master_agent.py`:
```python
# Default weights (equal)
weights = {"technical": 1.0, "fundamental": 1.0, "sentiment": 1.0}

# Regime-specific adjustments
if regime == "BULLISH":
    weights["technical"] *= 1.2  # Favor technical in bullish markets
```

---

## 🔧 Troubleshooting

### Common Issues

**1. Yahoo Finance Rate Limiting**
- **Symptom**: "Too Many Requests" error or 429 status
- **Solution**: System automatically uses stale cache fallback
- **Prevention**: Pre-populate cache with `create_sample_cache.py`

**2. PowerShell Execution Policy**
- **Symptom**: Script execution blocked
- **Solution**: Use full Python path:
  ```bash
  multi_agent_stock_platform\myenv\Scripts\python.exe -m streamlit run multi_agent_stock_platform/ui/app.py
  ```

**3. Missing Dependencies**
- **Symptom**: Import errors
- **Solution**: 
  ```bash
  cd c:\Users\djana\masdemov1
  multi_agent_stock_platform\myenv\Scripts\pip.exe install -r multi_agent_stock_platform/requirements.txt
  ```

**4. Cache Locked (Windows)**
- **Symptom**: "Database is locked" error
- **Solution**: Close all other processes using the cache, or restart

**5. No Data for Stock Symbol**
- **Symptom**: "Unable to fetch data"
- **Solution**: 
  - Verify symbol format (must end with `.NS` for NSE)
  - Check if stock is actively traded
  - Try with pre-cached symbols (RELIANCE.NS, TCS.NS)

### Debugging Commands

**Test System**:
```bash
cd c:\Users\djana\masdemov1
multi_agent_stock_platform\myenv\Scripts\python.exe -m multi_agent_stock_platform.test_system
```

**Check Cache Status**:
```bash
cd c:\Users\djana\masdemov1
multi_agent_stock_platform\myenv\Scripts\python.exe -c "from multi_agent_stock_platform.data.cache_manager import CacheManager; cm = CacheManager(); print('Cache file exists:', cm.db_path)"
```

**Warm Cache for Popular Stocks**:
```bash
cd c:\Users\djana\masdemov1
multi_agent_stock_platform\myenv\Scripts\python.exe -m multi_agent_stock_platform.data.warm_cache
```

---

## 🚀 Production Deployment

### System Requirements
- **Python**: 3.14+ (tested with 3.14)
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 500MB for code + cache
- **OS**: Windows 10/11, Linux (Ubuntu 20.04+), macOS 11+

### Pre-Production Checklist

✅ **All Tests Passing**: Run `test_system.py` (18/18 tests must pass)  
✅ **Cache Initialized**: Run `create_sample_cache.py`  
✅ **Error Handling**: Try-catch blocks throughout  
✅ **Logging**: Structured logging enabled  
✅ **Rate Limit Protection**: Stale cache fallback active  
✅ **Result Storage**: Audit trail with timestamps  
✅ **Documentation**: This README + DEVELOPER_GUIDE.md  

### Deployment Steps

1. **Clone Repository**:
   ```bash
   git clone <repository_url>
   cd multi_agent_stock_platform
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv myenv
   myenv\Scripts\activate  # Windows
   source myenv/bin/activate  # Linux/Mac
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize Cache**:
   ```bash
   python -m multi_agent_stock_platform.data.create_sample_cache
   ```

5. **Run Tests**:
   ```bash
   python -m multi_agent_stock_platform.test_system
   ```
   Verify: 18/18 tests passing

6. **Start Application**:
   ```bash
   # Web UI
   python -m streamlit run multi_agent_stock_platform/ui/app.py --server.port 8501

   # Or CLI
   python -m multi_agent_stock_platform.main RELIANCE.NS
   ```

### Docker Deployment (Optional)

```dockerfile
FROM python:3.14-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt
RUN python -m multi_agent_stock_platform.data.create_sample_cache

EXPOSE 8501

CMD ["python", "-m", "streamlit", "run", "multi_agent_stock_platform/ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Monitoring & Maintenance

**Regular Tasks**:
- Check cache size weekly: `data/cache.sqlite3`
- Cleanup old results monthly: `ResultStorage.cleanup_old_results(30)`
- Monitor rate limiting patterns
- Update dependencies quarterly

**Health Check**:
```bash
python -m multi_agent_stock_platform.health_check
```

---

## 📊 Project Statistics

- **Total Files**: 22 Python modules
- **Lines of Code**: ~3,000+
- **Test Coverage**: 18 automated tests (100% pass rate)
- **Documentation**: 2 comprehensive guides (README.md, DEVELOPER_GUIDE.md)
- **Dependencies**: 20+ packages (pandas, numpy, yfinance, streamlit, etc.)

---

## 📝 License & Contact

**Project**: Multi-Agent Stock Analysis Platform  
**Version**: 1.0.0 (Production Ready)  
**Last Updated**: December 24, 2025  
**Python Version**: 3.14+  

For technical details, see [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)

---

**⚠️ Disclaimer**: This tool is for educational and research purposes only. Not financial advice. Always conduct your own research before making investment decisions.

### Python API

```python
from multi_agent_stock_platform.data.data_fetcher import DataFetcher
from multi_agent_stock_platform.agents.technical_agent import TechnicalAgent
from multi_agent_stock_platform.agents.fundamental_agent import FundamentalAgent
from multi_agent_stock_platform.agents.sentiment_agent import SentimentAgent
from multi_agent_stock_platform.coordination.master_agent import MasterAgent
from multi_agent_stock_platform.coordination.market_regime import MarketRegimeDetector

# Fetch data
fetcher = DataFetcher()
snapshot = fetcher.build_snapshot("RELIANCE.NS")

# Run analysis
agents = [TechnicalAgent(), FundamentalAgent(), SentimentAgent()]
regime = MarketRegimeDetector().detect(snapshot)
master = MasterAgent(agents)
decision = master.decide(snapshot, regime)

print(f"Decision: {decision['decision']}")
print(f"Confidence: {decision['overall_confidence']:.2%}")
print(f"Score: {decision['final_score']:+.2f}")
```

## 📊 Supported Stocks

### Pre-cached Stocks (Ready to Use)
- `RELIANCE.NS` - Reliance Industries
- `BHARTIARTL.NS` - Bharti Airtel  
- `TCS.NS` - Tata Consultancy Services
- `INFY.NS` - Infosys
- `HDFCBANK.NS` - HDFC Bank
- `ICICIBANK.NS` - ICICI Bank

### Symbol Format
- **NSE**: Add `.NS` suffix (e.g., `WIPRO.NS`)
- **BSE**: Add `.BO` suffix (e.g., `500325.BO`)

## 🏗️ Architecture

```
Market Data (Prices, Fundamentals, News)
          ↓
    Data Fetcher (with Cache)
          ↓
    ┌─────┴─────┬─────────┐
    ↓           ↓         ↓
Technical   Fundamental  Sentiment
  Agent       Agent       Agent
    │           │         │
    └─────┬─────┴─────────┘
          ↓
     Master Agent
  (Regime-Aware Coordination)
          ↓
   Final Decision (BUY/SELL/HOLD)
```

### Components

#### 1. **Data Layer** (`data/`)
- **DataFetcher**: Retrieves market data with intelligent caching
- **CacheManager**: SQLite-based with stale fallback for resilience
- **Utilities**: Cache warming, sample data generation

#### 2. **Agent Layer** (`agents/`)
- **TechnicalAgent**: RSI, MACD, Bollinger Bands, Moving Averages
- **FundamentalAgent**: P/E, P/B, ROE, Debt/Equity, Growth metrics
- **SentimentAgent**: News sentiment using VADER

#### 3. **Coordination Layer** (`coordination/`)
- **MasterAgent**: Orchestrates agents with dynamic weighting
- **MarketRegimeDetector**: Classifies market conditions

#### 4. **Utilities** (`utils/`)
- **Logging**: Structured logging system
- **ResultStorage**: Saves analysis with timestamps for audit trail
- **Normalization**: Signal processing utilities

## 📖 Understanding Results

### Decision Types
- **BUY**: Strong positive signal (score ≥ 0.50)
- **HOLD**: Neutral signal (-0.30 < score < 0.50)
- **SELL**: Strong negative signal (score ≤ -0.30)

### Confidence Score (0.0 - 1.0)
- **High (>0.7)**: Strong agent agreement
- **Medium (0.4-0.7)**: Moderate confidence
- **Low (<0.4)**: Conflicting signals

### Agent Signals (-1.0 to +1.0)
- **Positive**: Bullish indicators
- **Negative**: Bearish indicators  
- **Near Zero**: Neutral outlook

## ⚙️ Configuration

### Cache Settings

```python
# Adjust in data/data_fetcher.py
DataFetcher(
    cache_ttl_seconds=7200,  # 2 hours (default)
    index_ticker="^NSEI"      # NIFTY 50 index
)
```

### Agent Weights

Modify regime-based weights in `coordination/master_agent.py`:

```python
# Normal conditions
"TechnicalAgent": 0.4,
"FundamentalAgent": 0.4,
"SentimentAgent": 0.2

# High Volatility
"TechnicalAgent": 0.5,  # Increase technical weight
"FundamentalAgent": 0.3,
"SentimentAgent": 0.2

# Bearish Markets
"TechnicalAgent": 0.35,
"FundamentalAgent": 0.45,  # Increase fundamental weight
"SentimentAgent": 0.2
```

### Decision Thresholds

```python
# Adjust in coordination/master_agent.py
if final_score >= 0.50:  # BUY threshold
    decision = "BUY"
elif final_score <= -0.30:  # SELL threshold
    decision = "SELL"
else:
    decision = "HOLD"
```

## 🔧 Troubleshooting

### Rate Limiting (Yahoo Finance)

**Problem**: "Too Many Requests" error

**Solutions**:
```bash
# Use sample cache (instant)
python -m multi_agent_stock_platform.data.create_sample_cache

# Wait 30 minutes, then warm cache
python -m multi_agent_stock_platform.data.warm_cache RELIANCE.NS
```

The system automatically falls back to stale cache when rate limited.

### No Data Available

**Check**:
1. Symbol format (needs `.NS` or `.BO`)
2. Internet connection
3. Use sample cache for testing

### Cache Issues

```bash
# Clear and rebuild cache
rm data/cache.sqlite3
python -m multi_agent_stock_platform.data.create_sample_cache
```

## 📁 Project Structure

```
multi_agent_stock_platform/
├── agents/              # Specialized analysis agents
│   ├── base_agent.py
│   ├── technical_agent.py
│   ├── fundamental_agent.py
│   └── sentiment_agent.py
├── coordination/        # Master coordination logic
│   ├── master_agent.py
│   └── market_regime.py
├── data/               # Data fetching and caching
│   ├── data_fetcher.py
│   ├── cache_manager.py
│   ├── warm_cache.py
│   └── create_sample_cache.py
├── ui/                 # Streamlit web interface
│   └── app.py
├── utils/              # Utilities
│   ├── logging_utils.py
│   ├── normalization.py
│   └── result_storage.py
├── results/            # Saved analysis results
├── main.py            # CLI entry point
├── health_check.py    # System health monitoring
└── requirements.txt
```

## 📚 Documentation

- **[RATE_LIMIT_FIX.md](RATE_LIMIT_FIX.md)**: Rate limiting solutions
- **[data/CACHE_GUIDE.md](data/CACHE_GUIDE.md)**: Cache management guide
- **[results/README.md](results/README.md)**: Result storage documentation
- **[PRODUCTION_GUIDE.md](PRODUCTION_GUIDE.md)**: Production deployment

## 🚀 Production Deployment

### Health Checks

```bash
python -m multi_agent_stock_platform.health_check
```

### Scheduled Cache Warming

Schedule daily cache refresh at 6 AM IST:

```bash
# Windows Task Scheduler or Linux cron
0 6 * * * cd /path/to/project && python -m multi_agent_stock_platform.data.warm_cache
```

### Monitoring

Key metrics to track:
- Cache hit rate
- Agent execution times  
- API rate limit warnings
- Decision confidence scores

Results are automatically saved to `results/` directory with timestamps.

### Best Practices

1. **Cache First**: Pre-warm cache during off-peak hours
2. **Monitor Limits**: Track Yahoo Finance rate limits
3. **Store Results**: Enable result storage for audit trail
4. **Regular Cleanup**: Remove old cache/results periodically
5. **Structured Logging**: Use logs for debugging and monitoring

## ⚠️ Disclaimer

**IMPORTANT**: This platform is for **informational and educational purposes only**.

- ❌ **NOT financial advice**
- ❌ **No guarantee of accuracy**
- ❌ **Not a trading bot** (does not execute trades)
- ✅ **Decision support tool**
- ✅ **Educational resource**

**Always**:
- Conduct your own research
- Consult qualified financial advisors
- Understand investment risks
- Never invest more than you can afford to lose

The authors are not responsible for any financial losses.

## 📄 License

MIT License - See LICENSE file for details.

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 🙏 Acknowledgments

- **yfinance**: Yahoo Finance API
- **TA-Lib / ta**: Technical analysis
- **VADER**: Sentiment analysis
- **Streamlit**: Web framework
- **pandas/numpy**: Data processing

## 📈 Roadmap

- [ ] Add more technical indicators
- [ ] Integrate additional data sources  
- [ ] ML-based ensemble methods
- [ ] Real-time streaming analysis
- [ ] Portfolio optimization
- [ ] Backtesting framework
- [ ] Mobile app

---

**Made with ❤️ for Indian stock market analysis**

For support and questions, create an issue on GitHub.
