"""Shared Perplexity AI scraper using Firefox headless."""

import re
import time
import platform

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from markdownify import markdownify as md

MAX_RETRIES = 10
RETRY_DELAY = 10

GECKODRIVER_PATH = {
    "Darwin": "/opt/homebrew/bin/geckodriver",
    "Linux": "/usr/local/bin/geckodriver",
}


def _get_driver():
    """Create a headless Firefox driver for the current platform."""
    options = Options()
    options.add_argument("--headless")
    system = platform.system()
    driver_path = GECKODRIVER_PATH.get(system)
    if driver_path:
        service = Service(driver_path)
        return webdriver.Firefox(options=options, service=service)
    return webdriver.Firefox(options=options)


def format_for_reddit(text):
    """Clean up Perplexity output for Reddit."""
    pattern = r'\[(\d+)\]\((https?://[^)]+)\)'

    def replace_citation(match):
        url = match.group(2)
        domain = re.search(r'https?://(?:www\.)?([^/]+)', url)
        if domain:
            return f" [[{domain.group(1)}]]({url}) "
        return match.group(0)

    text = re.sub(pattern, replace_citation, text)
    text = re.sub(r'\w*\+\d+', '', text)
    return text.strip()


def query_perplexity(query: str) -> str:
    """Query Perplexity AI and return the formatted markdown response."""
    import urllib.parse
    encoded = urllib.parse.quote(query)
    url = f"https://www.perplexity.ai/search?q={encoded}"

    driver = None
    answer = ""

    for attempt in range(MAX_RETRIES):
        try:
            driver = _get_driver()
            driver.get(url)

            WebDriverWait(driver, 40).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Follow-ups')]"))
            )
            dynamic_elements = WebDriverWait(driver, 40).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "prose"))
            )

            if dynamic_elements:
                for element in dynamic_elements:
                    html_content = element.get_attribute("innerHTML")
                    answer = md(html_content)
                break

        except (WebDriverException, TimeoutException) as e:
            print(f"Attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
            time.sleep(RETRY_DELAY)
        finally:
            if driver:
                driver.quit()
                driver = None

    return format_for_reddit(answer) if answer else ""
