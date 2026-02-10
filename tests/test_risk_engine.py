"""Unit tests for risk engine (pre_trade_checks with mocked DB)."""
from unittest.mock import MagicMock

from app.engines.risk import pre_trade_checks


def test_pre_trade_checks_no_settings() -> None:
    db = MagicMock()
    db.execute.return_value.scalar_one_or_none.return_value = None
    allowed, msg = pre_trade_checks(
        db, user_id=1, paper_live="paper", side="BUY", quantity=10,
        price_estimate=100.0, symbol="REL", exchange="NSE", product="CNC",
    )
    assert allowed is True
    assert msg == ""
