from datetime import date, datetime
from zoneinfo import ZoneInfo
from sqlalchemy import select
from database.session import SessionLocal
from database.models.mood_log import MoodLog, MoodPeriod
from database.models.user import User
from potok_api.client import PotokClient
from config.settings import settings
from middlewares.role_check import get_user_by_tg_id

potok_client = PotokClient()


async def sync_mood_to_potok(telegram_id: int, log: MoodLog):
    if not log.note or not log.ai_zone:
        return
    user = await get_user_by_tg_id(telegram_id)
    if not user or not user.potok_entity_id:
        return
    entity_type = "candidate" if log.entity_type == "candidate" else "employee"
    try:
        if entity_type == "candidate":
            await potok_client.add_applicant_note(
                int(user.potok_entity_id),
                f"[AI-{log.ai_zone.value.upper()}] {log.note} | Рекомендация: {log.ai_recommendation}",
            )
        else:
            await potok_client.create_notification(
                entity_type="employee",
                entity_id=int(user.potok_entity_id),
                message=f"Настроение: {log.reaction} ({log.period}) — {log.note}",
            )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to sync to Potok: {e}")
