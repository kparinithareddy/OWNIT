import asyncio
import logging
from datetime import datetime, timezone

from app.services.notification_service import notification_service

logger = logging.getLogger("ownit.scheduler")


class NotificationScheduler:
    """
    Lightweight AsyncIO background scheduler for local development and runtime reminders.
    Periodically checks warranty expiry dates and creates notifications without external dependencies.
    """
    def __init__(self, check_interval_seconds: int = 3600):
        self.check_interval = check_interval_seconds
        self._task: asyncio.Task = None
        self._is_running = False

    async def _run_loop(self):
        logger.info(f"Notification scheduler loop started (interval: {self.check_interval}s).")
        # Run an initial evaluation pass on startup
        try:
            res = await notification_service.evaluate_warranty_reminders()
            logger.info(f"Initial scheduler check complete: {res.newNotificationsCreated} new alerts created.")
        except Exception as e:
            logger.error(f"Error during initial notification evaluation: {e}")

        while self._is_running:
            try:
                await asyncio.sleep(self.check_interval)
                if not self._is_running:
                    break
                res = await notification_service.evaluate_warranty_reminders()
                logger.info(f"Periodic scheduler check complete: {res.newNotificationsCreated} new alerts created.")
            except asyncio.CancelledError:
                logger.info("Notification scheduler loop cancelled.")
                break
            except Exception as e:
                logger.error(f"Error during periodic notification check: {e}")

    def start(self):
        """Starts the background evaluation task."""
        if not self._is_running:
            self._is_running = True
            self._task = asyncio.create_task(self._run_loop())
            logger.info("Notification background scheduler task launched.")

    def stop(self):
        """Gracefully cancels and stops the background scheduler task."""
        if self._is_running:
            self._is_running = False
            if self._task and not self._task.done():
                self._task.cancel()
            logger.info("Notification background scheduler task stopped.")


notification_scheduler = NotificationScheduler(check_interval_seconds=3600)
