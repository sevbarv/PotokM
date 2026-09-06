from aiogram.filters import BaseFilter
from aiogram.types import Message
from sqlalchemy import select
from database.session import SessionLocal
from database.models import User
from database.models.enums import UserRole


class RoleFilter(BaseFilter):
    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles

    async def __call__(self, message: Message) -> bool:
        async with SessionLocal() as session:
            user = await session.scalar(
                select(User).where(User.telegram_id == message.from_user.id)
            )
        if not user:
            return False
        return user.role in self.allowed_roles


async def get_user_by_tg_id(telegram_id: int):
    async with SessionLocal() as session:
        return await session.scalar(select(User).where(User.telegram_id == telegram_id))
