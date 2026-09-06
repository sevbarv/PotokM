import asyncio
from loader import dp, bot
from scheduler.setup import setup_scheduler
from utils.logging import logger
from database.base import engine
from database.models import Base


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def main():
    await init_db()
    setup_scheduler(bot)
    logger.info("HR Agent started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
