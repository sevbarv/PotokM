from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_kb(role: str) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="Профиль"), KeyboardButton(text="О проекте")],
    ]
    if role == "recruiter":
        buttons.append([KeyboardButton(text="Карточки кандидатов"), KeyboardButton(text="Карточки сотрудников")])
        buttons.append([KeyboardButton(text="Уведомления")])
    elif role == "candidate":
        buttons.append([KeyboardButton(text="Оценить настроение")])
    elif role == "employee":
        buttons.append([KeyboardButton(text="Оценить утро"), KeyboardButton(text="Оценить вечер")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def mood_keyboard(period: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🤩"), KeyboardButton(text="🙂")],
            [KeyboardButton(text="😐")],
            [KeyboardButton(text="😔"), KeyboardButton(text="😭")],
            [KeyboardButton(text="Главное меню")],
        ],
        resize_keyboard=True,
    )


def note_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Да, хочу добавить"), KeyboardButton(text="Пока не хочется")],
            [KeyboardButton(text="Изменить реакцию")],
            [KeyboardButton(text="Главное меню")],
        ],
        resize_keyboard=True,
    )


def role_selection_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Я рекрутер"), KeyboardButton(text="Я кандидат")],
            [KeyboardButton(text="Я сотрудник")],
        ],
        resize_keyboard=True,
    )
