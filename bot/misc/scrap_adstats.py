import os
import json
import logging

from dotenv import load_dotenv

from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromiumService
from webdriver_manager.core.utils import ChromeType

from .advads_utils.get_adstats import move_old_pdfs
from .advads_utils.get_adstats import get_browser, signing_in
from .advads_utils.get_adstats import save_adstats_to_pdf

load_dotenv()
logger = logging.getLogger('kvedautobot.ads')


def main(
    period : str      = 'last_30_days', 
    update: bool      = True, 
    scrap_folder: str = './bot/misc/advads_utils/scrapped_data/',
    drafts: bool = False) -> dict:
    """
    Avaliable periods: last30days, lastmonth, last12months
    Args:
        period (str):   Period for scraping advertisement statistics
                        Default 'last_30_days'
        update (bool):  If True truncates result json-file
                        and deletes all pdfs to reload
    Returns:
        dict: { <stats_title> : <stats_link> }
    """

    trash_folder: str = os.path.join(scrap_folder, ".trash/")
    links_stats_file  = os.path.join(scrap_folder, "stats_links.json")
    if os.path.isfile(links_stats_file):
        if update:
            os.remove(links_stats_file)
            move_old_pdfs(scrap_folder, trash_folder)

        if not update: # return result dict
            with open(links_stats_file) as json_file:
                data = json.load(json_file)
            logger.info('data is already aggregated, filename: {}.'.format(links_stats_file))
            logger.info('Success.')
            return data
    # env
    username = os.getenv('KVED_USER')
    passwd = os.getenv('KVED_PSWD')
    # main url
    url = 'https://kvedomosti.ru/wp-admin/edit.php?post_type=advanced_ads'
    chrome_options = ChromeOptions()
    chrome_options.add_argument('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36')
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument('--ignore-ssl-errors=yes')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--remote-debugging-port=9555')
    service = ChromiumService(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
    driver, e = get_browser(
        None, 
        chrome_options 
    # , headless=False
    )
    if e:
        raise e
    # log in
    signing_in(driver, username, passwd)
    # go to ad posts page
    driver.get(url) 

    links_to_stats = save_adstats_to_pdf(driver, period, scrap_folder, drafts=drafts)

    driver.quit()
    with open(links_stats_file, "w") as outfile:
        json.dump(links_to_stats, outfile)

    logger.info('Process finished with success.')

    return links_to_stats