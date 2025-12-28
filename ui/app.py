from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict

import pandas as pd
import streamlit as st

# Ensure the workspace root is on sys.path when Streamlit executes this file directly.
# This allows absolute imports like `multi_agent_stock_platform.*` to resolve reliably.
try:
    _here = os.path.dirname(os.path.abspath(__file__))
    _package_root = os.path.abspath(os.path.join(_here, ".."))
    _workspace_root = os.path.abspath(os.path.join(_package_root, ".."))
    if _workspace_root not in sys.path:
        sys.path.insert(0, _workspace_root)
except Exception:
    # Non-fatal: imports may still resolve depending on execution context
    pass

from multi_agent_stock_platform.data.data_fetcher import DataFetcher
from multi_agent_stock_platform.agents.technical_agent import TechnicalAgent
from multi_agent_stock_platform.agents.fundamental_agent import FundamentalAgent
from multi_agent_stock_platform.agents.sentiment_agent import SentimentAgent
from multi_agent_stock_platform.coordination.market_regime import MarketRegimeDetector
from multi_agent_stock_platform.coordination.master_agent import MasterAgent
from multi_agent_stock_platform.utils.logging_utils import get_logger
from multi_agent_stock_platform.utils.result_storage import ResultStorage


st.set_page_config(page_title="Multi-Agent Stock Analysis (India)", layout="wide")
logger = get_logger(__name__)
storage = ResultStorage()


@st.cache_resource(show_spinner=False)
def get_fetcher() -> DataFetcher:
    return DataFetcher()


def run_analysis(symbol: str) -> Dict[str, Any]:
    """
    Run complete multi-agent analysis for a given stock symbol.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE.NS')
    
    Returns:
        Complete analysis result with decision, confidence, and agent outputs
    """
    logger.info(f"Starting analysis for {symbol}")
    
    # Fetch market data
    fetcher = get_fetcher()
    snapshot = fetcher.build_snapshot(symbol)
    
    # Initialize agents and run analysis
    agents = [TechnicalAgent(), FundamentalAgent(), SentimentAgent()]
    regime_info = MarketRegimeDetector().detect(snapshot)
    master = MasterAgent(agents)
    decision = master.decide(snapshot, regime_info)
    decision["regime"] = regime_info
    
    # Save result to disk for audit trail
    try:
        saved_path = storage.save_result(symbol, decision)
        logger.info(f"Analysis result saved to: {saved_path}")
        decision["_saved_to"] = saved_path
    except Exception as e:
        logger.error(f"Failed to save result: {e}")
    
    return decision


st.title("Multi-Agent Stock Investment & Analysis (India)")
st.caption("Decision-support only. No trade execution. Educational prototype.")

with st.sidebar:
    symbol = st.text_input(
        "NSE/BSE Symbol (append .NS or .BO)", value="RELIANCE.NS", help="Example: RELIANCE.NS, TCS.NS, 500325.BO"
    )
    run = st.button("Analyze")

if run and symbol:
    with st.spinner("Fetching data and running agents..."):
        result = run_analysis(symbol.strip())

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        st.subheader("Decision")
        st.metric("Action", result.get("decision", "-"))
        st.metric("Confidence", f"{result.get('overall_confidence', 0):.2f}")
    with col2:
        st.subheader("Final Score")
        st.metric("Score", f"{result.get('final_score', 0):+.2f}")
        st.write("Regime:", result.get("regime", {}).get("regime", "Unknown"))
    with col3:
        st.subheader("Explanation")
        st.write(result.get("explanation", ""))
        if "_saved_to" in result:
            st.caption(f"✓ Result saved to: {result['_saved_to']}")

    st.divider()
    st.subheader("Agent Breakdown")
    agents_out = result.get("agents", {})
    weights = result.get("weights", {})
    for name, out in agents_out.items():
        with st.expander(f"{name}"):
            st.write(f"Label: {out.get('label')}")
            st.write(f"Signal: {out.get('signal', 0):+.2f}")
            st.write(f"Confidence: {out.get('confidence', 0):.2f}")
            st.write(f"Weight: {weights.get(name, 0):.2f}")
            st.caption(out.get("rationale", ""))

    st.divider()
    st.caption(
        "This tool is for information and education only. It does not execute trades and does not constitute financial advice."
    )
