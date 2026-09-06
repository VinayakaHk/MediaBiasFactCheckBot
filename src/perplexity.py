"""Shared Perplexity AI scraper using Firefox headless with cookie injection."""

import os
import re
import sqlite3
import time
import platform

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from markdownify import markdownify as md

MAX_RETRIES = 3
RETRY_DELAY = 15

GECKODRIVER_PATH = {
    "Darwin": "/opt/homebrew/bin/geckodriver",
    "Linux": "/snap/bin/geckodriver" if platform.machine() in ("x86_64", "AMD64") else "/usr/local/bin/geckodriver",
}

FIREFOX_COOKIES_DB = {
    "Darwin": None,
    "Linux": os.path.expanduser("~/snap/firefox/common/.mozilla/firefox/6n1dsopf.default/cookies.sqlite"),
}


def _get_perplexity_cookies():
    """Read Perplexity cookies from Firefox's cookies.sqlite (read-only)."""
    system = platform.system()
    db_path = FIREFOX_COOKIES_DB.get(system)
    if not db_path or not os.path.isfile(db_path):
        return []

    conn = sqlite3.connect(f"file:{db_path}?mode=ro&immutable=1", uri=True)
    cur = conn.cursor()
    cur.execute(
        "SELECT name, value, host, path, isSecure, expiry FROM moz_cookies "
        "WHERE host LIKE '%perplexity%'"
    )
    cookies = []
    for name, value, host, path, is_secure, expiry in cur.fetchall():
        cookie = {
            "name": name,
            "value": value,
            "domain": host,
            "path": path or "/",
            "secure": bool(is_secure),
        }
        if expiry:
            cookie["expiry"] = expiry
        cookies.append(cookie)
    conn.close()
    return cookies


def _get_driver():
    """Create a headless Firefox driver (fresh profile, no lock issues)."""
    options = Options()
    options.add_argument("--headless")
    options.page_load_strategy = "eager"

    system = platform.system()
    driver_path = GECKODRIVER_PATH.get(system)
    if driver_path and os.path.isfile(driver_path):
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
    import logging
    import urllib.parse

    log = logging.getLogger("perplexity")
    encoded = urllib.parse.quote(query)
    url = f"https://www.perplexity.ai/search?q={encoded}"

    driver = None
    answer = ""

    log.info(f"Starting query: {query[:80]}...")
    log.info(f"URL: {url[:120]}...")

    for attempt in range(MAX_RETRIES):
        try:
            log.info(f"Attempt {attempt + 1}/{MAX_RETRIES}: launching headless Firefox")
            driver = _get_driver()
            driver.set_page_load_timeout(20)

            # First navigate to perplexity.ai to set the cookie domain
            try:
                driver.get("https://www.perplexity.ai")
                log.info("Navigated to perplexity.ai for cookie domain")
            except TimeoutException:
                log.warning("Timeout navigating to perplexity.ai (continuing)")

            # Inject cookies from Firefox profile
            cookies = _get_perplexity_cookies()
            log.info(f"Loaded {len(cookies)} cookies from Firefox profile")
            injected = 0
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                    injected += 1
                except Exception:
                    pass  # Some cookies may fail due to domain mismatch
            log.info(f"Injected {injected}/{len(cookies)} cookies")

            # Now navigate to the actual search query
            try:
                driver.get(url)
                log.info("Navigated to search URL")
            except TimeoutException:
                log.warning("Timeout navigating to search URL (continuing)")

            # Poll for the prose element to contain actual content.
            # Perplexity streams the response, so we wait until it stabilizes.
            last_text = ""
            stable_count = 0

            for poll_iter in range(24):  # Up to 120 seconds (24 * 5s)
                time.sleep(5)
                try:
                    prose_els = driver.find_elements(By.CLASS_NAME, "prose")
                except Exception as e:
                    log.debug(f"Poll {poll_iter}: find_elements error: {e}")
                    continue

                if not prose_els:
                    log.debug(f"Poll {poll_iter}: no .prose elements found")
                    continue

                current_text = prose_els[-1].text

                # Skip if it's just the sign-in message
                if "Sign up and repeat" in current_text:
                    log.warning(f"Attempt {attempt + 1}/{MAX_RETRIES}: Sign-in wall detected")
                    break

                if len(current_text) > 50:
                    if current_text == last_text:
                        stable_count += 1
                        if stable_count >= 2:  # Text stable for 10+ seconds = done
                            log.info(f"Poll {poll_iter}: text stable ({len(current_text)} chars), extracting answer")
                            html_content = prose_els[-1].get_attribute("innerHTML")
                            answer = md(html_content)
                            break
                    else:
                        stable_count = 0
                    last_text = current_text
                    log.debug(f"Poll {poll_iter}: text growing ({len(current_text)} chars)")
                else:
                    log.debug(f"Poll {poll_iter}: text too short ({len(current_text)} chars)")

            if answer:
                log.info(f"Success: got {len(answer)} char answer")
                break
            else:
                log.warning(f"Attempt {attempt + 1}/{MAX_RETRIES}: no answer extracted after polling")

        except (WebDriverException, TimeoutException) as e:
            log.error(f"Attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
        finally:
            if driver:
                driver.quit()
                driver = None

        if not answer:
            time.sleep(RETRY_DELAY)

    return format_for_reddit(answer) if answer else ""
