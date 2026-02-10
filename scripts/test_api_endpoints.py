#!/usr/bin/env python3
"""Test all API endpoints; report pass/fail."""
import os
import sys

# Ensure we load .env and use same app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

BASE = os.environ.get("API_BASE", "http://localhost:8000")
session = requests.Session()
token = None
watchlist_id = None
config_id = None
results = []


def auth_headers():
    return {"Authorization": f"Bearer {token}"} if token else {}


def test(name, method, path, expected_status=None, json_body=None, params=None, auth_required=True, allow_statuses=None):
    """allow_statuses: list of status codes that count as pass (e.g. [200, 404])."""
    url = BASE + path
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if auth_required:
        headers.update(auth_headers())
    try:
        if method == "GET":
            r = session.get(url, headers=headers, params=params or {}, timeout=15)
        elif method == "POST":
            r = session.post(url, headers=headers, json=json_body or {}, timeout=15)
        elif method == "PATCH":
            r = session.patch(url, headers=headers, json=json_body or {}, timeout=15)
        elif method == "DELETE":
            r = session.delete(url, headers=headers, timeout=15)
        else:
            results.append((name, False, f"Unknown method {method}"))
            return r
        default_ok = 200 if method != "DELETE" else 204
        ok_statuses = allow_statuses or [expected_status or default_ok]
        ok = r.status_code in ok_statuses
        if not ok:
            results.append((name, False, f"status={r.status_code} body={r.text[:200]}"))
        else:
            results.append((name, True, f"status={r.status_code}"))
        return r
    except Exception as e:
        results.append((name, False, str(e)))
        return None


def main():
    global token, watchlist_id, config_id

    # No auth
    test("GET /api/health", "GET", "/api/health", auth_required=False)
    test("GET /api/version", "GET", "/api/version", auth_required=False)
    # Login with form (required for subsequent tests)
    r = session.post(
        BASE + "/api/auth/login",
        data={"username": "user", "password": "any"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    if r.status_code != 200:
        results.append(("POST /api/auth/login (form)", False, f"status={r.status_code}"))
    else:
        token = r.json().get("access_token")
        results.append(("POST /api/auth/login (form)", True, "status=200"))

    if not token:
        print("Login failed; skipping auth-required tests")
        for name, ok, msg in results:
            print(f"  {'PASS' if ok else 'FAIL'}: {name} - {msg}")
        return 1

    # Auth required
    test("GET /api/auth/me", "GET", "/api/auth/me")
    test("GET /api/settings", "GET", "/api/settings")
    test("PATCH /api/settings", "PATCH", "/api/settings", json_body={})
    test("POST /api/settings/test-connection", "POST", "/api/settings/test-connection")
    test("GET /api/settings/trading-modes", "GET", "/api/settings/trading-modes")
    test("GET /api/dashboard", "GET", "/api/dashboard")
    test("GET /api/dashboard/pnl-history", "GET", "/api/dashboard/pnl-history", params={"days": 7})
    test("GET /api/orders", "GET", "/api/orders")
    test("GET /api/orders/positions", "GET", "/api/orders/positions")
    test("POST /api/orders", "POST", "/api/orders", json_body={"symbol": "RELIANCE", "exchange": "NSE", "side": "BUY", "quantity": 1})
    test("GET /api/strategies", "GET", "/api/strategies")
    test("GET /api/strategies/configs", "GET", "/api/strategies/configs")
    test("GET /api/strategies/configs/active", "GET", "/api/strategies/configs/active")

    # Watchlists
    test("GET /api/watchlists", "GET", "/api/watchlists")
    r = test("POST /api/watchlists", "POST", "/api/watchlists", json_body={"name": "API Test List"})
    if r and r.status_code == 200:
        watchlist_id = r.json().get("id")
    if not watchlist_id:
        # Try to get first watchlist
        r = session.get(BASE + "/api/watchlists", headers=auth_headers())
        if r.status_code == 200 and r.json():
            watchlist_id = r.json()[0]["id"]
    if watchlist_id:
        test("GET /api/watchlists/{id}", "GET", f"/api/watchlists/{watchlist_id}")
        test("GET /api/watchlists/{id}/universe", "GET", f"/api/watchlists/{watchlist_id}/universe")
        test("POST /api/watchlists/{id}/symbols", "POST", f"/api/watchlists/{watchlist_id}/symbols", json_body={"exchange": "NSE", "symbol": "RELIANCE"})
        test("DELETE /api/watchlists/{id}/symbols", "DELETE", f"/api/watchlists/{watchlist_id}/symbols?exchange=NSE&symbol=RELIANCE", allow_statuses=[200, 204])
        test("PATCH /api/watchlists/{id}", "PATCH", f"/api/watchlists/{watchlist_id}", json_body={"name": "API Test List Renamed"})
    else:
        results.append(("GET/PATCH watchlist (no id)", False, "no watchlist created"))

    test("GET /api/watchlists/auto/universe", "GET", "/api/watchlists/auto/universe", allow_statuses=[200, 404])

    # Strategy configs (need watchlist_id)
    wl_id = watchlist_id or 1
    r = test("POST /api/strategies/configs", "POST", "/api/strategies/configs", json_body={"name": "API Test Config", "strategy_key": "previous_high_breakout", "watchlist_id": wl_id})
    if r and r.status_code == 200:
        config_id = r.json().get("id")
    if config_id:
        test("PATCH /api/strategies/configs/{id}", "PATCH", f"/api/strategies/configs/{config_id}", json_body={"is_active": True})
        test("POST /api/strategies/run", "POST", "/api/strategies/run")
        test("PATCH /api/strategies/configs/{id}", "PATCH", f"/api/strategies/configs/{config_id}", json_body={"is_active": False})
        test("DELETE /api/strategies/configs/{id}", "DELETE", f"/api/strategies/configs/{config_id}")
    else:
        results.append(("Strategy config/run (no config)", False, "create config failed or no watchlist"))

    # Screener (may return empty if no gateway/data)
    for name in ["gainers", "losers", "volume-shockers", "most-active", "demand-zones", "supply-zones"]:
        test(f"GET /api/screener/{name}", "GET", f"/api/screener/{name}", params={"limit": 5})

    # Delete test watchlist if we created one
    if watchlist_id:
        test("DELETE /api/watchlists/{id}", "DELETE", f"/api/watchlists/{watchlist_id}")

    # Report
    passed = sum(1 for _, ok, _ in results if ok)
    failed = [x for x in results if not x[1]]
    print(f"\nResults: {passed}/{len(results)} passed")
    for name, ok, msg in results:
        print(f"  {'PASS' if ok else 'FAIL'}: {name} - {msg}")
    if failed:
        print(f"\nFailed ({len(failed)}):")
        for name, _, msg in failed:
            print(f"  - {name}: {msg}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
