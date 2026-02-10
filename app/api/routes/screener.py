"""Screener API: gainers, losers, volume shockers, demand/supply zones."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import CurrentUserId, get_db, get_user_gateway
from app.engines.screener import (
    run_demand_zones,
    run_gainers,
    run_losers,
    run_most_active,
    run_supply_zones,
    run_volume_shockers,
)
from app.schemas.screener import ScanResponse, ScanRowResponse

router = APIRouter(prefix="/screener", tags=["screener"])


def _to_response(scan: str, exchange: str, rows: list, message: str | None = None) -> ScanResponse:
    return ScanResponse(
        scan=scan,
        exchange=exchange,
        rows=[ScanRowResponse(exchange=r.exchange, symbol=r.symbol, value=r.value, extra=r.extra) for r in rows],
        message=message,
    )


@router.get("/gainers", response_model=ScanResponse)
def screener_gainers(
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
    exchange: str = Query("NSE", description="Exchange"),
    limit: int = Query(20, ge=1, le=100),
    symbols: str | None = Query(None, description="Comma-separated symbols; default universe if omitted"),
) -> ScanResponse:
    """Top gainers by % change (previous close to last close)."""
    gateway = get_user_gateway(db, user_id)
    if gateway is None:
        return _to_response("gainers", exchange, [], message="Configure broker in Settings and connect.")
    sym_list = [s.strip() for s in symbols.split(",")] if symbols else None
    rows = run_gainers(gateway, exchange=exchange, symbols=sym_list, limit=limit)
    return _to_response("gainers", exchange, rows)


@router.get("/losers", response_model=ScanResponse)
def screener_losers(
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
    exchange: str = Query("NSE", description="Exchange"),
    limit: int = Query(20, ge=1, le=100),
    symbols: str | None = Query(None, description="Comma-separated symbols"),
) -> ScanResponse:
    """Top losers by % change."""
    gateway = get_user_gateway(db, user_id)
    if gateway is None:
        return _to_response("losers", exchange, [], message="Configure broker in Settings and connect.")
    sym_list = [s.strip() for s in symbols.split(",")] if symbols else None
    rows = run_losers(gateway, exchange=exchange, symbols=sym_list, limit=limit)
    return _to_response("losers", exchange, rows)


@router.get("/volume-shockers", response_model=ScanResponse)
def screener_volume_shockers(
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
    exchange: str = Query("NSE", description="Exchange"),
    limit: int = Query(20, ge=1, le=100),
    symbols: str | None = Query(None, description="Comma-separated symbols"),
) -> ScanResponse:
    """Volume shockers: last volume vs 20-day average."""
    gateway = get_user_gateway(db, user_id)
    if gateway is None:
        return _to_response("volume_shockers", exchange, [], message="Configure broker in Settings and connect.")
    sym_list = [s.strip() for s in symbols.split(",")] if symbols else None
    rows = run_volume_shockers(gateway, exchange=exchange, symbols=sym_list, limit=limit)
    return _to_response("volume_shockers", exchange, rows)


@router.get("/most-active", response_model=ScanResponse)
def screener_most_active(
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
    exchange: str = Query("NSE", description="Exchange"),
    limit: int = Query(20, ge=1, le=100),
    symbols: str | None = Query(None, description="Comma-separated symbols"),
) -> ScanResponse:
    """Most active by last day volume."""
    gateway = get_user_gateway(db, user_id)
    if gateway is None:
        return _to_response("most_active", exchange, [], message="Configure broker in Settings and connect.")
    sym_list = [s.strip() for s in symbols.split(",")] if symbols else None
    rows = run_most_active(gateway, exchange=exchange, symbols=sym_list, limit=limit)
    return _to_response("most_active", exchange, rows)


@router.get("/demand-zones", response_model=ScanResponse)
def screener_demand_zones(
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
    exchange: str = Query("NSE", description="Exchange"),
    limit: int = Query(20, ge=1, le=100),
    symbols: str | None = Query(None, description="Comma-separated symbols"),
) -> ScanResponse:
    """Symbols at or near a recent demand zone (swing low)."""
    gateway = get_user_gateway(db, user_id)
    if gateway is None:
        return _to_response("demand_zones", exchange, [], message="Configure broker in Settings and connect.")
    sym_list = [s.strip() for s in symbols.split(",")] if symbols else None
    rows = run_demand_zones(gateway, exchange=exchange, symbols=sym_list, limit=limit)
    return _to_response("demand_zones", exchange, rows)


@router.get("/supply-zones", response_model=ScanResponse)
def screener_supply_zones(
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
    exchange: str = Query("NSE", description="Exchange"),
    limit: int = Query(20, ge=1, le=100),
    symbols: str | None = Query(None, description="Comma-separated symbols"),
) -> ScanResponse:
    """Symbols at or near a recent supply zone (swing high)."""
    gateway = get_user_gateway(db, user_id)
    if gateway is None:
        return _to_response("supply_zones", exchange, [], message="Configure broker in Settings and connect.")
    sym_list = [s.strip() for s in symbols.split(",")] if symbols else None
    rows = run_supply_zones(gateway, exchange=exchange, symbols=sym_list, limit=limit)
    return _to_response("supply_zones", exchange, rows)
