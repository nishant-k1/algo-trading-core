"""Unit tests for strategy registry and previous_high_breakout."""
from datetime import datetime, timezone

import pytest

from app.engines.broker.base import Candle
from app.engines.strategy import get_strategy, list_strategies
from app.engines.strategy.base import StrategyContext


def test_list_strategies() -> None:
    strategies = list_strategies()
    assert len(strategies) >= 1
    assert any(s["key"] == "previous_high_breakout" for s in strategies)
    assert any("breakout" in s["name"].lower() for s in strategies)


def test_get_strategy_known() -> None:
    s = get_strategy("previous_high_breakout")
    assert s is not None


def test_get_strategy_unknown() -> None:
    assert get_strategy("unknown_key") is None


def test_previous_high_breakout_no_signal() -> None:
    strategy = get_strategy("previous_high_breakout")
    assert strategy is not None
    ctx = StrategyContext(
        exchange="NSE",
        product="CNC",
        symbols_candles={
            "A": [
                Candle(datetime.now(timezone.utc), 100, 105, 99, 104, 1e6),
                Candle(datetime.now(timezone.utc), 104, 105, 103, 104, 1e6),  # close not > 105
            ]
        },
        params={},
    )
    signals = strategy.run(ctx)
    assert len(signals) == 0


def test_previous_high_breakout_signal() -> None:
    strategy = get_strategy("previous_high_breakout")
    assert strategy is not None
    ctx = StrategyContext(
        exchange="NSE",
        product="CNC",
        symbols_candles={
            "A": [
                Candle(datetime.now(timezone.utc), 100, 105, 99, 104, 1e6),
                Candle(datetime.now(timezone.utc), 104, 106, 103, 106, 1e6),  # close 106 > prev_high 105
            ]
        },
        params={},
    )
    signals = strategy.run(ctx)
    assert len(signals) == 1
    assert signals[0].symbol == "A"
    assert signals[0].side == "BUY"
    assert signals[0].reason == "close_above_previous_high"
