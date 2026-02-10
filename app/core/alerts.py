"""Alerts: Telegram (and optional email) on order, risk, kill switch."""

import httpx

from app.config import settings


def _send_telegram(text: str) -> bool:
    """Send message to Telegram. Returns True if sent."""
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return False
    try:
        url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
        r = httpx.post(
            url,
            json={"chat_id": settings.telegram_chat_id, "text": text, "disable_web_page_preview": True},
            timeout=10.0,
        )
        return r.status_code == 200
    except Exception:
        return False


def notify_order_placed(
    symbol: str,
    exchange: str,
    side: str,
    quantity: int,
    paper_live: str,
    order_id: str | None = None,
) -> None:
    """Notify when an order is placed."""
    mode = "Paper" if paper_live == "paper" else "Live"
    msg = f"[Algo Trading] {mode} order: {side} {quantity} {symbol} ({exchange})"
    if order_id:
        msg += f" | id: {order_id}"
    _send_telegram(msg)


def notify_kill_switch(on: bool) -> None:
    """Notify when kill switch is toggled."""
    state = "ON" if on else "OFF"
    _send_telegram(f"[Algo Trading] Kill switch turned {state}. New orders are {'blocked' if on else 'allowed'}.")


def notify_daily_loss_limit(user_id: int, pct: float) -> None:
    """Notify when daily loss limit is hit."""
    _send_telegram(f"[Algo Trading] Daily loss limit reached for user {user_id}: {pct:.1f}%.")
