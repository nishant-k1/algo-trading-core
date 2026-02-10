"""Gap up open: BUY when today opens above previous close and holds above previous high."""

from app.engines.broker.base import Candle
from app.engines.strategy.base import Signal, Strategy, StrategyContext


class GapUpOpenStrategy(Strategy):
    """Gap up (open > prev close) and current close above prev high => BUY."""

    def run(self, ctx: StrategyContext) -> list[Signal]:
        signals: list[Signal] = []
        for symbol, candles in ctx.symbols_candles.items():
            if len(candles) < 2:
                continue
            prev = candles[-2]
            today = candles[-1]
            gap_up = today.open > prev.close
            above_prev_high = today.close > prev.high
            if gap_up and above_prev_high and today.volume > 0:
                signals.append(
                    Signal(
                        exchange=ctx.exchange,
                        symbol=symbol,
                        side="BUY",
                        reason="gap_up_above_prev_high",
                        score=1.0,
                        meta={"prev_high": prev.high, "open": today.open, "close": today.close},
                    )
                )
        return signals
