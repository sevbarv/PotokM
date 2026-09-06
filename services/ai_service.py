from sqlalchemy import select
from database.session import SessionLocal
from database.models.user import User
from database.models.mood_log import MoodLog, MoodPeriod, AIZone
from ai_client.analyzer import AIAnalyzer
from utils.zones import SUSPICIOUS_WORDS, ZONE_LABELS
import logging
import re

logger = logging.getLogger(__name__)
ai_analyzer = AIAnalyzer()


def _detect_zone_keywords(note: str) -> str | None:
    if not note:
        return None
    lower = note.lower()
    words = re.findall(r"[а-яa-z]+", lower)
    count = sum(1 for w in words if w in SUSPICIOUS_WORDS)
    if count >= 3:
        return "red"
    if count >= 1:
        return "orange"
    return None


async def analyze_and_update_log(log_id: int, reaction: str, note: str):
    keyword_zone = _detect_zone_keywords(note)
    ai_result = await ai_analyzer.analyze_note(note or "", reaction)

    zone = ai_result.get("zone", "green")
    if keyword_zone == "red":
        zone = "red"
    elif keyword_zone == "orange" and zone != "red":
        zone = "orange"

    async with SessionLocal() as session:
        log = await session.get(MoodLog, log_id)
        if not log:
            return
        log.ai_zone = AIZone(zone)
        log.ai_recommendation = ai_result.get("recommendation", "")
        await session.commit()


async def run_daily_analysis(bot):
    from services.mood_service import get_orange_red_entities, get_recruiters_ids
    data = await get_orange_red_entities()
    if not data:
        return
    recruiters = await get_recruiters_ids()
    if not recruiters:
        return
    lines = ["⚠️ Анализ настроений за последний месяц:\n"]
    for key, entries in data.items():
        entity_type, user_id = key.split(":")
        user = await get_user_by_tg_id(int(user_id))
        name = user.full_name if user else f"ID {user_id}"
        lines.append(f"👤 {name} ({entity_type})")
        for e in entries:
            zone_label = ZONE_LABELS.get(e["zone"], e["zone"])
            lines.append(f"- {e['date']}: {zone_label} — {e['note'] or 'без заметки'}")
        lines.append("")
    text = "\n".join(lines)
    for rid in recruiters:
        try:
            await bot.send_message(rid, text)
        except Exception:
            pass


async def get_user_by_tg_id(telegram_id: int):
    async with SessionLocal() as session:
        return await session.scalar(select(User).where(User.telegram_id == telegram_id))
