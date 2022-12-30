from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def adstats_keyboard_markup(links: dict) -> ReplyKeyboardMarkup:
    reply_markup = InlineKeyboardMarkup()

    for title,link in links.items():
        reply_markup.add(InlineKeyboardButton(text=title,url=link))
    
    
    return reply_markup