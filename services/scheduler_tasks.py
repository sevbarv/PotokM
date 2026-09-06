from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from aiogram import Bot
from sqlalchemy import select, and_
from database.session import SessionLocal
from database.models.user import User
from database.models.mood_log import MoodLog, MoodPeriod
from config.settings import settings


async def _get_candidates_to_notify(bot: Bot):
    now = datetime.now(TZ)
    today = now.date()
    async with SessionLocal() as session:
        users = (await session.scalars(select(User).where(User.role == "candidate"))).all()
    to_notify = []
    for user in users:
        last_log = await session.scalar(
            select(MoodLog)
            .where(and_(MoodLog.user_id == user.telegram_id, MoodLog.entity_type == "candidate"))
            .order_by(MoodLog.created_at.desc())
            .limit(1)
        )
        if last_log and (today - last_log.date).days < 3:
            continue
        to_notify.append(user)
    return to_notify


async def _get_employees_to_notify(period: MoodPeriod):
    now = datetime.now(TZ)
    today = now.date()
    async with SessionLocal() as session:
        users = (await session.scalars(select(User).where(User.role == "employee"))).all()
    to_notify = []
    for user in users:
        existing = await session.scalar(
            select(MoodLog.id).where(
                and_(
                    MoodLog.user_id == user.telegram_id,
                    MoodLog.period == period,
                    MoodLog.date == today,
                )
            )
        )
        if existing:
            continue
        to_notify.append(user)
    return to_notify


async def send_candidate_mood_request(bot: Bot):
    users = await _get_candidates_to_notify(bot)
    for user in users:
        try:
            await bot.send_message(
                user.telegram_id,
                "Напоминаем оценить настроение. Как вы себя чувствуете?",
                reply_markup=get_mood_keyboard("candidate"),
            )
        except Exception:
            pass


async def send_employee_morning_request(bot: Bot):
    users = await _get_employees_to_notify(MoodPeriod.MORNING)
    for user in users:
        try:
            await bot.send_message(
                user.telegram_id,
                "Доброе утро! Как вы себя чувствуете после ночи?",
                reply_markup=get_mood_keyboard("morning"),
            )
        except Exception:
            pass


async def send_employee_evening_request(bot: Bot):
    users = await _get_employees_to_notify(MoodPeriod.EVENING)
    for user in users:
        try:
            await bot.send_message(
                user.telegram_id,
                "Добрый вечер! Как вы себя чувствуете к концу дня?",
                reply_markup=get_mood_keyboard("evening"),
            )
        except Exception:
            pass


def get_mood_keyboard(period: str):
    from keyboards.mood import mood_keyboard
    return mood_keyboard(period)
