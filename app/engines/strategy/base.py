"""Strategy engine: abstract interface and types."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from app.engines.broker.base import Candle


@dataclass
class Signal:
    """Trading signal from a strategy."""

    exchange: str
    symbol: str
    side: str  # BUY | SELL
    reason: str
    score: float = 0.0
    meta: dict[str, Any] | None = None


@dataclass
class StrategyContext:
    """Input context for running a strategy."""

    exchange: str
    product: str  # MIS | CNC | NRML (from trading mode)
    symbols_candles: dict[str, list[Candle]]  # symbol -> sorted daily candles (oldest first)
    params: dict[str, Any]  # strategy-specific params


class Strategy(ABC):
    """Abstract strategy: given context, produce signals."""

    @abstractmethod
    def run(self, ctx: StrategyContext) -> list[Signal]:
        """Run strategy and return signals. Candles are daily, sorted oldest first."""
        ...
