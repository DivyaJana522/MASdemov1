from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from .base_agent import BaseAgent
from ..utils.logging_utils import get_logger
from ..utils.normalization import clip_signal


class SentimentAgent(BaseAgent):
    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self.analyzer = SentimentIntensityAnalyzer()

    def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze with input validation and error handling."""
        if not market_data:
            return self._neutral_response("Empty market data")
        
        news = market_data.get("news") or []
        if not news:
            return self._neutral_response("No news available")
        
        try:
            return self._compute_sentiment_signals(news)
        except Exception as e:
            self.logger.error("Sentiment analysis failed: %s", e)
            return self._neutral_response(f"Analysis error: {str(e)}")
    
    def _neutral_response(self, reason: str) -> Dict[str, Any]:
        """Return neutral signal with reason."""
        return {
            "signal": 0.0,
            "confidence": 0.0,
            "label": "Neutral",
            "rationale": reason,
        }
    
    def _compute_sentiment_signals(self, news: List[Dict[str, Any]]) -> Dict[str, Any]:

        scores: List[float] = []
        pos_ct = 0
        neg_ct = 0
        for item in news:
            text = (item.get("headline") or "") + ". " + (item.get("summary") or "")
            text = text.strip()
            if not text:
                continue
            vs = self.analyzer.polarity_scores(text)
            comp = float(vs.get("compound", 0.0))  # already in [-1,1]
            scores.append(comp)
            if comp >= 0.2:
                pos_ct += 1
            elif comp <= -0.2:
                neg_ct += 1

        if not scores:
            return {
                "signal": 0.0,
                "confidence": 0.1,
                "label": "Neutral",
                "rationale": "Insufficient textual content for sentiment scoring.",
            }

        avg = float(np.mean(scores))
        std = float(np.std(scores))
        n = len(scores)

        # Confidence: more items and tighter agreement => higher confidence
        volume_factor = min(1.0, n / 20.0)  # saturate at 20 headlines
        agreement = 1.0 - min(1.0, std)  # std in [0,1+] -> map to [0,1]
        confidence = 0.2 + 0.5 * volume_factor + 0.3 * agreement
        confidence = float(max(0.0, min(1.0, confidence)))

        label = "Positive" if avg > 0.15 else ("Negative" if avg < -0.15 else "Neutral")
        rationale = f"Sentiment avg={avg:+.2f}, n={n}, agreement={agreement:.2f}; Pos={pos_ct}, Neg={neg_ct}."

        return {
            "signal": clip_signal(avg),
            "confidence": confidence,
            "label": label,
            "rationale": rationale,
        }
