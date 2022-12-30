import os
from datetime import datetime, timedelta
import csv
import logging

import requests
import pandas as pd
from tabulate import tabulate
from tapi_yandex_metrika import YandexMetrikaStats
from tapi_yandex_metrika.exceptions import YandexMetrikaTokenError
from dotenv import load_dotenv
load_dotenv('.env')

logger = logging.getLogger('kvedautobot.ym')
def get_dates_three_days_before() -> dict:
    date_format = '%d.%m'
    today = datetime.now()
    bb_yesterday = today - timedelta(days=3)
    before_yesterday = today - timedelta(days=2)
    yesterday = today - timedelta(days=1)

    return {
        'bb_yesterday': bb_yesterday.strftime(date_format),
        'before_yesterday': before_yesterday.strftime(date_format),
        'yesterday': yesterday.strftime(date_format)
    }


KVEDOMOSTI_URL = os.getenv('KVEDOMOSTI_URL')
# yandex-metrika access
YANDEX_APP_ID = os.getenv('YANDEX_APP_ID')
YANDEX_APP_PSWD = os.getenv('YANDEX_APP_PSWD')
YANDEX_METRIKA_TOKEN = os.getenv('YANDEX_METRIKA_TOKEN')


def get_status_code(url=KVEDOMOSTI_URL) -> str:
    """Pings url
    Args:
        url (str): url to ping. Defaults to KVEDOMOSTI_URL.
    Returns:
        str: status format "200;OK"
    """
    headers = {
        'User-Agent': 
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
        }
    response = requests.get(url, headers=headers)
    status = response.status_code
    if status > 200:
        logger.warning(f'Connection issue: {status}:\n{response.text}')
    elif status == 200:
        logger.info('Connection OK')
        return status
    return f'{status};{response.text}'


def monitor_yandex_metrika():
    """Get filtered and aggregated data from yandex.metrika for 
        - yesterday to before yesterday views difference and 
        - dict with three days before views
    Returns:
        tuple: (views difference to yesterday: int, {day.month: str: views: int})
    """    
    # По умолчанию возвращаются только 10000 строк отчета,
    # если не указать другое кол-во в параметре limit.

    api = YandexMetrikaStats(
        access_token=YANDEX_METRIKA_TOKEN
    )
    params = dict(
        ids="29848499",
        metrics="ym:s:visits",
        dimensions="ym:s:date",
        # filters="ym:s:isRobot=='No'", # роботы занимают больше 95% трафика
            sort="ym:s:date",
            limit=10
    )
    try:
        result = api.stats().get(params=params)
    except YandexMetrikaTokenError:
        return -1, dict(exception='Invalid yandex metrika token.')
    result = result().data['data']
    # result = result['data']
    dict_data = {'date': [], 'visits': []}
    for i in range(0, len(result)):
        dict_data['date'].append(result[i]['dimensions'][0]['name'])
        dict_data['visits'].append(result[i]['metrics'][0])

    df = pd.DataFrame.from_dict(dict_data)
    df['date'] = pd.to_datetime(df['date']).dt.date

    today = datetime.today().date()
    df = df.query('date < @today')

    yesterday_visits = df.iloc[-1, :]['visits']
    before_yesterday_visits = df.iloc[-2, :]['visits']
    diff: int = yesterday_visits - before_yesterday_visits
    # write to log information about scrapped visits
    logger.debug(f'Diff loaded: yv={yesterday_visits}, byv={before_yesterday_visits}')

    visits_3days_before: dict = dict(zip(
                                [df.iloc[i, :]['date'].strftime('%d.%m') for i in range(-3, 0)], 
                                [int(df.iloc[i, :]['visits']) for i in range(-3, 0)]
                            ))  # Out: {'24.03': 3118.0, '25.03': 2975.0, '26.03': 699.0}
    return diff, visits_3days_before

MONITOR_RESULT_FILE = 'monitoring.RESULT'


def write_result_file(filename=MONITOR_RESULT_FILE) -> dict:
    # date_modified = datetime.fromtimestamp(os.path.getmtime(filename))
    fields = [
            #'mdate',
            'diff',
            'status']
    fields.extend(list(get_dates_three_days_before().values()))
    if not os.path.isfile(filename) or \
        datetime.fromtimestamp(os.path.getmtime(filename)).date() != datetime.today().date() or \
            os.stat(filename).st_size == 0 or \
                csv_as_dict(filename, ',') is None:
        with open(filename, 'w', newline='') as result_file:
            writer = csv.DictWriter(result_file, fieldnames=fields, delimiter=',')
            writer.writeheader()
            writer.writerow(save_monitorig_result())
    monitoring_result = csv_as_dict(filename, ',')

    logger.debug(f'Got monitoring result')
    return monitoring_result


def csv_as_dict(file: str, delimiter: str = ',') -> dict:
    '''
    Returns dictionary of kind {'diff': int(integer), 'status': int(natural)}
    '''
    if not delimiter:
        delimiter = ','
    reader = csv.DictReader(open(file), delimiter=delimiter)
    for row in reader:
        return row     
        

def save_monitorig_result() -> dict:
    # days_before: yesterday, before yesterday, [before before] yesterday
    views_difference, visits_days_before = monitor_yandex_metrika()
    kved_response_status = get_status_code()
    # modify_date = str(datetime.today().date())
    result = {
        # 'mdate': modify_date,
        'diff': views_difference,
        'status': kved_response_status
    }
    result.update(visits_days_before)
    return result


def main() -> str:
    """Get monitoring message

    Returns:
        str: ready message to send with bot
    """    
    res = write_result_file()
    diff = int(float(res['diff']))
    sig = '+' if diff > 0 else ''
    is_ok_diff = True
    is_ok_status = True
    status = res['status']
    status_code = status
    if diff < 0:
        if abs(diff) > 500:
            is_ok_diff = False
    if isinstance(status, str):
        if not status.isalnum():
            is_ok_status = False
            status = status.split(';')
            status_code = status[0]
            status_msg = status[1]
        else:
            status_code = int(status)
    prev_data = [int(float(i)) for i in list(res.values())[2:]]
    prev_header = list(res.keys())[2:]
    table = tabulate([prev_data], prev_header, tablefmt='plain')
    message = f"""
#kvedomosti
Посещаемость ({sig}{diff}): {'OK' if is_ok_diff else 'check CEO'}
  `Визиты за последние дни:` 
`{table}`

Доступность сайта ({status_code}): {'OK' if is_ok_status else status_msg}
    """
    logger.info('Message created')
    return message

if __name__ == '__main__':
    print(main())
