import logging
import random
import re
import time
from pathlib import Path

import pandas as pd
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import os
import filecmp
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler('../logs/imdb_scraper.log')
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] - %(message)s"))
logger.addHandler(file_handler)

# Set constants
BASE_URL = "https://www.imdb.com/search/title/?count=100&groups=top_1000&sort=user_rating"
DATA_DIR = Path("../data")
RETRY_ATTEMPTS = 3
PROXIES = ["ip1:port1", "ip2:port2", "ip3:port3"]

def setup_driver(proxy):
    logger.info(f'Setting up driver with proxy {proxy}.')
    user_agent = UserAgent().random
    webdriver.DesiredCapabilities.CHROME["proxy"] = {
        "httpProxy": proxy,
        "ftpProxy": proxy,
        "sslProxy": proxy,
        "proxyType": "MANUAL",
    }
    chrome_options = Options()
    chrome_options.add_argument(f"user-agent={user_agent}")
    chrome_options.add_argument("--headless")

    return webdriver.Chrome(options=chrome_options)

def process_movie_info(info):
    lines = info.text.split('\n')
    header = lines[0].split(' ')
    rang = header[0]
    jahr = header[-1]
    film = ' '.join(header[1:-1])

    match = re.match(r'(?:(.*?)\|)?\s*(.*?)\|\s*(.*)', lines[1])
    if match:
        fsk = match.group(1) or 'NaN'
        dauer = match.group(2)
        genre = match.group(3)

    bewertung = lines[2].split(' ')[0]
    staff = lines[-2].split(" | ")
    for i in range(len(staff)):
        staff[i] = staff[i].replace('Director: ', '').replace('Stars: ', '')
    regisseur, stars = staff[0], ' '.join(staff[1:])

    return rang, film, jahr, fsk, dauer, genre, bewertung, regisseur, stars

def get_movie_data(driver):
    movie_data = []
    last_page_reached = False
    page_number = 1
    while not last_page_reached:
        movie_info = driver.find_elements(By.XPATH, '//div[@class="lister-item-content"]')
        for info in movie_info:
            movie_data.append(process_movie_info(info))

        try:
            next_page = driver.find_element(By.LINK_TEXT, "Next »")
            next_page.click()
            time.sleep(random.randint(1, 5))
            logger.info(f"Finished processing page {page_number}. Moving to the next page.")
            page_number += 1
        except Exception as e:
            logger.warning(f"Error while clicking next page on page {page_number}. Error: {e}")
            last_page_reached = True
            driver.quit()

    return movie_data

def save_data_as_csv(data, temp_file_path):
    logger.info(f'Writing data to temp file {temp_file_path}.')
    df = pd.DataFrame(data, columns=["rang", "film", "jahr", "fsk", "dauer", "genre", "bewertung", "regisseur", "stars"])
    df.to_csv(temp_file_path, index=False)
    logger.info('Data writing complete.')

def manage_data_file(temp_file_path, file_path):
    if file_path.exists():
        if not filecmp.cmp(temp_file_path, file_path, shallow=False):
            logger.info("Data has changed. Updating the existing file.")
            os.remove(file_path)
            shutil.move(temp_file_path, file_path)
            logger.info(f"Data saved to {file_path}")
        else:
            logger.info("Data has not changed. No update is necessary.")
            os.remove(temp_file_path)
    else:
        shutil.move(temp_file_path, file_path)
        logger.info(f"Data saved to {file_path}")

def main():
    for proxy in PROXIES:
        driver = setup_driver(proxy)

        for attempt in range(RETRY_ATTEMPTS):
            try:
                driver.get(BASE_URL)
                next_page = driver.find_element(By.LINK_TEXT, "Next »")
                break
            except Exception as e:
                logger.error(f'Error occurred with proxy {proxy} on page {attempt + 1}. Error: {e}')
                logger.info("Retrying...")

        else:
            logger.error(f'Failed to retrieve page after multiple attempts with proxy {proxy}. Moving to the next proxy.')
            continue

        movie_data = get_movie_data(driver)
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        temp_file_path = DATA_DIR / "temp_imdb_top_1000.csv"
        save_data_as_csv(movie_data, temp_file_path)

        file_path = DATA_DIR / "imdb_top_1000.csv"
        manage_data_file(temp_file_path, file_path)

        break

if __name__ == "__main__":
    main()
