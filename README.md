# IMDB Web Scraper
This is a web scraper built in Python using the Selenium and Fake UserAgent libraries. It is designed to scrape movie data from the top 1000 rated movies on IMDB.
# Why This is a Good Project
Web scraping is a valuable skill for data gathering when APIs are not available. This project demonstrates how to navigate and extract information from a website, handle common issues such as bot detection and proxies, and store the data for analysis. It's a great starting point for anyone interested in data gathering and analysis.
# Installation
To get started with this project, follow these steps:
1. Clone this repository: git clone https://github.com/daviddedicfhwn/WDB.git
2. Navigate to the project directory: cd WDB
3. Install the required Python libraries: fount in the requirements.txt file

# Usage
The scraper will start at the IMDB top 1000 rated movies page and navigate through each page, scraping data on each movie, such as the movie's rank, title, year, rating, duration, genre, director, and stars. The data is stored in lists which are then converted into a pandas DataFrame for easy analysis and manipulation.

The scraper uses random UserAgents and a list of proxies to help avoid detection. If the scraper encounters an error, it will attempt to retry with the same proxy. If it continues to fail, it will move on to the next proxy in the list.
# Further Information
The scraper is set to run in headless mode, meaning it runs in the background and you won't see the Chrome browser open. If you want to see the browser while the scraper is running, you can comment out the line that sets the browser to headless mode.

The scraper also includes a delay between page navigation to mimic human behavior and avoid triggering bot detection.

When the scraper has navigated through all pages and gathered all data, it will close the browser and end the program.
# Contributing
We welcome contributions to this project. Please feel free to submit issues or pull requests.
