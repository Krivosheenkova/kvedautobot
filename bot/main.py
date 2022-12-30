from datetime import datetime
import logging 
 
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from bot.filters import register_all_filters
from bot.misc import TgKeys, WorkChat
from bot.handlers import register_all_handlers
from bot.database.models import register_models
from bot.misc.scrap_ym import main as monitor
from bot.misc.scrap_adstats import main as scrap_adstats
from bot.misc.util import set_commands

async def send_message_cron(bot: Bot):
    await bot.send_message(chat_id=WorkChat.ID, text=monitor(), parse_mode=ParseMode.MARKDOWN)


async def __on_start_up(dp: Dispatcher) -> None:
    register_all_filters(dp)
    register_all_handlers(dp)
    register_models()


def start_bot():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - [%(levelname)s] -  %(name)s - "
                               "(%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
                        )
    bot = Bot(token=TgKeys.TOKEN, parse_mode='HTML')
    set_commands(bot)
    dp = Dispatcher(bot, storage=MemoryStorage())

    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(send_message_cron, trigger='cron', hour=10,
                      minute=00, start_date=datetime.now(), kwargs={'bot': bot})
    scheduler.add_job(scrap_adstats, trigger='cron', 
                      year='*', month='*', day='last', 
                    #   next_run_time=datetime.now()
                      )
    
    scheduler.start()

    executor.start_polling(dp, skip_updates=True, on_startup=__on_start_up)
