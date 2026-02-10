"""Strategy registry: key -> Strategy instance."""

from app.engines.strategy.base import Strategy
from app.engines.strategy.strategies import GapUpOpenStrategy, PreviousHighBreakoutStrategy

REGISTRY: dict[str, type[Strategy]] = {
    "previous_high_breakout": PreviousHighBreakoutStrategy,
    "gap_up_open": GapUpOpenStrategy,
}


def get_strategy(key: str) -> Strategy | None:
    """Return strategy instance for key, or None if unknown."""
    cls = REGISTRY.get(key)
    return cls() if cls else None


def list_strategies() -> list[dict[str, str]]:
    """Return list of {key, name} for UI."""
    names = {
        "previous_high_breakout": "Previous high breakout",
        "gap_up_open": "Gap up open",
    }
    return [{"key": k, "name": names.get(k, k)} for k in REGISTRY]
