"""Broker registry: return gateway by broker id and credentials."""

from app.config import settings
from app.engines.broker.base import BrokerGateway
from app.engines.broker.groww import GrowwGateway
from app.engines.broker.zerodha import ZerodhaGateway

BROKER_ZERODHA = "zerodha"
BROKER_GROWW = "groww"
SUPPORTED_BROKERS = (BROKER_ZERODHA, BROKER_GROWW)


def get_gateway(
    broker_id: str,
    *,
    zerodha_access_token: str = "",
    groww_access_token: str = "",
) -> BrokerGateway | None:
    """
    Return gateway for the given broker_id. Uses env credentials; pass access_token
    when stored per-session (e.g. Zerodha/Groww token).
    """
    if broker_id == BROKER_ZERODHA:
        if not settings.zerodha_api_key:
            return None
        return ZerodhaGateway(
            api_key=settings.zerodha_api_key,
            api_secret=settings.zerodha_api_secret or "",
            access_token=zerodha_access_token or "",
        )
    if broker_id == BROKER_GROWW:
        token = groww_access_token or ""
        if not token and settings.groww_api_key:
            # Can't get token here without user approval; return gateway that will fail test_connection
            return GrowwGateway(access_token="")
        return GrowwGateway(access_token=token)
    return None
