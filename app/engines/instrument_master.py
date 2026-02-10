"""Instrument master: resolve symbol <-> token via broker gateway."""

from app.engines.broker.base import BrokerGateway, Instrument


class InstrumentMaster:
    """Resolve instruments from broker; cache can be added later (DB/Redis)."""

    def __init__(self, gateway: BrokerGateway) -> None:
        self._gateway = gateway
        self._cache: list[Instrument] | None = None

    def get_instruments(self, exchange: str | None = None, use_cache: bool = True) -> list[Instrument]:
        """Get instrument list from broker; optional in-memory cache."""
        if use_cache and self._cache is not None and exchange is None:
            return self._cache
        instruments = self._gateway.get_instruments(exchange)
        if use_cache and exchange is None:
            self._cache = instruments
        return instruments

    def get_token(self, exchange: str, symbol: str) -> str | None:
        """Resolve (exchange, symbol) to broker token."""
        for inst in self.get_instruments(exchange=None):
            if inst.exchange == exchange and inst.symbol == symbol:
                return str(inst.token)
        for inst in self.get_instruments(exchange=exchange):
            if inst.symbol == symbol:
                return str(inst.token)
        return None
