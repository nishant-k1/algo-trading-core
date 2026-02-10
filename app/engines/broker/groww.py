"""Groww Trade API gateway adapter (REST)."""

import hashlib
import time
from datetime import datetime
from typing import Any

import httpx

from app.engines.broker.base import (
    BrokerGateway,
    Candle,
    Instrument,
    OrderRequest,
    Position,
)

GROWW_BASE = "https://api.groww.in/v1"
GROWW_TOKEN_URL = "https://api.groww.in/v1/token/api/access"


def get_groww_access_token(api_key: str, api_secret: str) -> str:
    """
    Exchange Groww API key + secret for an access token (approval flow).
    Requires daily approval on https://groww.in/trade-api/api-keys
    """
    if not api_key or not api_secret:
        raise ValueError("Groww API key and secret required")
    timestamp = str(int(time.time()))
    checksum = hashlib.sha256((api_secret + timestamp).encode("utf-8")).hexdigest()
    r = httpx.post(
        GROWW_TOKEN_URL,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "X-API-VERSION": "1.0",
        },
        json={
            "key_type": "approval",
            "checksum": checksum,
            "timestamp": timestamp,
        },
        timeout=15.0,
    )
    try:
        data = r.json() if r.content else {}
    except Exception:
        data = {}
    if not isinstance(data, dict):
        data = {}
    if data.get("status") == "FAILURE":
        err = data.get("error", {}) or {}
        msg = err.get("message", "Groww token exchange failed") if isinstance(err, dict) else "Groww token exchange failed"
        raise RuntimeError(msg)
    if r.status_code >= 400:
        raise RuntimeError(data.get("message", f"Groww API returned {r.status_code}"))
    payload = data.get("payload", data)
    if isinstance(payload, dict):
        token = payload.get("token")
    else:
        token = data.get("token")
    if not token:
        raise RuntimeError("No token in Groww response")
    return str(token)


class GrowwGateway(BrokerGateway):
    """Groww Trade API adapter via REST."""

    def __init__(self, access_token: str = "") -> None:
        self._access_token = access_token
        self._client = httpx.Client(
            base_url=GROWW_BASE,
            headers={
                "Accept": "application/json",
                "X-API-VERSION": "1.0",
                "Authorization": f"Bearer {access_token}" if access_token else "",
            },
            timeout=30.0,
        )

    def _ensure_connected(self) -> None:
        if not self._access_token:
            raise RuntimeError("Groww: not connected; set access_token")

    def _get(self, path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        r = self._client.get(path, params=params or {})
        r.raise_for_status()
        data = r.json()
        if data.get("status") == "FAILURE":
            err = data.get("error", {})
            raise RuntimeError(err.get("message", "Groww API error"))
        return data.get("payload", data)

    def _post(self, path: str, json: dict[str, Any]) -> dict[str, Any]:
        r = self._client.post(path, json=json)
        r.raise_for_status()
        data = r.json()
        if data.get("status") == "FAILURE":
            err = data.get("error", {})
            raise RuntimeError(err.get("message", "Groww API error"))
        return data.get("payload", data)

    def get_historical_candles(
        self,
        exchange: str,
        symbol: str,
        interval: str,
        from_date: datetime,
        to_date: datetime,
    ) -> list[Candle]:
        self._ensure_connected()
        # Groww: interval_in_minutes = 1, 5, 60, 1440 (day), etc.
        interval_map = {"minute": 1, "5minute": 5, "15minute": 15, "60minute": 60, "day": 1440}
        interval_min = interval_map.get(interval, 5)
        start = from_date.strftime("%Y-%m-%d %H:%M:%S")
        end = to_date.strftime("%Y-%m-%d %H:%M:%S")
        payload = self._get(
            "/historical/candle/range",
            params={
                "exchange": exchange,
                "segment": "CASH",
                "trading_symbol": symbol,
                "start_time": start,
                "end_time": end,
                "interval_in_minutes": str(interval_min),
            },
        )
        candles_raw = payload.get("candles") or []
        return [
            Candle(
                timestamp=datetime.fromtimestamp(c[0]),
                open=float(c[1]),
                high=float(c[2]),
                low=float(c[3]),
                close=float(c[4]),
                volume=float(c[5]) if len(c) > 5 else 0,
            )
            for c in candles_raw
        ]

    def get_instruments(self, exchange: str | None = None) -> list[Instrument]:
        self._ensure_connected()
        # Groww instruments endpoint - check docs for path
        path = "/instruments"
        params = {} if not exchange else {"exchange": exchange}
        payload = self._get(path, params=params)
        items = payload if isinstance(payload, list) else payload.get("instruments", [])
        return [
            Instrument(
                exchange=str(i.get("exchange", "")),
                symbol=str(i.get("tradingsymbol", i.get("trading_symbol", ""))),
                token=str(i.get("instrument_token", i.get("token", ""))),
                name=str(i.get("name", "")),
            )
            for i in items
        ]

    def place_order(self, req: OrderRequest) -> dict[str, Any]:
        self._ensure_connected()
        body = {
            "exchange": req.exchange,
            "transaction_type": req.side,
            "order_type": req.order_type,
            "quantity": req.quantity,
            "product": req.product,
            "validity": req.validity,
            "segment": "CASH",
            "trading_symbol": req.symbol,
            "price": req.price or 0,
        }
        if req.client_order_id:
            body["order_reference_id"] = req.client_order_id
        return self._post("/order/create", body)

    def cancel_order(self, order_id: str, variety: str = "regular") -> dict[str, Any]:
        self._ensure_connected()
        return self._post("/order/cancel", {"groww_order_id": order_id})

    def get_orders(self) -> list[dict[str, Any]]:
        self._ensure_connected()
        payload = self._get("/order/list", {"segment": "CASH"})
        return payload if isinstance(payload, list) else payload.get("orders", [])

    def get_positions(self) -> list[Position]:
        self._ensure_connected()
        payload = self._get("/portfolio/positions", {"segment": "CASH"})
        positions = payload if isinstance(payload, list) else payload.get("positions", [])
        return [
            Position(
                symbol=str(p.get("tradingsymbol", p.get("trading_symbol", ""))),
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
            self._get("/user/profile")
            return True
        except Exception:
            return False
