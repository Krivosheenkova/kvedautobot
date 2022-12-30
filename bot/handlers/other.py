import os

from aiogram import Dispatcher
from aiogram.types import Message, ParseMode, MediaGroup, InputMediaDocument
from bot.misc.scrap_ym import main as monitor
from bot.misc.post_video import post_video
from bot.misc.scrap_adstats import main as scrap_adstats
from bot.keyboards.reply import adstats_keyboard_markup
from bot.misc import AdstatsKeys
from bot.misc.util import clear_folder

async def send_monitor(message: Message):
    await message.answer(monitor(), parse_mode=ParseMode.MARKDOWN)

async def send_post_selchas(message: Message):
    await message.answer(post_video())

async def send_adstats(message: Message):
    drafts = message.get_args()
    if drafts is None: drafts = False
    elif drafts.__contains__('draft') or drafts.__contains__('черновик'):
        drafts = True
    else: drafts = False

    reply_markup = adstats_keyboard_markup(links=scrap_adstats(update=True, drafts=drafts))
    await message.answer('AdvancedAds statistics', reply_markup=reply_markup)

async def send_adstats_pdf(message: Message):
    path = AdstatsKeys.ADSTATS_PATH
    files = [os.path.join(path, file) for file in os.listdir(path)]
    for file in files:
        if os.path.isfile(file) and file[-3:] == 'pdf':
            media_group = MediaGroup()
            media_group.attach(InputMediaDocument(open(file, 'rb')))
            await message.reply_media_group(media=media_group, reply=False, disable_notification=True)

async def clear_scrapped_adstats(message: Message):
    path = AdstatsKeys.ADSTATS_PATH
    try:
        clear_folder(path)
    except Exception as e:
        await message.reply(str(e))
    await message.reply(f'{path} successfully cleared')

def register_other_handlers(dp: Dispatcher) -> None:
    # todo: register all other handlers
    # dp.register_message_handler(echo, content_types=['text'])
    dp.register_message_handler(send_monitor, commands=["monitor"])
    dp.register_message_handler(send_post_selchas, commands=["seload"])
    dp.register_message_handler(send_adstats, commands=["adstats"])
    dp.register_message_handler(send_adstats_pdf, commands=["adstats_pdf"])
    dp.register_message_handler(clear_scrapped_adstats, commands=["casf"])