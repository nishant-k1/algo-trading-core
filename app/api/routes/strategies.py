"""Strategy config CRUD and run."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import CurrentUserId, get_db
from app.db.models.strategy_config import StrategyConfig
from app.db.models.watchlist import Watchlist
from app.db.models.user_settings import UserSettings
from app.db.models.trading_mode import TradingMode
from app.engines.strategy import list_strategies
from app.services.strategy_run import run_strategy_for_user
from app.schemas.strategy import (
    StrategyOption,
    StrategyConfigResponse,
    StrategyConfigCreate,
    StrategyConfigUpdate,
    StrategyRunResponse,
)

router = APIRouter(prefix="/strategies", tags=["strategies"])


def _get_config(db: Session, config_id: int, user_id: int) -> StrategyConfig:
    result = db.execute(
        select(StrategyConfig).where(
            StrategyConfig.id == config_id,
            StrategyConfig.user_id == user_id,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Strategy config not found")
    return row


def _get_watchlist_universe(db: Session, watchlist_id: int, user_id: int) -> list[tuple[str, str]]:
    result = db.execute(
        select(Watchlist).where(
            Watchlist.id == watchlist_id,
            Watchlist.user_id == user_id,
        ).options(joinedload(Watchlist.symbols))
    )
    w = result.scalars().unique().one_or_none()
    if w is None:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return [(s.exchange, s.symbol) for s in w.symbols]


def _product_from_settings(db: Session, user_id: int) -> str:
    result = db.execute(
        select(UserSettings, TradingMode)
        .outerjoin(TradingMode, UserSettings.active_trading_mode_id == TradingMode.id)
        .where(UserSettings.user_id == user_id)
    )
    row = result.one_or_none()
    if row and row[1] is not None:
        return row[1].product
    return "CNC"


@router.get("", response_model=list[StrategyOption])
def list_available_strategies() -> list[StrategyOption]:
    """List available strategy keys and names."""
    return [StrategyOption(key=s["key"], name=s["name"]) for s in list_strategies()]


@router.get("/configs", response_model=list[StrategyConfigResponse])
def list_configs(
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
) -> list[StrategyConfigResponse]:
    """List current user's strategy configs."""
    result = db.execute(
        select(StrategyConfig).where(StrategyConfig.user_id == user_id).order_by(StrategyConfig.id)
    )
    configs = result.scalars().unique().all()
    return [
        StrategyConfigResponse(
            id=c.id,
            name=c.name,
            strategy_key=c.strategy_key,
            params=c.params or {},
            watchlist_id=c.watchlist_id,
            is_active=c.is_active,
        )
        for c in configs
    ]


@router.post("/configs", response_model=StrategyConfigResponse)
def create_config(
    body: StrategyConfigCreate,
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
) -> StrategyConfigResponse:
    """Create a strategy config. Verify watchlist belongs to user."""
    _get_watchlist_universe(db, body.watchlist_id, user_id)
    c = StrategyConfig(
        user_id=user_id,
        name=body.name,
        strategy_key=body.strategy_key,
        params=body.params,
        watchlist_id=body.watchlist_id,
        is_active=False,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return StrategyConfigResponse(
        id=c.id,
        name=c.name,
        strategy_key=c.strategy_key,
        params=c.params or {},
        watchlist_id=c.watchlist_id,
        is_active=c.is_active,
    )


@router.get("/configs/active", response_model=StrategyConfigResponse | None)
def get_active_config(
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
) -> StrategyConfigResponse | None:
    """Get the active strategy config for current user."""
    result = db.execute(
        select(StrategyConfig).where(
            StrategyConfig.user_id == user_id,
            StrategyConfig.is_active == True,
        )
    )
    c = result.scalar_one_or_none()
    if c is None:
        return None
    return StrategyConfigResponse(
        id=c.id,
        name=c.name,
        strategy_key=c.strategy_key,
        params=c.params or {},
        watchlist_id=c.watchlist_id,
        is_active=c.is_active,
    )


@router.patch("/configs/{config_id}", response_model=StrategyConfigResponse)
def update_config(
    config_id: int,
    body: StrategyConfigUpdate,
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
) -> StrategyConfigResponse:
    """Update a strategy config. If is_active=True, deactivate others."""
    c = _get_config(db, config_id, user_id)
    if body.name is not None:
        c.name = body.name
    if body.params is not None:
        c.params = body.params
    if body.watchlist_id is not None:
        _get_watchlist_universe(db, body.watchlist_id, user_id)
        c.watchlist_id = body.watchlist_id
    if body.is_active is True:
        others = db.execute(
            select(StrategyConfig).where(
                StrategyConfig.user_id == user_id,
                StrategyConfig.id != config_id,
            )
        ).scalars().unique().all()
        for other in others:
            other.is_active = False
        c.is_active = True
    elif body.is_active is False:
        c.is_active = False
    db.commit()
    db.refresh(c)
    return StrategyConfigResponse(
        id=c.id,
        name=c.name,
        strategy_key=c.strategy_key,
        params=c.params or {},
        watchlist_id=c.watchlist_id,
        is_active=c.is_active,
    )


@router.delete("/configs/{config_id}", status_code=204)
def delete_config(
    config_id: int,
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
) -> None:
    """Delete a strategy config."""
    c = _get_config(db, config_id, user_id)
    db.delete(c)
    db.commit()


@router.post("/run", response_model=StrategyRunResponse)
def run_strategy(
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
) -> StrategyRunResponse:
    """
    Run the active strategy config: fetch candles for watchlist universe,
    apply gap filter, run strategy, return signals.
    """
    run_response = run_strategy_for_user(db, user_id)
    if run_response is None:
        raise HTTPException(
            status_code=400,
            detail="No active strategy config or broker not configured. Create one and set as active, and set broker in Settings.",
        )
    return run_response
