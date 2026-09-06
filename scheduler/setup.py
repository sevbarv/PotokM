from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from services.scheduler_tasks import (
    send_candidate_mood_request,
    send_employee_morning_request,
    send_employee_evening_request,
)
from services.ai_service import run_daily_analysis
from config.settings import settings

scheduler = AsyncIOScheduler(timezone=settings.TIMEZONE)


def setup_scheduler(bot: Bot):
    scheduler.add_job(send_candidate_mood_request, "cron", hour=12, minute=0, args=[bot])
    scheduler.add_job(send_employee_morning_request, "cron", hour=10, minute=0, args=[bot])
    scheduler.add_job(send_employee_evening_request, "cron", hour=17, minute=0, args=[bot])
    scheduler.add_job(run_daily_analysis, "cron", hour=9, minute=30, args=[bot])
    scheduler.start()
