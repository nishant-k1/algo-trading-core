"""Strategy run with mocked broker/market data (no real broker or market calls)."""
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.engines.broker.base import Candle


def _make_candle(open_: float, high: float, low: float, close: float) -> Candle:
    return Candle(
        timestamp=datetime.now(timezone.utc),
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=1000,
    )


@pytest.fixture
def mock_gateway():
    """Gateway that returns fake candles (two days: prev high 105, today close 106)."""
    gw = MagicMock()
    gw.get_historical_candles.return_value = [
        _make_candle(100, 105, 99, 104),
        _make_candle(104, 106, 103, 106),
    ]
    return gw


@pytest.mark.integration
def test_run_strategy_with_mocked_gateway(
    client: TestClient,
    auth_headers: dict[str, str],
    mock_gateway: MagicMock,
) -> None:
    """POST /strategies/run uses mocked gateway; no real broker or market data."""
    with patch("app.services.strategy_run.get_user_gateway", return_value=mock_gateway):
        # Need active config + watchlist with symbols. Create via API.
        wl = client.post("/api/watchlists", headers=auth_headers, json={"name": "E2E Run WL"})
        assert wl.status_code == 200
        watchlist_id = wl.json()["id"]
        client.post(
            f"/api/watchlists/{watchlist_id}/symbols",
            headers=auth_headers,
            json={"exchange": "NSE", "symbol": "RELIANCE"},
        )
        cfg = client.post(
            "/api/strategies/configs",
            headers=auth_headers,
            json={
                "name": "E2E Run Config",
                "strategy_key": "previous_high_breakout",
                "watchlist_id": watchlist_id,
            },
        )
        assert cfg.status_code == 200
        config_id = cfg.json()["id"]
        client.patch(
            f"/api/strategies/configs/{config_id}",
            headers=auth_headers,
            json={"is_active": True},
        )

        r = client.post("/api/strategies/run", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert "signals" in data
        assert "symbols_scanned" in data
        assert "symbols_filtered_by_gap" in data
        assert isinstance(data["signals"], list)
        assert mock_gateway.get_historical_candles.called
