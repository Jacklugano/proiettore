"""
Scheduler for automated video playback
"""
import logging
from datetime import datetime, time
from typing import List, Optional, Callable
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import sqlite3
from config import Config

logger = logging.getLogger(__name__)


class PlaybackScheduler:
    """Manages scheduled video playback"""

    def __init__(self, db_path: str = None):
        self.scheduler = BackgroundScheduler()
        self.db_path = db_path or Config.DATABASE_PATH
        self._init_database()

    def _init_database(self):
        """Initialize database for schedules"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS schedules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    video_path TEXT NOT NULL,
                    hour INTEGER NOT NULL,
                    minute INTEGER NOT NULL,
                    days_of_week TEXT,
                    enabled BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()
            conn.close()
            logger.info("Database initialized")

        except Exception as e:
            logger.error(f"Error initializing database: {e}")

    def start(self):
        """Start the scheduler"""
        try:
            if not self.scheduler.running:
                self.scheduler.start()
                logger.info("Scheduler started")
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")

    def stop(self):
        """Stop the scheduler"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                logger.info("Scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")

    def add_schedule(
        self,
        name: str,
        video_path: str,
        hour: int,
        minute: int,
        callback: Callable,
        days_of_week: Optional[str] = None
    ) -> Optional[int]:
        """
        Add a scheduled playback

        Args:
            name: Schedule name/description
            video_path: Path to video file
            hour: Hour (0-23)
            minute: Minute (0-59)
            callback: Function to call when schedule triggers
            days_of_week: Comma-separated days (mon,tue,wed,thu,fri,sat,sun) or None for daily

        Returns:
            Schedule ID or None if failed
        """
        try:
            # Save to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO schedules (name, video_path, hour, minute, days_of_week)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, video_path, hour, minute, days_of_week))

            schedule_id = cursor.lastrowid
            conn.commit()
            conn.close()

            # Add to scheduler
            self._add_job(schedule_id, video_path, hour, minute, callback, days_of_week)

            logger.info(f"Schedule added: {name} at {hour:02d}:{minute:02d}")
            return schedule_id

        except Exception as e:
            logger.error(f"Error adding schedule: {e}")
            return None

    def _add_job(
        self,
        schedule_id: int,
        video_path: str,
        hour: int,
        minute: int,
        callback: Callable,
        days_of_week: Optional[str] = None
    ):
        """Add job to APScheduler"""
        try:
            # Create cron trigger
            if days_of_week:
                trigger = CronTrigger(
                    day_of_week=days_of_week,
                    hour=hour,
                    minute=minute
                )
            else:
                trigger = CronTrigger(
                    hour=hour,
                    minute=minute
                )

            # Add job
            self.scheduler.add_job(
                func=callback,
                trigger=trigger,
                args=[video_path],
                id=f"schedule_{schedule_id}",
                replace_existing=True
            )

        except Exception as e:
            logger.error(f"Error adding job to scheduler: {e}")

    def remove_schedule(self, schedule_id: int) -> bool:
        """Remove a schedule"""
        try:
            # Remove from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('DELETE FROM schedules WHERE id = ?', (schedule_id,))
            conn.commit()
            conn.close()

            # Remove from scheduler
            try:
                self.scheduler.remove_job(f"schedule_{schedule_id}")
            except Exception:
                pass  # Job might not exist in scheduler

            logger.info(f"Schedule removed: {schedule_id}")
            return True

        except Exception as e:
            logger.error(f"Error removing schedule: {e}")
            return False

    def get_schedules(self) -> List[dict]:
        """Get all schedules"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM schedules ORDER BY hour, minute')
            rows = cursor.fetchall()
            conn.close()

            schedules = []
            for row in rows:
                schedules.append({
                    'id': row['id'],
                    'name': row['name'],
                    'video_path': row['video_path'],
                    'hour': row['hour'],
                    'minute': row['minute'],
                    'days_of_week': row['days_of_week'],
                    'enabled': bool(row['enabled']),
                    'created_at': row['created_at']
                })

            return schedules

        except Exception as e:
            logger.error(f"Error getting schedules: {e}")
            return []

    def toggle_schedule(self, schedule_id: int) -> bool:
        """Enable/disable a schedule"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                'SELECT enabled FROM schedules WHERE id = ?',
                (schedule_id,)
            )
            row = cursor.fetchone()

            if not row:
                conn.close()
                return False

            new_state = not bool(row[0])

            cursor.execute(
                'UPDATE schedules SET enabled = ? WHERE id = ?',
                (new_state, schedule_id)
            )
            conn.commit()
            conn.close()

            # Pause or resume job
            job_id = f"schedule_{schedule_id}"
            if new_state:
                self.scheduler.resume_job(job_id)
            else:
                self.scheduler.pause_job(job_id)

            logger.info(f"Schedule {schedule_id} {'enabled' if new_state else 'disabled'}")
            return True

        except Exception as e:
            logger.error(f"Error toggling schedule: {e}")
            return False

    def load_schedules(self, callback: Callable):
        """Load all schedules from database and add to scheduler"""
        try:
            schedules = self.get_schedules()

            for schedule in schedules:
                if schedule['enabled']:
                    self._add_job(
                        schedule['id'],
                        schedule['video_path'],
                        schedule['hour'],
                        schedule['minute'],
                        callback,
                        schedule['days_of_week']
                    )

            logger.info(f"Loaded {len(schedules)} schedules")

        except Exception as e:
            logger.error(f"Error loading schedules: {e}")
