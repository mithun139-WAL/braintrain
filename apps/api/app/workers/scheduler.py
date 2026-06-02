"""
APScheduler setup — background job scheduler for BrainTrain API.

Jobs:
  - evaluation_tick   every 10 seconds — processes one PENDING EvaluationJob
  - zombie_recovery   every 5 minutes  — resets stuck PROCESSING jobs

Uses AsyncIOScheduler so all jobs run on the same asyncio event loop as FastAPI.

Usage (in app/main.py lifespan):
    from app.workers.scheduler import start_scheduler, stop_scheduler

    @asynccontextmanager
    async def lifespan(app):
        start_scheduler()
        yield
        stop_scheduler()
"""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)

_scheduler = AsyncIOScheduler()


def start_scheduler() -> None:
    """Register all background jobs and start the scheduler."""
    from app.workers.evaluation_worker import run_evaluation_tick, run_zombie_recovery

    _scheduler.add_job(
        run_evaluation_tick,
        trigger="interval",
        seconds=10,
        id="evaluation_tick",
        max_instances=1,          # never run two ticks concurrently
        coalesce=True,            # skip missed fires if a tick takes >10s
        replace_existing=True,
    )

    _scheduler.add_job(
        run_zombie_recovery,
        trigger="interval",
        minutes=5,
        id="zombie_recovery",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )

    _scheduler.start()
    logger.info(
        "Scheduler started — evaluation_tick every 10s, zombie_recovery every 5m"
    )


def stop_scheduler() -> None:
    """Gracefully stop the scheduler on application shutdown."""
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
