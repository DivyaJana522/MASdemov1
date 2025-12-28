"""
Multi-Agent Stock Analysis Platform - Command Line Interface

This module provides a CLI for running stock analysis using multiple AI agents.
Each agent specializes in different aspects: technical, fundamental, and sentiment analysis.

Usage:
    python -m multi_agent_stock_platform.main SYMBOL

Example:
    python -m multi_agent_stock_platform.main RELIANCE.NS
    python -m multi_agent_stock_platform.main TCS.NS
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from multi_agent_stock_platform.data.data_fetcher import DataFetcher
from multi_agent_stock_platform.agents.technical_agent import TechnicalAgent
from multi_agent_stock_platform.agents.fundamental_agent import FundamentalAgent
from multi_agent_stock_platform.agents.sentiment_agent import SentimentAgent
from multi_agent_stock_platform.coordination.market_regime import MarketRegimeDetector
from multi_agent_stock_platform.coordination.master_agent import MasterAgent
from multi_agent_stock_platform.utils.logging_utils import get_logger
from multi_agent_stock_platform.utils.result_storage import ResultStorage

logger = get_logger(__name__)


def main() -> None:
    """
    Main entry point for CLI analysis.
    
    Parses command line arguments, runs multi-agent analysis,
    and outputs results as JSON.
    """
    parser = argparse.ArgumentParser(
        description="Multi-Agent Stock Investment & Analysis Platform (India)",
        epilog="Example: python -m multi_agent_stock_platform.main RELIANCE.NS"
    )
    parser.add_argument(
        "symbol", 
        help="Stock ticker with exchange suffix (e.g., RELIANCE.NS for NSE, 500325.BO for BSE)"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save analysis result to results directory"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging output"
    )
    
    args = parser.parse_args()
    
    try:
        logger.info(f"Starting analysis for {args.symbol}")
        print(f"\n{'='*60}")
        print(f"Multi-Agent Stock Analysis: {args.symbol}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        # Fetch market data
        print("📊 Fetching market data...")
        fetcher = DataFetcher()
        snapshot = fetcher.build_snapshot(args.symbol)
        print("✓ Market data fetched successfully\n")
        
        # Initialize agents
        print("🤖 Initializing analysis agents...")
        agents = [TechnicalAgent(), FundamentalAgent(), SentimentAgent()]
        print(f"   • Technical Agent: Analyzing price patterns and indicators")
        print(f"   • Fundamental Agent: Evaluating financial metrics")
        print(f"   • Sentiment Agent: Assessing news and market sentiment")
        print("✓ Agents initialized\n")
        
        # Detect market regime
        print("🌐 Detecting market regime...")
        regime_detector = MarketRegimeDetector()
        regime_info = regime_detector.detect(snapshot)
        print(f"✓ Market Regime: {regime_info.get('regime', 'Unknown')}\n")
        
        # Run master agent coordination
        print("⚙️  Running master agent coordination...")
        master = MasterAgent(agents)
        decision = master.decide(snapshot, regime_info)
        decision["regime"] = regime_info
        print("✓ Analysis completed\n")
        
        # Display results
        print(f"{'='*60}")
        print("ANALYSIS RESULTS")
        print(f"{'='*60}")
        print(f"\n🎯 Decision: {decision.get('decision', 'N/A')}")
        print(f"📈 Final Score: {decision.get('final_score', 0):+.2f}")
        print(f"🎲 Confidence: {decision.get('overall_confidence', 0):.2%}")
        print(f"\n💡 Explanation:")
        print(f"   {decision.get('explanation', 'N/A')}\n")
        
        # Agent breakdown
        print(f"{'='*60}")
        print("AGENT BREAKDOWN")
        print(f"{'='*60}\n")
        agents_output = decision.get("agents", {})
        weights = decision.get("weights", {})
        
        for agent_name, agent_result in agents_output.items():
            print(f"🔹 {agent_name}")
            print(f"   Signal: {agent_result.get('signal', 0):+.2f}")
            print(f"   Confidence: {agent_result.get('confidence', 0):.2%}")
            print(f"   Weight: {weights.get(agent_name, 0):.2f}")
            print(f"   Label: {agent_result.get('label', 'N/A')}")
            print(f"   Rationale: {agent_result.get('rationale', 'N/A')}\n")
        
        # Save result if requested
        if args.save:
            try:
                storage = ResultStorage()
                saved_path = storage.save_result(args.symbol, decision)
                print(f"💾 Result saved to: {saved_path}\n")
            except Exception as e:
                logger.error(f"Failed to save result: {e}")
                print(f"⚠️  Warning: Could not save result to file\n")
        
        # Output full JSON for programmatic use
        if args.verbose:
            print(f"{'='*60}")
            print("FULL JSON OUTPUT")
            print(f"{'='*60}\n")
            print(json.dumps(decision, ensure_ascii=False, indent=2))
        
        print(f"{'='*60}")
        print("⚠️  DISCLAIMER: This is for informational purposes only.")
        print("   Not financial advice. Do your own research.")
        print(f"{'='*60}\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        print("Please check the logs for more details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
