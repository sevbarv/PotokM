import random
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from database.session import SessionLocal
from database.models.user import User
from database.models.mood_log import MoodLog, MoodPeriod
from keyboards.mood import main_menu_kb, mood_keyboard, note_keyboard
from states.mood import MoodNote
from services.mood_service import save_mood_log
from services.ai_service import analyze_and_update_log
from services.potok_sync import sync_mood_to_potok
from config.settings import settings

router = Router()

EMOTION_PHRASES = {
    "🤩": ["Отличное настроение! Продолжайте в том же духе."],
    "🙂": ["Хорошее состояние — это уже успех."],
    "😐": ["Нормально. Следите за собой."],
    "😔": ["Похоже, сейчас непросто. Спасибо, что отметили это."],
    "😭": ["Нам жаль, что вам плохо. Мы рядом."],
}


def get_random_phrase(mood: str) -> str:
    return random.choice(EMOTION_PHRASES.get(mood, ["Спасибо за оценку!"]))


async def _ask_mood(message: Message, state: FSMContext, period: str, entity_type: str):
    async with SessionLocal() as session:
        user = await session.scalar(
            User.__table__.select().where(User.telegram_id == message.from_user.id)
        )
    await state.update_data(period=period, entity_type=entity_type)
    period_text = {
        "morning": "утро", "evening": "вечер", "candidate": "настроение"
    }.get(period, period)
    await message.answer(
        f"Как вы себя чувствуете ({period_text})?",
        reply_markup=mood_keyboard(period),
    )


@router.message(F.text == "Оценить настроение")
async def candidate_mood(message: Message, state: FSMContext):
    await _ask_mood(message, state, "candidate", "candidate")


@router.message(F.text == "Оценить утро")
async def employee_morning(message: Message, state: FSMContext):
    await _ask_mood(message, state, "morning", "employee")


@router.message(F.text == "Оценить вечер")
async def employee_evening(message: Message, state: FSMContext):
    await _ask_mood(message, state, "evening", "employee")


@router.message(F.text.in_(["🤩", "🙂", "😐", "😔", "😭"]))
async def process_mood(message: Message, state: FSMContext):
    data = await state.get_data()
    period = data.get("period")
    entity_type = data.get("entity_type", "employee")
    if not period:
        from datetime import datetime
        from zoneinfo import ZoneInfo
        hour = datetime.now(ZoneInfo(settings.TIMEZONE)).hour
        period = "morning" if hour < 12 else "evening"
    mood = message.text
    phrase = get_random_phrase(mood)
    await state.update_data(mood=mood, period=period, entity_type=entity_type)
    await message.answer(
        f"{mood} {phrase}\n\nХотите добавить заметку?",
        reply_markup=note_keyboard(),
    )


@router.message(F.text == "Да, хочу добавить")
async def process_note_yes(message: Message, state: FSMContext):
    await message.answer("Напишите заметку о своём состоянии:", reply_markup=None)
    await state.set_state(MoodNote.waiting_for_note)


@router.message(F.text == "Пока не хочется")
async def process_note_no(message: Message, state: FSMContext):
    data = await state.get_data()
    mood = data.get("mood")
    period = data.get("period")
    entity_type = data.get("entity_type", "employee")
    if not mood or not period:
        await state.clear()
        return
    log = await save_mood_log(message.from_user.id, entity_type, mood, MoodPeriod(period), None)
    await message.answer("Спасибо! Записали ✅", reply_markup=main_menu_kb("user"))
    await state.clear()


@router.message(F.text == "Изменить реакцию")
async def process_change_reaction(message: Message, state: FSMContext):
    data = await state.get_data()
    period = data.get("period")
    entity_type = data.get("entity_type", "employee")
    await state.update_data(mood=None)
    await message.answer("Как вы себя чувствуете?", reply_markup=mood_keyboard(period))


@router.message(MoodNote.waiting_for_note)
async def process_note_text(message: Message, state: FSMContext):
    from middlewares.role_check import get_user_by_tg_id
    data = await state.get_data()
    mood = data.get("mood")
    period = data.get("period")
    entity_type = data.get("entity_type", "employee")
    note = message.text.strip()
    if not mood or not period:
        await state.clear()
        return
    log = await save_mood_log(message.from_user.id, entity_type, mood, MoodPeriod(period), note)
    await analyze_and_update_log(log.id, mood, note)
    await session_get_latest_and_sync(message.from_user.id)
    user = await get_user_by_tg_id(message.from_user.id)
    role = user.role.value if user else "user"
    await message.answer("Спасибо за заметку! Записали ✅", reply_markup=main_menu_kb(role))
    await state.clear()


async def session_get_latest_and_sync(telegram_id: int):
    async with SessionLocal() as session:
        log = await session.scalar(
            select(MoodLog)
            .where(MoodLog.user_id == telegram_id)
            .order_by(MoodLog.created_at.desc())
            .limit(1)
        )
        if log:
            await session.refresh(log)
            await sync_mood_to_potok(telegram_id, log)
