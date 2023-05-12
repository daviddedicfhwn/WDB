import logging
import random
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
from selenium.webdriver.common.proxy import Proxy, ProxyType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Set constants
BASE_URL = "https://www.imdb.com/search/title/?count=100&groups=top_1000&sort=user_rating"
DATA_DIR = Path("data")
RETRY_ATTEMPTS = 3
PROXIES = ["ip1:port1", "ip2:port2", "ip3:port3"]


def setup_driver(proxy):
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


def get_movie_data(driver):
    rang, film, jahr, fsk, dauer, genre, bewertung, regisseur, stars = [], [], [], [], [], [], [], [], []

    last_page_reached = False
    page_number = 1
    while not last_page_reached:
        movie_info = driver.find_elements(By.XPATH, '//div[@class="lister-item-content"]')
        for info in movie_info:
            # Split the text into lines and select the second line
            lines = info.text.split('\n')
            header = lines[0].split(' ')
            # Append the data to the lists
            rang.append(header[0])
            jahr.append(header[-1])
            film.append(header[1:-1])

            # Check for the length of the list to avoid errors
            if len(lines[1].split('|')) == 3:
                fsk.append(lines[1].split('|')[0])
                dauer.append(lines[1].split('|')[1])
                genre.append(lines[1].split('|')[2])
            elif len(lines[1].split('|')) == 2:
                fsk.append('NaN')
                dauer.append(lines[1].split('|')[0])
                genre.append(lines[1].split('|')[1])

            bewertung.append(lines[2].split(' ')[0])
            staff = lines[-2].split(" | ")
            # Iterating through the list and replacing 'Director:' with an empty string
            for i in range(len(staff)):
                staff[i] = staff[i].replace('Director: ', '')
                staff[i] = staff[i].replace('Stars: ', '')
            # Append the duration to the list
            regisseur.append(staff[0])
            stars.append(staff[-1])

        try:
            next_page = driver.find_element(By.LINK_TEXT, "Next »")
            next_page.click()
            time.sleep(random.randint(1, 5))
            logger.info(f"Finished processing page {page_number}. Moving to the next page.")
            page_number += 1
        except Exception as e:
            logger.info("Last page reached")
            last_page_reached = True
            driver.quit()

    return rang, film, jahr, fsk, dauer, genre, bewertung, regisseur, stars


def main():
    for proxy in PROXIES:
        driver = setup_driver(proxy)

        for attempt in range(RETRY_ATTEMPTS):
            try:
                driver.get(BASE_URL)
                next_page = driver.find_element(By.LINK_TEXT, "Next »")
                break
            except Exception as e:
                logger.error(f"An error occurred: {e}")
                logger.info("Retrying...")

        else:
            logger.error("Failed to retrieve page after multiple attempts. Moving to the next proxy.")
            continue

        # Scrape the data
        rang, film, jahr, fsk, dauer, genre, bewertung, regisseur, stars = get_movie_data(driver)

        # Create a DataFrame with the scraped data
        df = pd.DataFrame(
            {
                "rang": rang,
                "film": film,
                "jahr": jahr,
                "fsk": fsk,
                "dauer": dauer,
                "genre": genre,
                "bewertung": bewertung,
                "regisseur": regisseur,
                "stars": stars,
            }
        )

        # Save the DataFrame as a temporary CSV file
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        temp_file_path = DATA_DIR / "temp_imdb_top_1000.csv"
        df.to_csv(temp_file_path, index=False)

        # Check if the data file already exists
        file_path = DATA_DIR / "imdb_top_1000.csv"
        if file_path.exists():
            # Compare the contents of the old and new files
            if not filecmp.cmp(temp_file_path, file_path, shallow=False):
                # If the files are different, replace the old file with the new one
                logger.info("Data has changed. Updating the existing file.")
                os.remove(file_path)
                shutil.move(temp_file_path, file_path)
                logger.info(f"Data saved to {file_path}")
            else:
                logger.info("Data has not changed. No update is necessary.")
                os.remove(temp_file_path)
        else:
            # If the file does not exist, save the new data
            shutil.move(temp_file_path, file_path)
            logger.info(f"Data saved to {file_path}")

        break


if __name__ == "__main__":
    main()
