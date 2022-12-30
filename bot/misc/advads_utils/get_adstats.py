from time import sleep
import os
import json
import base64
import logging
import shutil

from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By

from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFParser
from pdfminer.pdfpage import PDFDocument
load_dotenv('.env')


logger = logging.getLogger('kvedautobot.ads')

def get_browser(service, options, headless=True):
    if headless:    
        options.add_argument('--headless')
        logger.debug('Set --headless option')
    try:
        # driver = webdriver.Remote(
        #     "http://176.119.158.235:4446", 
        #     # DesiredCapabilities.CHROME, 
        #     options=options
        #     )

        driver = webdriver.Chrome(service=service, options=options)
        return driver, None
    except Exception as e:
        logger.error(str(e))
        logger.critical(e)
        logger.critical('Exiting.')
        return None, e

def signing_in(driver, username, password, url='https://kvedomosti.ru/wp-admin/edit.php?post_type=advanced_ads'):
    logger.info('Sign in routine. . .')

    driver.get(url)
    sleep(1)
    def auth_triple(driver: webdriver):
        """
        locate and fill login field ->
        locate and fill password field ->
        click Submit button.       
        """
        driver.refresh()
        user_login = driver.find_element(By.CSS_SELECTOR, '#user_login')
        user_login.clear()
        user_login.send_keys(username)
        user_pass = driver.find_element(By.CSS_SELECTOR, '#user_pass')
        user_pass.clear()
        user_pass.send_keys(password)
        driver.find_element(By.CSS_SELECTOR, '#wp-submit').click()

    tries = 0; max_tries = 10
    try:
        while driver.current_url != 'https://kvedomosti.ru/?page_id=212767&user=29400':
            tries += 1
            driver.refresh()
            if tries == max_tries:
                logger.critical('Unable to sign in WordPress. Exit.')
                logger.debug(f'tries num: {tries}; max tries: {max_tries}.')

            auth_triple(driver)
            sleep(3)
    except WebDriverException as e:
        logger.warning('Session closed.')
        logger.exception(e)


def check_pdf_mediabox(pdf_filename: str) -> bool:
    if not os.path.isfile(pdf_filename):
        logger.error('File {} not exists'.format(pdf_filename))
        return False
    parser = PDFParser(open(pdf_filename, 'rb'))
    doc = PDFDocument(parser)
    # check pages' formats
    page_sizes_list = [page.attrs['MediaBox'] for page in PDFPage.create_pages(doc)]
    # check pages number
    num_pages = len(page_sizes_list)
    logger.debug(f'check {pdf_filename}')
    logger.debug(f'page_sizes_list: {page_sizes_list}')
    logger.debug(f'{num_pages} pages found in newly downloaded pdf')

    # 594.95996x840.95996 points = A4
    A4 = [0, 0, 594, 841]
    flags = [([int(k) for k in i] == A4) for i in page_sizes_list]
    logger.debug(f'flags: {flags}')
    if sum(flags) != num_pages:
        logger.warning(
            'Wrong pages format ({}/{})'.format(sum(flags), num_pages)
            )
        return False
    logger.debug('Pdfs all have A4 format')
    return True


def kilobytes(bytes: int or float) -> int:
    return bytes // 1024

def check_pdf_size(pdfname: str) -> bool:
    file_size = kilobytes(os.stat(pdfname).st_size)
    if file_size == 0:
        logger.warning('{} is broken'.format(file_size))
        return False
    return True

def print_to_pdf(driver, title: str, scrap_folder: str) -> bool:
    pdf_name = os.path.join(scrap_folder, f'{title}.pdf')

    if os.path.isfile(pdf_name):
        logger.info('File {} is already exists'.format(pdf_name))
        if check_pdf_size(pdf_name):
            return True
        logger.warning('Detected empty or broken file: {}'.format(pdf_name))
    params = {'landscape': False,
              'paperWidth': 8.27,
              'paperHeight': 11.69}                         
    data = driver.execute_cdp_cmd("Page.printToPDF", params)
    
    with open(pdf_name, 'wb') as file:
        file.write(base64.b64decode(data['data']))
    return check_pdf_mediabox(
        pdf_filename=pdf_name)*check_pdf_size(pdf_name)


class AdstatsUrl:
    def __init__(self, url, period):
        if period is None:
            period = 'last_30_days'
        self.period : str = self.validate_period(period)
        self.url : str = url+'&period='+self.period

    @staticmethod
    def validate_period(period: str) -> str:
        period: str = period.lower().replace('_','').replace(' ','').replace('-','')
        available_periods: tuple = ('lastmonth', 'last30days', 'last12months')
        assert period in available_periods, 'No such period is available'
        return period


def save_adstats_to_pdf(driver: webdriver, period: str, scrap_folder: str, drafts=True):
    """Browse and save ad-statistics from WordPress to pdf

    Args:
        driver (webdriver): webdriver instance  with posts curr_url
        period (str): period of advertisement statistics

    Returns:
        shareable_links: dict(title: formatted_link)
    """   
    rows_drafts = list()
    if drafts: 
        rows_drafts = driver.find_elements(By.XPATH, "//tr[contains(@class, 'status-draft')]//a[@class='row-title']")
        logger.debug(f'{len(rows_drafts)} drafts found')
    rows_published = driver.find_elements(By.XPATH, "//tr[contains(@class, 'status-publish')]//a[@class='row-title']")
    logger.debug(f'{len(rows_published)} items(posts) found')
   
    rows_published.extend(rows_drafts)
    posts_titles_links = {row.text: row.get_attribute('href') for row in rows_published}
    shareable_links = {key: value for key, value in posts_titles_links.items()}
    for title, post_link in posts_titles_links.items():
        driver.get(post_link)
        shareable_href = driver.find_element(By.ID, 'ad-public-link')\
                               .get_attribute('href')
        shareable_href = AdstatsUrl(url=shareable_href, period=period).url
        shareable_links[title] = shareable_href

        stats_link = shareable_links[title]
        driver.get(stats_link)
        sleep(2)
        success = print_to_pdf(driver, title, scrap_folder)

        tries = 0; max_tries=3
        while not success:
            tries+=1
            if tries == max_tries:
                logger.warning(f'tries={tries}; max_tries={max_tries}')
                logger.warning(f'{title}.pdf was not downloaded or format problems were occured.')
                logger.warning(f'You may also use wrong period for the certain ad-post: {period}')
            
            logger.warning('Try to reopen failed page and download once again...')
            driver.get(stats_link)
            sleep(2)
            success = print_to_pdf(driver, title, scrap_folder)

        logger.info(f'{title}.pdf downloaded succefully.')

    return shareable_links 

def move_old_pdfs(source_folder, destination_folder):
    if not os.path.isdir(destination_folder):
        os.mkdir(destination_folder)
        logger.debug(f'Created directory: {destination_folder}')
    # fetch all files
    for file_name in os.listdir(source_folder):
        # construct full file path
        source = source_folder + file_name
        destination = destination_folder + file_name
        # move only files
        if os.path.isfile(source):
            shutil.move(source, destination)
            logger.info('Moved: %s' % file_name)

