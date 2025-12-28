"""
Master Agent Coordination Module

This module implements the central coordination logic that combines outputs
from multiple specialized agents (Technical, Fundamental, Sentiment) into a
unified investment decision.

Key Features:
- Parallel agent execution for performance
- Regime-aware dynamic weight adjustment
- Cross-verification to detect conflicting signals
- Confidence-based weight modulation
- Comprehensive explanation generation
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, Iterable, List, Tuple

import numpy as np

from ..agents.base_agent import BaseAgent
from ..utils.logging_utils import get_logger


class MasterAgent:
    """
    Coordination engine that combines independent agent signals with regime-aware weights.
    
    The MasterAgent orchestrates multiple specialized agents and synthesizes their
    outputs into a single investment decision (BUY/SELL/HOLD) with confidence scores.
    
    Architecture:
    - Rule-based (no ML): Transparent, explainable, deterministic
    - Dynamic weighting: Adjusts based on market regime and agent confidence
    - Cross-verification: Dampens confidence of outlier agents
    - Parallel execution: Runs all agents concurrently for speed
    
    Attributes:
        agents: List of BaseAgent instances to coordinate
        alpha: Confidence adjustment factor (0-1). Higher values give more weight
               to high-confidence agents
        min_weight: Minimum weight assigned to any agent (prevents zero influence)
    """

    def __init__(self, agents: Iterable[BaseAgent], alpha: float = 0.5, min_weight: float = 0.1):
        """
        Initialize the Master Agent coordinator.
        
        Args:
            agents: Collection of agent instances to coordinate
            alpha: Confidence boost factor [0, 1]. Default 0.5 provides moderate adjustment
            min_weight: Minimum weight per agent to prevent complete exclusion. Default 0.1
        """
        self.agents = list(agents)
        self.alpha = alpha
        self.min_weight = min_weight
        self.logger = get_logger(__name__)
        self.logger.info(f"MasterAgent initialized with {len(self.agents)} agents")

    def _regime_base_weights(self, regime: str, agent_names: List[str]) -> Dict[str, float]:
        """
        Determine base weights for each agent based on market regime.
        
        Different market conditions favor different analysis approaches:
        - High Volatility: Technical signals more reliable (50%)
        - Bearish: Fundamentals matter more (45%)
        - Normal/Bullish: Balanced approach (40% each for tech/fundamental)
        
        Args:
            regime: Market regime classification
            agent_names: Names of agents to assign weights to
            
        Returns:
            Dictionary mapping agent name to base weight (normalized to sum=1)
        """
        # Default distribution across known agents
        defaults = {
            "TechnicalAgent": 0.4,
            "FundamentalAgent": 0.4,
            "SentimentAgent": 0.2,
        }
        if regime == "High Volatility":
            # In volatile markets, technical analysis is more responsive
            defaults = {
                "TechnicalAgent": 0.5,
                "FundamentalAgent": 0.3,
                "SentimentAgent": 0.2,
            }
        elif regime == "Bearish":
            # In downturns, fundamentals help identify survivors
            defaults = {
                "TechnicalAgent": 0.35,
                "FundamentalAgent": 0.45,
                "SentimentAgent": 0.2,
            }
        
        # Keep only for agents present; renormalize
        base = {name: defaults.get(name, 0.1) for name in agent_names}
        s = sum(base.values()) or 1.0
        normalized = {k: v / s for k, v in base.items()}
        
        self.logger.debug(f"Regime '{regime}' base weights: {normalized}")
        return normalized

    def _cross_verify(self, results: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Cross-verify agent outputs and dampen confidence of outliers.
        
        If an agent strongly contradicts the majority direction, its confidence
        (not signal) is reduced. This prevents a single agent from dominating
        when others disagree.
        
        Args:
            results: Dictionary of agent outputs with signals and confidences
            
        Returns:
            Adjusted results with confidence dampening applied to outliers
        """
        signals = {k: v.get("signal", 0.0) for k, v in results.items()}
        sig_values = list(signals.values())
        
        if not sig_values:
            return results
        
        avg = float(np.mean(sig_values))
        
        # If signals are neutral overall, no dampening needed
        if abs(avg) < 0.05:
            return results
        
        majority_sign = np.sign(avg)
        adjusted = {}
        dampened_agents = []
        
        for name, out in results.items():
            s = float(out.get("signal", 0.0))
            conf = float(out.get("confidence", 0.0))
            
            # Dampen confidence if agent strongly disagrees with majority
            if abs(s) >= 0.6 and np.sign(s) != majority_sign:
                conf *= 0.5  # 50% confidence reduction
                dampened_agents.append(name)
            
            adjusted[name] = {**out, "confidence": float(max(0.0, min(1.0, conf)))}
        
        if dampened_agents:
            self.logger.info(f"Cross-verification dampened: {', '.join(dampened_agents)}")
        
        return adjusted

    def decide(self, market_data: Dict[str, Any], regime_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute multi-agent analysis and produce final investment decision.
        
        Process:
        1. Run all agents in parallel
        2. Apply cross-verification to dampen outliers
        3. Compute regime-based base weights
        4. Adjust weights based on agent confidence
        5. Aggregate weighted signals into final score
        6. Map score to decision (BUY/SELL/HOLD)
        7. Generate comprehensive explanation
        
        Args:
            market_data: Complete market snapshot with price, fundamental, news data
            regime_info: Market regime classification and details
            
        Returns:
            Dictionary containing:
            - decision: 'BUY', 'SELL', or 'HOLD'
            - final_score: Weighted aggregate signal [-1, +1]
            - overall_confidence: Mean confidence across agents [0, 1]
            - weights: Final normalized weights per agent
            - agents: Individual agent outputs
            - explanation: Human-readable rationale
        """
        self.logger.info("Starting multi-agent decision process")
        
        # 1. Collect outputs in parallel for performance
        results: Dict[str, Dict[str, Any]] = {}
        with ThreadPoolExecutor(max_workers=len(self.agents) or 1) as ex:
            fut_to_name = {
                ex.submit(agent.analyze, market_data): agent.__class__.__name__ 
                for agent in self.agents
            }
            
            for fut in as_completed(fut_to_name):
                name = fut_to_name[fut]
                try:
                    results[name] = fut.result()
                    self.logger.debug(f"{name} completed: signal={results[name].get('signal')}")
                except Exception as e:
                    self.logger.warning(f"Agent {name} failed: {e}")
                    results[name] = {
                        "signal": 0.0, 
                        "confidence": 0.0, 
                        "label": "Error", 
                        "rationale": str(e)
                    }

        # 2. Cross verification
        results = self._cross_verify(results)

        # 3. Regime base weights
        regime = regime_info.get("regime", "Unknown") if isinstance(regime_info, dict) else str(regime_info)
        agent_names = list(results.keys())
        base_w = self._regime_base_weights(regime, agent_names)

        # 4. Confidence adjustment and min-weight enforcement
        adjusted_w = {}
        for name, bw in base_w.items():
            conf = float(results.get(name, {}).get("confidence", 0.0))
            # Boost weight for high-confidence agents
            w = bw * (1.0 + self.alpha * conf)
            adjusted_w[name] = max(self.min_weight, w)

        # 5. Normalize weights to sum to 1.0
        total_w = sum(adjusted_w.values()) or 1.0
        norm_w = {k: v / total_w for k, v in adjusted_w.items()}

        # 6. Aggregate final score (weighted sum of signals)
        final_score = 0.0
        contributions: List[Tuple[str, float]] = []
        for name, out in results.items():
            s = float(out.get("signal", 0.0))
            w = norm_w.get(name, 0.0)
            contrib = w * s
            contributions.append((name, contrib))
            final_score += contrib

        # 7. Decision mapping based on threshold rules
        if final_score >= 0.50:
            decision = "BUY"
        elif final_score <= -0.30:
            decision = "SELL"
        else:
            decision = "HOLD"

        # 8. Generate explanation
        dominant = sorted(contributions, key=lambda kv: abs(kv[1]), reverse=True)[:2]
        conflicting = [
            name
            for name, out in results.items()
            if np.sign(float(out.get("signal", 0.0))) != np.sign(final_score) 
            and abs(float(out.get("signal", 0.0))) > 0.2
        ]
        
        expl_parts = [
            f"Regime: {regime}.",
            "Dominant contributions: "
            + ", ".join(f"{n} {c:+.2f} (w={norm_w.get(n, 0):.2f})" for n, c in dominant)
            + ".",
        ]
        
        if conflicting:
            expl_parts.append("Conflicting signals from: " + ", ".join(conflicting) + ".")
        
        # Include brief rationales from each agent
        for name in agent_names:
            r = results.get(name, {}).get("rationale")
            if r:
                expl_parts.append(f"{name}: {r}")
        
        explanation = " ".join(expl_parts)

        # Overall confidence is mean of agent confidences
        overall_conf = float(
            np.mean([float(v.get("confidence", 0.0)) for v in results.values()]) 
            if results else 0.0
        )

        self.logger.info(
            f"Decision: {decision}, Score: {final_score:.2f}, Confidence: {overall_conf:.2%}"
        )

        return {
            "decision": decision,
            "final_score": round(float(final_score), 4),
            "overall_confidence": round(overall_conf, 4),
            "weights": norm_w,
            "agents": results,
            "explanation": explanation,
        }
