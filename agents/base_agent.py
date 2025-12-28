from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAgent(ABC):
    @abstractmethod
    def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze provided market snapshot and return an explainable decision signal.

        Must return a dict with keys:
        {
            "signal": float,     # normalized in [-1, +1]
            "confidence": float, # [0, 1]
            "label": str,
            "rationale": str
        }
        """
        raise NotImplementedError
