from aiogram import executor
# https://docs.aiogram.dev/en/latest/index.html
# https://core.telegram.org/bots/api

from loader import dp
from handlers import all_handlers
from logs.log_info import logger


async def startup(dp):  # диспатчер не убрать. Полинг передаёт.
    await all_handlers.send_to_admin()


async def shutdown(dp):
    await all_handlers.send_to_admin_end()


if __name__ == '__main__':
    try:
        logger.info(f'\n{80*"="}\nБот запущен')
        executor.start_polling(dp, on_startup=startup, on_shutdown=shutdown)
        logger.info(f'\n{80 * "="}\nБот оффлайн')
    except Exception as ex:
        logger.debug(str(ex))
        logger.exception(str(ex))
