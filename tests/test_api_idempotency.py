"""Idempotency: duplicate place_order with same client_order_id returns same order."""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_place_order_idempotent_same_client_order_id(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    body = {
        "symbol": "REL",
        "exchange": "NSE",
        "side": "BUY",
        "quantity": 1,
        "order_type": "MARKET",
        "client_order_id": "e2e-idempotent-001",
    }
    r1 = client.post("/api/orders", headers=auth_headers, json=body)
    assert r1.status_code == 200
    data1 = r1.json()
    assert data1["client_order_id"] == "e2e-idempotent-001"
    order_id_1 = data1["id"]

    r2 = client.post("/api/orders", headers=auth_headers, json=body)
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["client_order_id"] == "e2e-idempotent-001"
    assert data2["id"] == order_id_1
