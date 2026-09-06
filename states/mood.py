from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    waiting_full_name = State()
    waiting_department = State()
    waiting_role = State()


class MoodNote(StatesGroup):
    waiting_for_note = State()
