"""Gap filter: exclude symbols with open gap beyond threshold."""

from app.engines.broker.base import Candle


def symbols_filtered_by_gap(
    symbols_candles: dict[str, list[Candle]],
    max_gap_pct: float = 2.0,
) -> set[str]:
    """
    Return set of symbols to exclude: |open - prev_close| / prev_close > max_gap_pct.
    Needs at least 2 candles per symbol; otherwise symbol is not excluded.
    """
    excluded: set[str] = set()
    for symbol, candles in symbols_candles.items():
        if len(candles) < 2:
            continue
        prev_close = candles[-2].close
        today_open = candles[-1].open
        if prev_close <= 0:
            continue
        gap_pct = abs(today_open - prev_close) / prev_close * 100.0
        if gap_pct > max_gap_pct:
            excluded.add(symbol)
    return excluded


def apply_gap_filter(
    symbols_candles: dict[str, list[Candle]],
    max_gap_pct: float = 2.0,
) -> dict[str, list[Candle]]:
    """Return subset of symbols_candles with gap-filtered symbols removed."""
    excluded = symbols_filtered_by_gap(symbols_candles, max_gap_pct)
    return {s: c for s, c in symbols_candles.items() if s not in excluded}
