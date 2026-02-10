"""Watchlist CRUD and universe resolution."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import CurrentUserId, get_db
from app.db.models.watchlist import Watchlist, WatchlistSymbol
from app.schemas.watchlist import (
    UniverseResponse,
    WatchlistCreate,
    WatchlistResponse,
    WatchlistSymbolSchema,
    WatchlistUpdate,
)

router = APIRouter(prefix="/watchlists", tags=["watchlists"])


def _get_watchlist(db: Session, watchlist_id: int, user_id: int) -> Watchlist:
    result = db.execute(
        select(Watchlist).where(Watchlist.id == watchlist_id, Watchlist.user_id == user_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return row


@router.get("", response_model=list[WatchlistResponse])
def list_watchlists(
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
) -> list[WatchlistResponse]:
    """List all watchlists for the current user."""
    result = db.execute(
        select(Watchlist).where(Watchlist.user_id == user_id).options(joinedload(Watchlist.symbols))
    )
    watchlists = result.scalars().unique().all()
    return [
        WatchlistResponse(
            id=w.id,
            user_id=w.user_id,
            name=w.name,
            is_auto_for_screener=w.is_auto_for_screener,
            symbols=[WatchlistSymbolSchema(exchange=s.exchange, symbol=s.symbol) for s in w.symbols],
        )
        for w in watchlists
    ]


@router.post("", response_model=WatchlistResponse)
def create_watchlist(
    body: WatchlistCreate,
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
) -> WatchlistResponse:
    """Create a new watchlist."""
    w = Watchlist(user_id=user_id, name=body.name, is_auto_for_screener=False)
    db.add(w)
    db.commit()
    db.refresh(w)
    return WatchlistResponse(
        id=w.id,
        user_id=w.user_id,
        name=w.name,
        is_auto_for_screener=w.is_auto_for_screener,
        symbols=[],
    )


@router.get("/auto/universe", response_model=UniverseResponse)
def get_auto_universe(
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
) -> UniverseResponse:
    """Get symbol list for the user's auto (screener) watchlist. 404 if none set."""
    result = db.execute(
        select(Watchlist)
        .where(Watchlist.user_id == user_id, Watchlist.is_auto_for_screener == True)
        .options(joinedload(Watchlist.symbols))
    )
    w = result.scalars().unique().one_or_none()
    if w is None:
        raise HTTPException(status_code=404, detail="No auto watchlist set. Set one in Watchlists.")
    return UniverseResponse(
        watchlist_id=w.id,
        symbols=[WatchlistSymbolSchema(exchange=s.exchange, symbol=s.symbol) for s in w.symbols],
    )


@router.get("/{watchlist_id}", response_model=WatchlistResponse)
def get_watchlist(
    watchlist_id: int,
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
) -> WatchlistResponse:
    """Get one watchlist by id."""
    result = db.execute(
        select(Watchlist)
        .where(Watchlist.id == watchlist_id, Watchlist.user_id == user_id)
        .options(joinedload(Watchlist.symbols))
    )
    w = result.scalars().unique().one_or_none()
    if w is None:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return WatchlistResponse(
        id=w.id,
        user_id=w.user_id,
        name=w.name,
        is_auto_for_screener=w.is_auto_for_screener,
        symbols=[WatchlistSymbolSchema(exchange=s.exchange, symbol=s.symbol) for s in w.symbols],
    )


@router.patch("/{watchlist_id}", response_model=WatchlistResponse)
def update_watchlist(
    watchlist_id: int,
    body: WatchlistUpdate,
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
) -> WatchlistResponse:
    """Update watchlist name and/or set as auto for screener."""
    w = _get_watchlist(db, watchlist_id, user_id)
    if body.name is not None:
        w.name = body.name
    if body.is_auto_for_screener is not None:
        w.is_auto_for_screener = body.is_auto_for_screener
        if body.is_auto_for_screener:
            others = db.execute(
                select(Watchlist).where(Watchlist.user_id == user_id, Watchlist.id != watchlist_id)
            ).scalars().all()
            for o in others:
                o.is_auto_for_screener = False
    db.commit()
    result = db.execute(
        select(Watchlist).where(Watchlist.id == watchlist_id).options(joinedload(Watchlist.symbols))
    )
    w = result.scalars().unique().one_or_none()
    if not w:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return WatchlistResponse(
        id=w.id,
        user_id=w.user_id,
        name=w.name,
        is_auto_for_screener=w.is_auto_for_screener,
        symbols=[WatchlistSymbolSchema(exchange=s.exchange, symbol=s.symbol) for s in w.symbols],
    )


@router.delete("/{watchlist_id}", status_code=204)
def delete_watchlist(
    watchlist_id: int,
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
) -> None:
    """Delete a watchlist."""
    w = _get_watchlist(db, watchlist_id, user_id)
    db.delete(w)
    db.commit()


@router.post("/{watchlist_id}/symbols")
def add_symbol(
    watchlist_id: int,
    body: WatchlistSymbolSchema,
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Add a symbol to the watchlist."""
    w = _get_watchlist(db, watchlist_id, user_id)
    existing = db.execute(
        select(WatchlistSymbol).where(
            WatchlistSymbol.watchlist_id == watchlist_id,
            WatchlistSymbol.exchange == body.exchange,
            WatchlistSymbol.symbol == body.symbol,
        )
    ).scalar_one_or_none()
    if existing:
        return {"status": "already_present"}
    sym = WatchlistSymbol(watchlist_id=watchlist_id, exchange=body.exchange, symbol=body.symbol)
    db.add(sym)
    db.commit()
    return {"status": "added"}


@router.delete("/{watchlist_id}/symbols")
def remove_symbol(
    watchlist_id: int,
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
    exchange: str = Query("NSE"),
    symbol: str = Query(..., description="Symbol to remove"),
) -> dict[str, str]:
    """Remove a symbol from the watchlist."""
    w = _get_watchlist(db, watchlist_id, user_id)
    result = db.execute(
        select(WatchlistSymbol).where(
            WatchlistSymbol.watchlist_id == watchlist_id,
            WatchlistSymbol.exchange == exchange,
            WatchlistSymbol.symbol == symbol,
        )
    )
    sym = result.scalar_one_or_none()
    if sym:
        db.delete(sym)
        db.commit()
    return {"status": "removed"}


@router.get("/{watchlist_id}/universe", response_model=UniverseResponse)
def get_watchlist_universe(
    watchlist_id: int,
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
) -> UniverseResponse:
    """Get symbol list (universe) for a watchlist."""
    w = _get_watchlist(db, watchlist_id, user_id)
    return UniverseResponse(
        watchlist_id=w.id,
        symbols=[WatchlistSymbolSchema(exchange=s.exchange, symbol=s.symbol) for s in w.symbols],
    )
