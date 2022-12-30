from os import environ
from typing import Final


class TgKeys:
    TOKEN: Final = environ.get('TOKEN', None)


class WorkChat:
    ID: Final = environ.get('WORK_CHAT_ID', None)


class AdstatsKeys:
    ADSTATS_PATH: Final = environ.get('ADSTATS_PATH', None)
    PSWD:         Final = environ.get('KVED_PSWD', None)
    USER:         Final = environ.get('KVED_USER', None)
    WP_APP_PSWD:  Final = environ.get('WP_APP_PASSWORD', None)