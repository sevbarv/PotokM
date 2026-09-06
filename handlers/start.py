from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from database.session import SessionLocal
from database.models.user import User
from database.models.enums import UserRole
from keyboards.mood import main_menu_kb, role_selection_kb
from states.mood import Registration

router = Router()


@router.message(F.text == "/start")
async def start_handler(message: Message, state: FSMContext):
    async with SessionLocal() as session:
        user = await session.scalar(
            User.__table__.select().where(User.telegram_id == message.from_user.id)
        )
    if user:
        await message.answer(
            f"С возвращением, {user.full_name or message.from_user.full_name}!",
            reply_markup=main_menu_kb(user.role.value),
        )
        await state.clear()
        return

    await message.answer(
        "Привет! Я HR-агент на основе открытого API «Потока».\n"
        "Давайте зарегистрируемся. Введите ваше ФИО:"
    )
    await state.set_state(Registration.waiting_full_name)


@router.message(Registration.waiting_full_name)
async def process_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer("Укажите вашу точку/отдел:")
    await state.set_state(Registration.waiting_department)


@router.message(Registration.waiting_department)
async def process_department(message: Message, state: FSMContext):
    await state.update_data(department=message.text)
    await message.answer(
        "Выберите вашу роль:\n"
        "— Я рекрутер\n"
        "— Я кандидат\n"
        "— Я сотрудник",
        reply_markup=role_selection_kb(),
    )
    await state.set_state(Registration.waiting_role)


@router.message(Registration.waiting_role)
async def process_role(message: Message, state: FSMContext):
    text = message.text.strip()
    role_map = {
        "Я рекрутер": UserRole.RECRUITER,
        "Я кандидат": UserRole.CANDIDATE,
        "Я сотрудник": UserRole.EMPLOYEE,
    }
    role = role_map.get(text)
    if not role:
        await message.answer("Пожалуйста, выберите роль кнопкой ниже.")
        return

    data = await state.get_data()
    async with SessionLocal() as session:
        user = User(
            telegram_id=message.from_user.id,
            username=message.from_user.username or str(message.from_user.id),
            full_name=data.get("full_name", message.from_user.full_name),
            department=data.get("department", ""),
            role=role,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    await state.clear()
    await message.answer(
        f"Регистрация завершена ✅\nДобро пожаловать, {user.full_name}!",
        reply_markup=main_menu_kb(user.role.value),
    )
