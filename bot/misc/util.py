from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault


async def set_commands(bot: Bot):
    commands = [
        BotCommand(
            command='monitor',
            description='Monitor kvedomosti.ru visitors'
        ),
        BotCommand(
            command='seload',
            description='Upload video to FTP and post to сельский-час.рф'
        ),
        BotCommand(
            command='adstats',
            description='AdvancedAds statistics links'
        ),
        BotCommand(
            command='adstats_pdf',
            description='AdvancedAds statistics PDFs'
        )
    ]

    await bot.set_my_commands(commands, BotCommandScopeDefault())



def clip_text(filename: str):
    with open(filename, 'r') as f:
        text = [
            s.replace("ERROR", html_bold("ERROR"))\
                .replace("CRITICAL", html_bold("CRITICAL"))
            for s in f.readlines()]
    return ''.join(text[:16])

def markdown_link(title, link) -> str:
    return f'[{title}]({link})'

def markdown_encode_string(string: str) -> str:
    return string\
        .replace('-', '\-')\
        .replace('!', '\!')\
        .replace('.', '\.')\
        .replace('#', '\#')\
        .replace('(', '\(')\
        .replace(')', '\)')\
        .replace('=', '\=')\
        .replace('_', '\_')\
        .replace('$', '\$')\
        .replace('?', '\?')\
        .replace('/', '\/')\
        .replace('&', '\&')\
        .replace('[', '\[')\
        .replace(']', '\]')


def html_link(title, link):
    return f'<a href="{link}">{title}</a>'
    
def html_bold(string: str) -> str:
    return f'<b>{string}</b>'

def clear_folder(folder):
    import os, shutil
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            # elif os.path.isdir(file_path):
                # shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
        