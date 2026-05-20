"""
EvaluationWorker — background job that processes pending evaluation jobs.

Schedule (via APScheduler in scheduler.py):
  - run_evaluation_tick()  every 10 seconds — claims and processes one PENDING job
  - recover_zombie_jobs()  every 5 minutes  — resets stuck PROCESSING jobs to PENDING

Design decisions:
  - Each tick claims exactly one job (SELECT ... FOR UPDATE SKIP LOCKED)
  - Idempotency: if the session was already analyzed (ConflictException from service),
    the worker marks the job COMPLETED rather than FAILED
  - Worker uses its own DB session (not the request-scoped session)
  - All failures are caught; the job is marked FAILED with backoff
  - Zombie recovery is separate from the main tick to keep error surfaces isolated

Matches NestJS: apps/backend/src/modules/evaluation-job/evaluation-job.service.ts (worker logic)
"""
import logging
import uuid

from app.db.session import SessionLocal
from app.modules.evaluation import repository as eval_repo
from app.modules.evaluation import service as eval_service

logger = logging.getLogger(__name__)


async def run_evaluation_tick() -> None:
    """
    Called every 10 seconds by the APScheduler.
    Claims one PENDING job, runs evaluation, marks it COMPLETED or FAILED.
    """
    async with SessionLocal() as db:
        try:
            job = await eval_repo.claim_next_pending_job(db)
            if job is None:
                return  # nothing to process right now

            session_id: uuid.UUID = job.session_id
            job_id: uuid.UUID = job.id
            logger.info("EvaluationWorker: processing job %s for session %s", job_id, session_id)

            try:
                await eval_service.analyze_session_internal(db, session_id)
                await eval_repo.mark_job_completed(db, job_id)
                await db.commit()
                logger.info("EvaluationWorker: job %s COMPLETED", job_id)

            except Exception as exc:
                # Idempotency: ConflictException means evaluation already exists
                # (worker crashed after report was saved but before markCompleted).
                # Mark COMPLETED rather than retrying.
                from app.core.exceptions import ConflictException
                if isinstance(exc, ConflictException):
                    logger.warning(
                        "EvaluationWorker: job %s — evaluation already exists, marking COMPLETED",
                        job_id,
                    )
                    await db.rollback()
                    async with SessionLocal() as fix_db:
                        await eval_repo.mark_job_completed(fix_db, job_id)
                        await fix_db.commit()
                    return

                # All other errors → mark failed with backoff
                error_msg = str(exc)
                logger.error(
                    "EvaluationWorker: job %s FAILED — %s", job_id, error_msg
                )
                await db.rollback()
                async with SessionLocal() as fail_db:
                    await eval_repo.mark_job_failed(fail_db, job_id, error_msg)
                    await fail_db.commit()

        except Exception as exc:
            # Errors claiming the job itself (rare DB issues)
            logger.error("EvaluationWorker: unexpected error in tick — %s", exc)
            try:
                await db.rollback()
            except Exception:
                pass


async def run_zombie_recovery() -> None:
    """
    Called every 5 minutes by the APScheduler.
    Resets PROCESSING jobs that have been stuck for >10 minutes.
    """
    async with SessionLocal() as db:
        try:
            count = await eval_repo.recover_zombie_jobs(db)
            await db.commit()
            if count > 0:
                logger.warning("Zombie recovery: reset %d job(s)", count)
        except Exception as exc:
            logger.error("Zombie recovery failed: %s", exc)
            await db.rollback()
