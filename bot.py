from aiogram import Bot, Dispatcher
from config.settings import settings
from handlers import routers

if not settings.BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

for router in routers:
    dp.include_router(router)
