import time
import platform
import re 

from selenium import webdriver
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from markdownify import markdownify as md

try:
    from pyvirtualdisplay import Display
except ImportError:
    Display = None

MAX_RETRIES = 10
RETRY_DELAY = 10

def element_strip(elem):
    return elem.text.strip()

def format_for_reddit(text):
    """Clean up Perplexity output for Reddit."""
    # Remove citation links [number](url) -> [[domain]](url)
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
    
def get_latest_news():
    answer = ''
    driver = None
    display = None
    firefox_driver_path = "/opt/homebrew/bin/geckodriver"
    try:
        for i in range(MAX_RETRIES):
            print('i',i)
            try:
                if platform.system() == "Darwin":
                    service = Service(firefox_driver_path)
                    options = Options()
                    options.add_argument("--headless")
                    driver = webdriver.Firefox(options=options, service=service) 
                elif platform.system() == "Linux":
                    options = Options()
                    options.add_argument("--headless")
                    driver = webdriver.Firefox(options=options)
                else :
                    driver = uc.Chrome()
                driver.get("https://www.perplexity.ai/search?q=What are the latest geopolitical news this week? Make it region wise. ")
                print('driver',driver)

                WebDriverWait(driver, 40).until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Follow-ups')]"))
                )
                dynamic_elements = WebDriverWait(driver, 40).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, 'prose'))
                )
                if dynamic_elements:
                    for element in dynamic_elements:
                        html_content = element.get_attribute('innerHTML')
                        answer = md(html_content)
                break
            except (WebDriverException, TimeoutException) as e:
                print(f"Error encountered: {str(e)}")
                if driver:
                    driver.quit()
                    driver = None
                time.sleep(RETRY_DELAY)
                continue  
            finally:
                if driver:
                    driver.quit()
                    driver = None

        if len(answer) > 0:
            formatted_text = format_for_reddit(answer)
            print("formatted Text ", formatted_text)
            answer = formatted_text
        else:
            print('API error', answer)

    except Exception as e:
        print(e)
    finally:
        if driver:
            driver.quit()
    return answer
