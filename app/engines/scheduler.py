"""APScheduler: run strategies at market open (9:15 AM India)."""

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from app.db.models.strategy_config import StrategyConfig
from app.db.session import SessionLocal
from app.services.strategy_run import run_strategy_for_user

logger = logging.getLogger(__name__)
_scheduler: BackgroundScheduler | None = None


def _scheduled_run_job() -> None:
    """Run active strategy config for each user (9:15 AM)."""
    db = SessionLocal()
    try:
        result = db.execute(
            select(StrategyConfig.user_id)
            .where(StrategyConfig.is_active == True)
            .distinct()
        )
        user_ids = [row[0] for row in result.all()]
        for user_id in user_ids:
            try:
                run_strategy_for_user(db, user_id)
                logger.info("Scheduled strategy run completed for user_id=%s", user_id)
            except Exception as e:
                logger.exception("Scheduled strategy run failed for user_id=%s: %s", user_id, e)
    finally:
        db.close()


def start_scheduler() -> None:
    """Start background scheduler (9:15 AM IST = 3:45 UTC)."""
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = BackgroundScheduler(timezone=timezone.utc)
    _scheduler.add_job(
        _scheduled_run_job,
        CronTrigger(hour=3, minute=45, timezone=timezone.utc),
        id="strategy_run",
    )
    _scheduler.start()
    logger.info("Scheduler started (strategy run at 09:15 IST)")


def stop_scheduler() -> None:
    """Stop scheduler (e.g. on app shutdown)."""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler stopped")
