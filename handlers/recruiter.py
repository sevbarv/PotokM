from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database.session import SessionLocal
from database.models.user import User
from database.models.mood_log import MoodLog
from utils.zones import ZONE_LABELS
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


@router.message(F.text == "Профиль")
async def profile(message: Message):
    async with SessionLocal() as session:
        user = await session.scalar(
            User.__table__.select().where(User.telegram_id == message.from_user.id)
        )
    if not user:
        await message.answer("Пользователь не найден. Зарегистрируйтесь через /start")
        return
    latest = None
    async with SessionLocal() as session:
        latest = await session.scalar(
            MoodLog.__table__.select()
            .where(MoodLog.user_id == message.from_user.id)
            .order_by(MoodLog.created_at.desc())
            .limit(1)
        )
    text = f"ФИО: {user.full_name}\nТТ/Отдел: {user.department}\nРоль: {user.role.value}\n"
    if latest:
        zone = ZONE_LABELS.get(latest.ai_zone.value, "—") if latest.ai_zone else "—"
        text += f"Последнее настроение: {latest.reaction} ({latest.period})\nЗаметка: {latest.note or '—'}\nЗона: {zone}\n"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Показать детали", callback_data=f"mood_detail:{latest.id}")]
        ])
    else:
        kb = None
    await message.answer(text, reply_markup=kb)


def get_main_menu(role: str):
    from keyboards.mood import main_menu_kb
    return main_menu_kb(role)


@router.message(F.text == "О проекте")
async def about(message: Message):
    await message.answer(
        "HR-агент на основе открытого API «Потока».\n"
        "Трекер настроений с AI-анализом заметок, цветовыми зонами и рекомендациями.\n"
        "Лицензия MIT. Воспроизводимость: подключите .env и запустите docker-compose up."
    )


@router.callback_query(F.data.startswith("mood_detail:"))
async def mood_detail(callback: CallbackQuery):
    log_id = int(callback.data.split(":")[1])
    async with SessionLocal() as session:
        log = await session.get(MoodLog, log_id)
    if not log:
        await callback.message.answer("Запись не найдена.")
        await callback.answer()
        return
    zone = ZONE_LABELS.get(log.ai_zone.value, "—") if log.ai_zone else "—"
    text = (
        f"Дата: {log.date} {log.time}\n"
        f"Период: {log.period}\n"
        f"Реакция: {log.reaction}\n"
        f"Заметка: {log.note or '—'}\n"
        f"Зона: {zone}\n"
    )
    if log.ai_recommendation:
        text += f"Рекомендация: {log.ai_recommendation}\n"
    await callback.message.answer(text)
    await callback.answer()


@router.message(F.text == "Карточки кандидатов")
async def recruiter_candidates(message: Message):
    from potok_api.client import PotokClient
    client = PotokClient()
    try:
        data = await client.get_applicants()
        items = data.get("data", [])
        if not items:
            await message.answer("Кандидатов пока нет.")
            return
        text = "Кандидаты:\n" + "\n".join([f"- {i.get('full_name', 'N/A')} (ID {i.get('id')})" for i in items[:10]])
        await message.answer(text)
    except Exception as e:
        await message.answer(f"Ошибка подключения к Потоку: {e}")


@router.message(F.text == "Карточки сотрудников")
async def recruiter_employees(message: Message):
    from potok_api.client import PotokClient
    client = PotokClient()
    try:
        data = await client.get_employees()
        items = data if isinstance(data, list) else data.get("data", [])
        if not items:
            await message.answer("Сотрудников пока нет.")
            return
        text = "Сотрудники:\n" + "\n".join([f"- {i.get('full_name', 'N/A')} (ID {i.get('id')})" for i in items[:10]])
        await message.answer(text)
    except Exception as e:
        await message.answer(f"Ошибка подключения к Потоку: {e}")


@router.message(F.text == "Уведомления")
async def recruiter_notifications(message: Message):
    from services.ai_service import get_orange_red_entities
    data = await get_orange_red_entities()
    if not data:
        await message.answer("Нет уведомлений за последний месяц.")
        return
    lines = ["Уведомления за месяц:\n"]
    for key, entries in data.items():
        lines.append(f"{key}: {len(entries)} записей в оранжевой/красной зоне")
    await message.answer("\n".join(lines))
