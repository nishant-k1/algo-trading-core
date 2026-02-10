"""Settings API: active broker, paper/live, test connection."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUserId, get_db
from app.config import settings as app_settings
from app.db.models.user_settings import UserSettings
from app.db.models.trading_mode import TradingMode
from app.engines.broker.groww import get_groww_access_token
from app.engines.broker.registry import get_gateway, SUPPORTED_BROKERS
from app.core.alerts import notify_kill_switch
from app.schemas.settings import (
    SettingsResponse,
    SettingsUpdate,
    TestConnectionResponse,
    TradingModeResponse,
)

router = APIRouter(prefix="/settings", tags=["settings"])


def _get_or_create_settings(db: Session, user_id: int) -> UserSettings:
    result = db.execute(select(UserSettings).where(UserSettings.user_id == user_id))
    row = result.scalar_one_or_none()
    if row is None:
        row = UserSettings(user_id=user_id)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


@router.get("", response_model=SettingsResponse)
def get_settings(
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
) -> SettingsResponse:
    """Get current user settings."""
    settings_row = _get_or_create_settings(db, user_id)
    return SettingsResponse(
        active_broker_id=settings_row.active_broker_id,
        paper_live=settings_row.paper_live,
        brokers_available=list(SUPPORTED_BROKERS),
        active_trading_mode_id=settings_row.active_trading_mode_id,
        kill_switch=getattr(settings_row, "kill_switch", False),
        max_position_value=getattr(settings_row, "max_position_value", None),
        max_orders_per_day=getattr(settings_row, "max_orders_per_day", None),
        daily_loss_limit_pct=getattr(settings_row, "daily_loss_limit_pct", None),
    )


@router.patch("", response_model=SettingsResponse)
def update_settings(
    body: SettingsUpdate,
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
) -> SettingsResponse:
    """Update settings (broker, paper/live, trading mode, risk, kill switch)."""
    settings_row = _get_or_create_settings(db, user_id)
    if body.active_broker_id is not None and body.active_broker_id in SUPPORTED_BROKERS:
        settings_row.active_broker_id = body.active_broker_id
    if body.paper_live is not None and body.paper_live in ("paper", "live"):
        settings_row.paper_live = body.paper_live
    sent = body.model_dump(exclude_unset=True)
    if "active_trading_mode_id" in sent:
        settings_row.active_trading_mode_id = body.active_trading_mode_id
    if body.kill_switch is not None:
        settings_row.kill_switch = body.kill_switch
        if body.kill_switch:
            try:
                notify_kill_switch(True)
            except Exception:
                pass
    if "max_position_value" in sent:
        settings_row.max_position_value = body.max_position_value
    if "max_orders_per_day" in sent:
        settings_row.max_orders_per_day = body.max_orders_per_day
    if "daily_loss_limit_pct" in sent:
        settings_row.daily_loss_limit_pct = body.daily_loss_limit_pct
    if body.zerodha_access_token is not None:
        settings_row.zerodha_access_token = body.zerodha_access_token or None
    if body.groww_access_token is not None:
        settings_row.groww_access_token = body.groww_access_token or None
    db.commit()
    db.refresh(settings_row)
    return SettingsResponse(
        active_broker_id=settings_row.active_broker_id,
        paper_live=settings_row.paper_live,
        brokers_available=list(SUPPORTED_BROKERS),
        active_trading_mode_id=settings_row.active_trading_mode_id,
        kill_switch=getattr(settings_row, "kill_switch", False),
        max_position_value=getattr(settings_row, "max_position_value", None),
        max_orders_per_day=getattr(settings_row, "max_orders_per_day", None),
        daily_loss_limit_pct=getattr(settings_row, "daily_loss_limit_pct", None),
    )


@router.post("/test-connection", response_model=TestConnectionResponse)
def test_connection(
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
) -> TestConnectionResponse:
    """Test connection for the currently selected broker."""
    try:
        settings_row = _get_or_create_settings(db, user_id)
        broker_id = settings_row.active_broker_id

        groww_token = getattr(settings_row, "groww_access_token", None) or ""
        if broker_id == "groww" and app_settings.groww_api_key and app_settings.groww_api_secret:
            try:
                groww_token = get_groww_access_token(
                    app_settings.groww_api_key,
                    app_settings.groww_api_secret,
                )
                setattr(settings_row, "groww_access_token", groww_token)
                db.commit()
            except Exception as e:
                return TestConnectionResponse(
                    broker_id=broker_id,
                    connected=False,
                    message=f"Groww token exchange failed: {e}",
                )

        gateway = get_gateway(
            broker_id,
            zerodha_access_token=getattr(settings_row, "zerodha_access_token", None) or "",
            groww_access_token=groww_token,
        )
        if gateway is None:
            return TestConnectionResponse(
                broker_id=broker_id,
                connected=False,
                message="Broker not configured or credentials missing",
            )
        try:
            ok = gateway.test_connection()
            return TestConnectionResponse(
                broker_id=broker_id,
                connected=ok,
                message="Connected" if ok else "Connection failed",
            )
        except Exception as e:
            return TestConnectionResponse(
                broker_id=broker_id,
                connected=False,
                message=str(e),
            )
    except Exception as e:
        return TestConnectionResponse(
            broker_id="groww",
            connected=False,
            message=f"Error: {e!s}",
        )


@router.get("/trading-modes", response_model=list[TradingModeResponse])
def list_trading_modes(
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
) -> list[TradingModeResponse]:
    """List available trading modes."""
    result = db.execute(select(TradingMode))
    modes = result.scalars().all()
    return [
        TradingModeResponse(id=m.id, name=m.name, segment=m.segment, product=m.product, exchange=m.exchange)
        for m in modes
    ]
