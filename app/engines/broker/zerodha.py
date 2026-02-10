"""Zerodha Kite Connect gateway adapter."""

from datetime import datetime
from typing import Any

from app.engines.broker.base import (
    BrokerGateway,
    Candle,
    Instrument,
    OrderRequest,
    Position,
)


class ZerodhaGateway(BrokerGateway):
    """Zerodha Kite Connect API adapter."""

    def __init__(self, api_key: str, api_secret: str, access_token: str = "") -> None:
        self._api_key = api_key
        self._api_secret = api_secret
        self._access_token = access_token
        self._kite = None
        if api_key and access_token:
            try:
                from kiteconnect import KiteConnect

                self._kite = KiteConnect(api_key=api_key)
                self._kite.set_access_token(access_token)
            except Exception:
                self._kite = None

    def _ensure_connected(self) -> None:
        if self._kite is None:
            raise RuntimeError("Zerodha: not connected; set api_key and access_token")

    def get_historical_candles(
        self,
        exchange: str,
        symbol: str,
        interval: str,
        from_date: datetime,
        to_date: datetime,
    ) -> list[Candle]:
        self._ensure_connected()
        instruments = self.get_instruments(exchange)
        token = None
        for inst in instruments:
            if inst.symbol == symbol and inst.exchange == exchange:
                token = str(inst.token) if isinstance(inst.token, int) else inst.token
                break
        if token is None:
            return []
        # Kite: interval "minute", "3minute", "day" etc.; instrument_token must be int
        token_int = int(token)
        raw = self._kite.historical_data(
            token_int,
            from_date,
            to_date,
            interval,
        )
        return [
            Candle(
                timestamp=datetime.fromisoformat(r["date"].replace("Z", "+00:00"))
                if hasattr(r["date"], "isoformat")
                else r["date"],
                open=float(r["open"]),
                high=float(r["high"]),
                low=float(r["low"]),
                close=float(r["close"]),
                volume=float(r.get("volume", 0)),
            )
            for r in (raw or [])
        ]

    def get_instruments(self, exchange: str | None = None) -> list[Instrument]:
        self._ensure_connected()
        # Kite returns list of dicts with exchange, tradingsymbol, instrument_token, name
        raw = self._kite.instruments(exchange) if exchange else self._kite.instruments()
        return [
            Instrument(
                exchange=str(r.get("exchange", "")),
                symbol=str(r.get("tradingsymbol", "")),
                token=str(r.get("instrument_token", "")),
                name=str(r.get("name", "")),
            )
            for r in (raw or [])
        ]

    def place_order(self, req: OrderRequest) -> dict[str, Any]:
        self._ensure_connected()
        return self._kite.place_order(
            variety="regular",
            tradingsymbol=req.symbol,
            exchange=req.exchange,
            transaction_type=req.side,
            quantity=req.quantity,
            product=req.product,
            order_type=req.order_type,
            price=req.price or 0,
            trigger_price=req.trigger_price or 0,
            validity=req.validity,
            tag=req.client_order_id or "",
        )

    def cancel_order(self, order_id: str, variety: str = "regular") -> dict[str, Any]:
        self._ensure_connected()
        return self._kite.cancel_order(variety=variety, order_id=order_id)

    def get_orders(self) -> list[dict[str, Any]]:
        self._ensure_connected()
        return self._kite.orders() or []

    def get_positions(self) -> list[Position]:
        self._ensure_connected()
        raw = self._kite.positions() or {}
        positions = raw.get("net", []) or []
        return [
            Position(
                symbol=str(p.get("tradingsymbol", "")),
                exchange=str(p.get("exchange", "")),
                side="BUY" if int(p.get("quantity", 0)) >= 0 else "SELL",
                quantity=abs(int(p.get("quantity", 0))),
                average_price=float(p.get("average_price", 0)),
                product=str(p.get("product", "")),
            )
            for p in positions
        ]

    def test_connection(self) -> bool:
        try:
            self._ensure_connected()
            self._kite.profile()
            return True
        except Exception:
            return False
