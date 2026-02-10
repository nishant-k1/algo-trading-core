"""Run strategy for a user (used by API route and scheduler)."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_user_gateway
from app.db.models.strategy_config import StrategyConfig
from app.db.models.strategy_run_cache import StrategyRunCache
from app.db.models.watchlist import Watchlist
from app.db.models.user_settings import UserSettings
from app.db.models.trading_mode import TradingMode
from app.engines.market_data import MarketDataService
from app.engines.strategy import (
    get_strategy,
    apply_gap_filter,
    symbols_filtered_by_gap,
)
from app.engines.strategy.base import StrategyContext
from app.schemas.strategy import StrategyRunResponse, SignalResponse


def _get_watchlist_universe(db: Session, watchlist_id: int, user_id: int) -> list[tuple[str, str]]:
    result = db.execute(
        select(Watchlist).where(
            Watchlist.id == watchlist_id,
            Watchlist.user_id == user_id,
        ).options(joinedload(Watchlist.symbols))
    )
    w = result.scalars().unique().one_or_none()
    if w is None:
        return []
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


def run_strategy_for_user(db: Session, user_id: int) -> StrategyRunResponse | None:
    """
    Run the active strategy config for the user. Returns None if no active config or no gateway.
    """
    config = db.execute(
        select(StrategyConfig).where(
            StrategyConfig.user_id == user_id,
            StrategyConfig.is_active == True,
        )
    ).scalar_one_or_none()
    if config is None:
        return None
    strategy = get_strategy(config.strategy_key)
    if strategy is None:
        return None
    gateway = get_user_gateway(db, user_id)
    if gateway is None:
        return None
    universe = _get_watchlist_universe(db, config.watchlist_id, user_id)
    if not universe:
        return StrategyRunResponse(signals=[], symbols_scanned=0, symbols_filtered_by_gap=0)

    market_data = MarketDataService(gateway)
    to_d = datetime.now(timezone.utc)
    from_d = to_d - timedelta(days=30)
    symbols_candles: dict[str, list] = {}
    exchange = universe[0][0]
    for _ex, symbol in universe:
        exchange = _ex
        try:
            candles = market_data.get_historical_candles(
                exchange=exchange,
                symbol=symbol,
                interval="day",
                from_date=from_d,
                to_date=to_d,
            )
            if candles:
                symbols_candles[symbol] = sorted(candles, key=lambda x: x.timestamp)
        except Exception:
            continue

    max_gap_pct = float((config.params or {}).get("max_gap_pct", 2.0))
    excluded = symbols_filtered_by_gap(symbols_candles, max_gap_pct)
    filtered = apply_gap_filter(symbols_candles, max_gap_pct)
    product = _product_from_settings(db, user_id)
    ctx = StrategyContext(
        exchange=exchange,
        product=product,
        symbols_candles=filtered,
        params=config.params or {},
    )
    signals = strategy.run(ctx)

    run_response = StrategyRunResponse(
        signals=[
            SignalResponse(
                exchange=s.exchange,
                symbol=s.symbol,
                side=s.side,
                reason=s.reason,
                score=s.score,
                meta=s.meta,
            )
            for s in signals
        ],
        symbols_scanned=len(symbols_candles),
        symbols_filtered_by_gap=len(excluded),
    )

    cache = db.execute(
        select(StrategyRunCache).where(StrategyRunCache.user_id == user_id)
    ).scalar_one_or_none()
    if cache is None:
        cache = StrategyRunCache(
            user_id=user_id,
            run_at=datetime.now(timezone.utc),
            signals_count=len(signals),
            symbols_scanned=len(symbols_candles),
            symbols_filtered_by_gap=len(excluded),
        )
        db.add(cache)
    else:
        cache.run_at = datetime.now(timezone.utc)
        cache.signals_count = len(signals)
        cache.symbols_scanned = len(symbols_candles)
        cache.symbols_filtered_by_gap = len(excluded)
    db.commit()
    return run_response
