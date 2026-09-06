from aiogram import Router, F
from aiogram.types import Message
from database.session import SessionLocal
from database.models.mood_log import MoodLog
from services.mood_service import get_user_month_moods
from utils.zones import ZONE_LABELS

router = Router()


@router.message(F.text == "Мои оценки")
async def my_ratings(message: Message):
    logs = await get_user_month_moods(message.from_user.id)
    if not logs:
        await message.answer("Нет оценок за месяц.")
        return
    lines = ["Мои оценки за месяц:\n"]
    for log in logs:
        zone = ZONE_LABELS.get(log.ai_zone.value, "—") if log.ai_zone else "—"
        lines.append(f"{log.date} {log.period}: {log.reaction} — {zone}")
    await message.answer("\n".join(lines))


@router.message(F.text == "Последнее настроение")
async def last_mood(message: Message):
    async with SessionLocal() as session:
        latest = await session.scalar(
            MoodLog.__table__.select()
            .where(MoodLog.user_id == message.from_user.id)
            .order_by(MoodLog.created_at.desc())
            .limit(1)
        )
    if not latest:
        await message.answer("Вы ещё не оценивали настроение.")
        return
    zone = ZONE_LABELS.get(latest.ai_zone.value, "—") if latest.ai_zone else "—"
    text = (
        f"Последнее настроение: {latest.reaction}\n"
        f"Период: {latest.period}\n"
        f"Заметка: {latest.note or '—'}\n"
        f"Зона: {zone}\n"
    )
    if latest.ai_recommendation:
        text += f"Рекомендация: {latest.ai_recommendation}\n"
    await message.answer(text)
