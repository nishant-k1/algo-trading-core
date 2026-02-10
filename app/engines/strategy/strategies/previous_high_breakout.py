"""Previous day high breakout: BUY when today's close > previous day's high."""

from app.engines.broker.base import Candle
from app.engines.strategy.base import Signal, Strategy, StrategyContext


class PreviousHighBreakoutStrategy(Strategy):
    """Close above previous day high => BUY. Params: lookback_days (default 1)."""

    def run(self, ctx: StrategyContext) -> list[Signal]:
        signals: list[Signal] = []
        lookback = max(1, int(ctx.params.get("lookback_days", 1)))
        for symbol, candles in ctx.symbols_candles.items():
            if len(candles) < lookback + 1:
                continue
            prev_high = max(c.high for c in candles[-(lookback + 1) : -1])
            today = candles[-1]
            if today.close > prev_high and today.volume > 0:
                signals.append(
                    Signal(
                        exchange=ctx.exchange,
                        symbol=symbol,
                        side="BUY",
                        reason="close_above_previous_high",
                        score=1.0,
                        meta={"prev_high": prev_high, "close": today.close},
                    )
                )
        return signals
