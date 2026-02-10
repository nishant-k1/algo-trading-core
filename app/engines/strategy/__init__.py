"""Strategy engine: interface, gap filter, registry, run loop."""

from app.engines.strategy.base import Signal, Strategy, StrategyContext
from app.engines.strategy.gap_filter import apply_gap_filter, symbols_filtered_by_gap
from app.engines.strategy.registry import get_strategy, list_strategies

__all__ = [
    "Signal",
    "Strategy",
    "StrategyContext",
    "apply_gap_filter",
    "symbols_filtered_by_gap",
    "get_strategy",
    "list_strategies",
]
