from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from sqlalchemy import select, func, and_
from database.session import SessionLocal
from database.models.user import User
from database.models.mood_log import MoodLog, MoodPeriod, AIZone
from utils.zones import ZONE_LABELS
from config.settings import settings


async def save_mood_log(telegram_id: int, entity_type: str, reaction: str, period: MoodPeriod, note: str = None) -> MoodLog:
    async with SessionLocal() as session:
        user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
        if not user:
            raise ValueError("User not found")
        tz = ZoneInfo(settings.TIMEZONE)
        now = datetime.now(tz)
        log = MoodLog(
            user_id=telegram_id,
            entity_type=entity_type,
            reaction=reaction,
            period=period,
            date=now.date(),
            time=now.strftime("%H:%M"),
            note=note,
        )
        session.add(log)
        await session.commit()
        await session.refresh(log)
        return log


async def get_user_latest_mood(telegram_id: int) -> MoodLog | None:
    async with SessionLocal() as session:
        result = await session.scalar(
            select(MoodLog)
            .where(MoodLog.user_id == telegram_id)
            .order_by(MoodLog.created_at.desc())
            .limit(1)
        )
        return result


async def get_user_month_moods(telegram_id: int, entity_type: str = None) -> list[MoodLog]:
    month_ago = date.today() - timedelta(days=30)
    async with SessionLocal() as session:
        query = select(MoodLog).where(
            and_(MoodLog.user_id == telegram_id, MoodLog.date >= month_ago)
        )
        if entity_type:
            query = query.where(MoodLog.entity_type == entity_type)
        query = query.order_by(MoodLog.created_at.desc())
        result = await session.scalars(query)
        return list(result.all())


async def get_orange_red_entities(period_days: int = 30) -> dict[str, list[dict]]:
    cutoff = date.today() - timedelta(days=period_days)
    async with SessionLocal() as session:
        result = await session.execute(
            select(MoodLog)
            .where(
                and_(
                    MoodLog.date >= cutoff,
                    MoodLog.ai_zone.in_([AIZone.ORANGE, AIZone.RED]),
                )
            )
            .order_by(MoodLog.created_at.desc())
        )
        logs = result.scalars().all()

    by_entity: dict[str, list[dict]] = {}
    for log in logs:
        key = f"{log.entity_type}:{log.user_id}"
        by_entity.setdefault(key, []).append({
            "id": log.id,
            "reaction": log.reaction,
            "note": log.note,
            "zone": log.ai_zone.value if log.ai_zone else None,
            "recommendation": log.ai_recommendation,
            "date": log.date.isoformat(),
        })
    return by_entity


async def get_recruiters_ids() -> list[int]:
    async with SessionLocal() as session:
        result = await session.scalars(select(User.telegram_id).where(User.role == "recruiter"))
        return list(result.all())
