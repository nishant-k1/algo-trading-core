"""Market data service: historical candles with Redis cache."""

import json
from datetime import datetime

from app.db.redis_client import get_redis_sync
from app.engines.broker.base import BrokerGateway, Candle

CANDLES_CACHE_TTL = 300  # 5 minutes


def _candle_to_dict(c: Candle) -> dict:
    return {
        "timestamp": c.timestamp.isoformat() if c.timestamp else None,
        "open": c.open,
        "high": c.high,
        "low": c.low,
        "close": c.close,
        "volume": c.volume,
    }


def _dict_to_candle(d: dict) -> Candle:
    ts = d.get("timestamp")
    if isinstance(ts, str):
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    else:
        dt = datetime.now()
    return Candle(
        timestamp=dt,
        open=float(d["open"]),
        high=float(d["high"]),
        low=float(d["low"]),
        close=float(d["close"]),
        volume=float(d.get("volume", 0)),
    )


class MarketDataService:
    """Fetch OHLCV data from broker gateway with Redis cache."""

    def __init__(self, gateway: BrokerGateway) -> None:
        self._gateway = gateway

    def get_historical_candles(
        self,
        exchange: str,
        symbol: str,
        interval: str,
        from_date: datetime,
        to_date: datetime,
    ) -> list[Candle]:
        """Get historical candles from cache or broker."""
        from_str = from_date.strftime("%Y-%m-%d") if from_date else ""
        to_str = to_date.strftime("%Y-%m-%d") if to_date else ""
        key = f"candles:{exchange}:{symbol}:{interval}:{from_str}:{to_str}"
        try:
            r = get_redis_sync()
            raw = r.get(key)
            if raw:
                data = json.loads(raw)
                return [_dict_to_candle(item) for item in data]
        except Exception:
            pass
        candles = self._gateway.get_historical_candles(
            exchange=exchange,
            symbol=symbol,
            interval=interval,
            from_date=from_date,
            to_date=to_date,
        )
        try:
            r = get_redis_sync()
            r.setex(
                key,
                CANDLES_CACHE_TTL,
                json.dumps([_candle_to_dict(c) for c in candles], default=str),
            )
        except Exception:
            pass
        return candles
