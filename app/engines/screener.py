"""Screener engine: gainers, losers, volume shockers, demand/supply zones."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from app.engines.broker.base import BrokerGateway, Candle
from app.engines.market_data import MarketDataService

if TYPE_CHECKING:
    pass

# Default NSE symbols when none provided (subset for demo; expand via config later)
DEFAULT_UNIVERSE_NSE = [
    "RELIANCE",
    "TCS",
    "HDFCBANK",
    "INFY",
    "ICICIBANK",
    "SBIN",
    "BHARTIARTL",
    "ITC",
    "KOTAKBANK",
    "LT",
    "AXISBANK",
    "ASIANPAINT",
    "MARUTI",
    "HINDUNILVR",
    "WIPRO",
    "SUNPHARMA",
    "BAJFINANCE",
    "TITAN",
    "ULTRACEMCO",
    "NESTLEIND",
]


@dataclass
class ScanResultRow:
    """Single row from a screener scan."""

    exchange: str
    symbol: str
    value: float
    extra: dict[str, float | str] | None = None


def _fetch_daily_candles(
    market_data: MarketDataService,
    exchange: str,
    symbols: list[str],
    days_back: int = 25,
) -> dict[str, list[Candle]]:
    """Fetch last N days of daily candles for each symbol."""
    to_d = datetime.now(timezone.utc)
    from_d = to_d - timedelta(days=days_back)
    result: dict[str, list[Candle]] = {}
    for symbol in symbols:
        try:
            candles = market_data.get_historical_candles(
                exchange=exchange,
                symbol=symbol,
                interval="day",
                from_date=from_d,
                to_date=to_d,
            )
            if candles:
                result[symbol] = candles
        except Exception:
            continue
    return result


def run_gainers(
    gateway: BrokerGateway,
    exchange: str = "NSE",
    symbols: list[str] | None = None,
    limit: int = 20,
) -> list[ScanResultRow]:
    """Top gainers by % change (last close vs previous close)."""
    symbols = symbols or DEFAULT_UNIVERSE_NSE
    market_data = MarketDataService(gateway)
    data = _fetch_daily_candles(market_data, exchange, symbols, days_back=10)
    rows: list[ScanResultRow] = []
    for symbol, candles in data.items():
        if len(candles) < 2:
            continue
        prev_close = candles[-2].close
        last_close = candles[-1].close
        if prev_close <= 0:
            continue
        pct = ((last_close - prev_close) / prev_close) * 100
        rows.append(
            ScanResultRow(
                exchange=exchange,
                symbol=symbol,
                value=round(pct, 2),
                extra={"close": last_close, "prev_close": prev_close},
            )
        )
    rows.sort(key=lambda r: r.value, reverse=True)
    return rows[:limit]


def run_losers(
    gateway: BrokerGateway,
    exchange: str = "NSE",
    symbols: list[str] | None = None,
    limit: int = 20,
) -> list[ScanResultRow]:
    """Top losers by % change."""
    symbols = symbols or DEFAULT_UNIVERSE_NSE
    market_data = MarketDataService(gateway)
    data = _fetch_daily_candles(market_data, exchange, symbols, days_back=10)
    rows: list[ScanResultRow] = []
    for symbol, candles in data.items():
        if len(candles) < 2:
            continue
        prev_close = candles[-2].close
        last_close = candles[-1].close
        if prev_close <= 0:
            continue
        pct = ((last_close - prev_close) / prev_close) * 100
        rows.append(
            ScanResultRow(
                exchange=exchange,
                symbol=symbol,
                value=round(pct, 2),
                extra={"close": last_close, "prev_close": prev_close},
            )
        )
    rows.sort(key=lambda r: r.value)
    return rows[:limit]


def run_volume_shockers(
    gateway: BrokerGateway,
    exchange: str = "NSE",
    symbols: list[str] | None = None,
    limit: int = 20,
    avg_days: int = 20,
) -> list[ScanResultRow]:
    """Symbols with volume > avg volume (ratio)."""
    symbols = symbols or DEFAULT_UNIVERSE_NSE
    market_data = MarketDataService(gateway)
    data = _fetch_daily_candles(market_data, exchange, symbols, days_back=avg_days + 5)
    rows: list[ScanResultRow] = []
    for symbol, candles in data.items():
        if len(candles) < avg_days + 1:
            continue
        recent = candles[-(avg_days + 1) :]
        last_vol = recent[-1].volume
        avg_vol = sum(c.volume for c in recent[:-1]) / len(recent[:-1]) if len(recent) > 1 else last_vol
        if avg_vol <= 0:
            continue
        ratio = last_vol / avg_vol
        rows.append(
            ScanResultRow(
                exchange=exchange,
                symbol=symbol,
                value=round(ratio, 2),
                extra={"volume": last_vol, "avg_volume": avg_vol},
            )
        )
    rows.sort(key=lambda r: r.value, reverse=True)
    return rows[:limit]


def run_most_active(
    gateway: BrokerGateway,
    exchange: str = "NSE",
    symbols: list[str] | None = None,
    limit: int = 20,
) -> list[ScanResultRow]:
    """Sort by last day volume (desc)."""
    symbols = symbols or DEFAULT_UNIVERSE_NSE
    market_data = MarketDataService(gateway)
    data = _fetch_daily_candles(market_data, exchange, symbols, days_back=5)
    rows: list[ScanResultRow] = []
    for symbol, candles in data.items():
        if not candles:
            continue
        last = candles[-1]
        rows.append(
            ScanResultRow(
                exchange=exchange,
                symbol=symbol,
                value=last.volume,
                extra={"close": last.close},
            )
        )
    rows.sort(key=lambda r: r.value, reverse=True)
    return rows[:limit]


def _swing_low_index(candles: list[Candle], lookback: int = 5) -> int | None:
    """Index of most recent swing low (low < left and right)."""
    if len(candles) < lookback or lookback < 2:
        return None
    for i in range(len(candles) - 1, lookback - 1, -1):
        low = candles[i].low
        if all(candles[j].low >= low for j in range(i - 1, i - lookback - 1, -1)):
            if i + 1 < len(candles) and candles[i + 1].low >= low:
                return i
    return None


def _swing_high_index(candles: list[Candle], lookback: int = 5) -> int | None:
    """Index of most recent swing high."""
    if len(candles) < lookback or lookback < 2:
        return None
    for i in range(len(candles) - 1, lookback - 1, -1):
        high = candles[i].high
        if all(candles[j].high <= high for j in range(i - 1, i - lookback - 1, -1)):
            if i + 1 < len(candles) and candles[i + 1].high <= high:
                return i
    return None


def run_demand_zones(
    gateway: BrokerGateway,
    exchange: str = "NSE",
    symbols: list[str] | None = None,
    limit: int = 20,
    near_pct: float = 1.5,
) -> list[ScanResultRow]:
    """Symbols where price is near a recent swing low (demand zone)."""
    symbols = symbols or DEFAULT_UNIVERSE_NSE
    market_data = MarketDataService(gateway)
    data = _fetch_daily_candles(market_data, exchange, symbols, days_back=30)
    rows: list[ScanResultRow] = []
    for symbol, candles in data.items():
        if len(candles) < 10:
            continue
        idx = _swing_low_index(candles, lookback=3)
        if idx is None:
            continue
        zone_low = candles[idx].low
        current = candles[-1].close
        if zone_low <= 0:
            continue
        dist_pct = ((current - zone_low) / zone_low) * 100
        if 0 <= dist_pct <= near_pct:
            rows.append(
                ScanResultRow(
                    exchange=exchange,
                    symbol=symbol,
                    value=round(zone_low, 2),
                    extra={"close": current, "distance_pct": round(dist_pct, 2)},
                )
            )
    rows.sort(key=lambda r: (r.extra or {}).get("distance_pct", 0))
    return rows[:limit]


def run_supply_zones(
    gateway: BrokerGateway,
    exchange: str = "NSE",
    symbols: list[str] | None = None,
    limit: int = 20,
    near_pct: float = 1.5,
) -> list[ScanResultRow]:
    """Symbols where price is near a recent swing high (supply zone)."""
    symbols = symbols or DEFAULT_UNIVERSE_NSE
    market_data = MarketDataService(gateway)
    data = _fetch_daily_candles(market_data, exchange, symbols, days_back=30)
    rows: list[ScanResultRow] = []
    for symbol, candles in data.items():
        if len(candles) < 10:
            continue
        idx = _swing_high_index(candles, lookback=3)
        if idx is None:
            continue
        zone_high = candles[idx].high
        current = candles[-1].close
        if zone_high <= 0:
            continue
        dist_pct = ((zone_high - current) / zone_high) * 100
        if 0 <= dist_pct <= near_pct:
            rows.append(
                ScanResultRow(
                    exchange=exchange,
                    symbol=symbol,
                    value=round(zone_high, 2),
                    extra={"close": current, "distance_pct": round(dist_pct, 2)},
                )
            )
    rows.sort(key=lambda r: (r.extra or {}).get("distance_pct", 0))
    return rows[:limit]
