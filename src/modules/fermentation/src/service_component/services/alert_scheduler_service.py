"""
Alert Scheduler Service (ADR-040 Phase 4)

Background job that runs every 30 minutes and scans all ACTIVE protocol
executions to generate time-based alerts automatically:

  STEP_OVERDUE    — step's tolerance window has passed and it is not completed
  STEP_DUE_SOON   — step is due within the next 12 hours

Duplicate-alert guard: a new alert for the same (execution, step, type) is
suppressed if a non-dismissed alert already exists for that combination,
preventing spam across scheduler runs.

Wire-up:
    Call ``AlertSchedulerService.start()`` on FastAPI startup
    and ``AlertSchedulerService.stop()`` on shutdown.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.shared.wine_fermentator_logging import get_logger
from src.modules.fermentation.src.domain.entities.protocol_alert import ProtocolAlert
from src.modules.fermentation.src.domain.entities.protocol_execution import ProtocolExecution
from src.modules.fermentation.src.domain.entities.protocol_step import ProtocolStep
from src.modules.fermentation.src.domain.entities.step_completion import StepCompletion
from src.modules.fermentation.src.domain.enums.step_type import ProtocolExecutionStatus

logger = get_logger(__name__)

# How far ahead to warn about approaching steps
_APPROACHING_HOURS = 12

# Suppress duplicate alert for the same (execution, step, type) for this window
_DEDUP_HOURS = 6


class AlertSchedulerService:
    """
    Asyncio-compatible background scheduler that auto-generates protocol alerts.

    Creates one ProtocolAlert row per alert event; the existing alert API
    (alert_router.py) exposes these to the frontend for display/acknowledge.
    """

    def __init__(self, database_url: str, interval_minutes: int = 30) -> None:
        """
        Args:
            database_url:      Async DB URL  (``postgresql+asyncpg://...``)
            interval_minutes:  How often the scan runs (default 30 min).
        """
        self._db_url = database_url
        self._interval = interval_minutes
        self._scheduler = AsyncIOScheduler()

    # ─── Lifecycle ──────────────────────────────────────────────────────────

    def start(self) -> None:
        """Register the job and start the scheduler (call on FastAPI startup)."""
        self._scheduler.add_job(
            self._scan_all_executions,
            trigger="interval",
            minutes=self._interval,
            id="alert_scan",
            replace_existing=True,
            coalesce=True,          # skip missed runs; don't pile up
            max_instances=1,
        )
        self._scheduler.start()
        logger.info(
            "alert_scheduler_started",
            interval_minutes=self._interval,
        )

    def stop(self) -> None:
        """Shutdown the scheduler cleanly (call on FastAPI shutdown)."""
        self._scheduler.shutdown(wait=False)
        logger.info("alert_scheduler_stopped")

    # ─── Main scan ──────────────────────────────────────────────────────────

    async def _scan_all_executions(self) -> None:
        """
        Main job body: open a short-lived DB session, find all ACTIVE
        executions, and generate alerts for each one.
        """
        engine = create_async_engine(self._db_url, pool_pre_ping=True)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        try:
            async with async_session() as session:
                async with session.begin():
                    executions = await self._get_active_executions(session)
                    logger.info(
                        "alert_scan_started",
                        active_executions=len(executions),
                    )

                    total_created = 0
                    for execution in executions:
                        created = await self._process_execution(session, execution)
                        total_created += created

                    logger.info(
                        "alert_scan_completed",
                        active_executions=len(executions),
                        alerts_created=total_created,
                    )
        except Exception as exc:
            logger.error("alert_scan_failed", error=str(exc))
        finally:
            await engine.dispose()

    # ─── Per-execution logic ─────────────────────────────────────────────────

    async def _process_execution(
        self, session: AsyncSession, execution: ProtocolExecution
    ) -> int:
        """
        Check one execution and create alerts for overdue / approaching steps.

        Returns number of alerts created.
        """
        # All steps for this protocol
        steps_result = await session.execute(
            select(ProtocolStep)
            .where(ProtocolStep.protocol_id == execution.protocol_id)
            .order_by(ProtocolStep.step_order)
        )
        steps: List[ProtocolStep] = list(steps_result.scalars().all())

        # Set of step IDs that are already completed or skipped
        completions_result = await session.execute(
            select(StepCompletion.step_id)
            .where(StepCompletion.execution_id == execution.id)
        )
        completed_step_ids = set(completions_result.scalars().all())

        now = datetime.utcnow()
        alerts_created = 0

        for step in steps:
            if step.id in completed_step_ids:
                continue  # already done

            # Window: execution.start_date + expected_day ± tolerance_hours
            due_at = execution.start_date + timedelta(
                days=step.expected_day,
                hours=step.tolerance_hours,
            )
            approaching_at = due_at - timedelta(hours=_APPROACHING_HOURS)

            if now >= due_at:
                # OVERDUE
                created = await self._maybe_create_alert(
                    session=session,
                    execution=execution,
                    step=step,
                    alert_type="STEP_OVERDUE",
                    severity="CRITICAL" if step.is_critical else "WARNING",
                    message=(
                        f"Step '{step.description}' is overdue "
                        f"(was due {due_at.strftime('%Y-%m-%d %H:%M')} UTC)."
                    ),
                )
                alerts_created += created

            elif now >= approaching_at:
                # DUE SOON
                hours_left = round((due_at - now).total_seconds() / 3600, 1)
                created = await self._maybe_create_alert(
                    session=session,
                    execution=execution,
                    step=step,
                    alert_type="STEP_DUE_SOON",
                    severity="WARNING" if step.is_critical else "INFO",
                    message=(
                        f"Step '{step.description}' is due in "
                        f"{hours_left}h "
                        f"(deadline {due_at.strftime('%Y-%m-%d %H:%M')} UTC)."
                    ),
                )
                alerts_created += created

        return alerts_created

    # ─── Dedup + persist ────────────────────────────────────────────────────

    async def _maybe_create_alert(
        self,
        session: AsyncSession,
        execution: ProtocolExecution,
        step: ProtocolStep,
        alert_type: str,
        severity: str,
        message: str,
    ) -> int:
        """
        Create a ProtocolAlert only if no non-dismissed alert with the same
        (execution_id, step_id, alert_type) exists within the dedup window.

        Returns 1 if alert was created, 0 if suppressed.
        """
        dedup_since = datetime.utcnow() - timedelta(hours=_DEDUP_HOURS)

        existing = await session.execute(
            select(ProtocolAlert.id).where(
                and_(
                    ProtocolAlert.execution_id == execution.id,
                    ProtocolAlert.step_id == step.id,
                    ProtocolAlert.alert_type == alert_type,
                    ProtocolAlert.status != "DISMISSED",
                    ProtocolAlert.created_at >= dedup_since,
                )
            ).limit(1)
        )
        if existing.scalar_one_or_none() is not None:
            return 0  # already alerted recently

        alert = ProtocolAlert(
            execution_id=execution.id,
            protocol_id=execution.protocol_id,
            winery_id=execution.winery_id,
            step_id=step.id,
            step_name=step.description,
            alert_type=alert_type,
            severity=severity,
            status="PENDING",
            message=message,
            created_at=datetime.utcnow(),
        )
        session.add(alert)
        # flush happens at the enclosing begin() commit

        logger.info(
            "alert_created",
            execution_id=execution.id,
            step_id=step.id,
            alert_type=alert_type,
            severity=severity,
        )
        return 1

    # ─── Helpers ────────────────────────────────────────────────────────────

    @staticmethod
    async def _get_active_executions(
        session: AsyncSession,
    ) -> List[ProtocolExecution]:
        """Return all ACTIVE protocol executions."""
        result = await session.execute(
            select(ProtocolExecution).where(
                ProtocolExecution.status == ProtocolExecutionStatus.ACTIVE.value
            )
        )
        return list(result.scalars().all())
