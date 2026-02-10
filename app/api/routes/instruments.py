"""Instruments API: symbol search for autocomplete."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import CurrentUserId, get_db, get_user_gateway
from app.engines.instrument_master import InstrumentMaster

router = APIRouter(prefix="/instruments", tags=["instruments"])


@router.get("/suggest", response_model=list[dict])
def suggest_symbols(
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
    q: str = Query("", min_length=1, max_length=20),
    exchange: str = Query("NSE"),
    limit: int = Query(20, ge=1, le=50),
) -> list[dict]:
    """Suggest symbols for autocomplete (e.g. watchlist). Requires broker configured."""
    gateway = get_user_gateway(db, user_id)
    if gateway is None:
        return []
    try:
        master = InstrumentMaster(gateway)
        instruments = master.get_instruments(exchange=exchange)
        q_lower = q.strip().upper()
        out = [
            {"symbol": inst.symbol, "exchange": inst.exchange}
            for inst in instruments
            if q_lower in inst.symbol.upper()
        ][:limit]
        return out
    except Exception:
        return []
