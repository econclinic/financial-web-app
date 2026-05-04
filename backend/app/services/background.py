"""Background task runner.

Runs periodic tasks in a separate asyncio task.
Designed to be extensible — add new tasks to _run_tasks().
"""

import asyncio
import logging

from app.core.database import SessionLocal
from app.services.alerts import evaluate_alerts
from app.services.market_data_service import get_current_prices_map

logger = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 60


def _check_alerts() -> None:
    """Evaluate all active alerts against current market prices."""
    db = SessionLocal()
    try:
        prices = get_current_prices_map()
        triggered = evaluate_alerts(db, prices)
        if triggered > 0:
            logger.info("Triggered %d alert(s)", triggered)
    except Exception:
        logger.exception("Alert check failed")
    finally:
        db.close()


async def _run_tasks() -> None:
    """Main loop: run all periodic tasks every CHECK_INTERVAL_SECONDS."""
    while True:
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
        await asyncio.to_thread(_check_alerts)


async def start_background_worker() -> asyncio.Task:
    """Start the background worker and return the task handle."""
    task = asyncio.create_task(_run_tasks())
    logger.info("Background worker started (interval=%ds)", CHECK_INTERVAL_SECONDS)
    return task
