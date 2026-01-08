import asyncio
import logging

from config import bot, dp
from app.utils.logger import setup_logging
from app.handlers.main import setup_routers


logger = logging.getLogger(__name__)
setup_logging(debug=False)


async def main():
    routers = await setup_routers()
    for router in routers:
        dp.include_router(router)

    logger.info("Бот запущен")
    await run_bot()


async def run_bot():
    try:
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        logger.error(f"Ошибка при интерпретации: {e}")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Бот остановлен пользователем (Ctrl+C)")
    except Exception as e:
        logger.error(f"Бот выключен из-за ошибки:\n{e}")