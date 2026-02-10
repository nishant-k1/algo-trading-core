"""Unit tests for gap filter."""
from datetime import datetime, timezone

import pytest

from app.engines.broker.base import Candle
from app.engines.strategy.gap_filter import apply_gap_filter, symbols_filtered_by_gap


def _candle(open_: float, close: float) -> Candle:
    return Candle(
        timestamp=datetime.now(timezone.utc),
        open=open_,
        high=max(open_, close),
        low=min(open_, close),
        close=close,
        volume=1000,
    )


def test_symbols_filtered_by_gap_empty() -> None:
    assert symbols_filtered_by_gap({}) == set()
    assert symbols_filtered_by_gap({"A": [_candle(100, 101)]}) == set()


def test_symbols_filtered_by_gap_under_threshold() -> None:
    # gap = |102 - 100|/100 = 2% -> not excluded at 2.0%
    data = {"A": [_candle(100, 100), _candle(102, 103)]}
    assert symbols_filtered_by_gap(data, max_gap_pct=2.0) == set()


def test_symbols_filtered_by_gap_over_threshold() -> None:
    # gap = |105 - 100|/100 = 5%
    data = {"A": [_candle(100, 100), _candle(105, 106)]}
    assert symbols_filtered_by_gap(data, max_gap_pct=2.0) == {"A"}
    assert symbols_filtered_by_gap(data, max_gap_pct=6.0) == set()


def test_symbols_filtered_by_gap_negative_prev_close_skipped() -> None:
    data = {"A": [_candle(0, 0), _candle(10, 11)]}
    assert symbols_filtered_by_gap(data) == set()


def test_apply_gap_filter() -> None:
    data = {
        "A": [_candle(100, 100), _candle(102, 103)],
        "B": [_candle(200, 200), _candle(210, 211)],  # 5% gap
    }
    out = apply_gap_filter(data, max_gap_pct=2.0)
    assert list(out.keys()) == ["A"]
    assert len(out["A"]) == 2
