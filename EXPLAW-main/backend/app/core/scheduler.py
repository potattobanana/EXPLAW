"""
Stage 1: scheduled trigger. Runs the same check as the manual
'check now' button, once a day.
"""

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import settings
from app.services import change_service

_scheduler = BackgroundScheduler()


def run_daily_check():
    change_service.run_check()


def start_scheduler():
    _scheduler.add_job(
        run_daily_check,
        "cron",
        hour=settings.scrape_cron_hour,
        minute=settings.scrape_cron_minute,
    )
    _scheduler.start()
