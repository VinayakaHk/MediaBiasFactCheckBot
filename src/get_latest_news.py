import time
import platform
import re 

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException

from markdownify import markdownify as md

from pyvirtualdisplay import Display



MAX_RETRIES = 10
RETRY_DELAY = 10

def element_strip(elem):
    return elem.text.strip()

def format_for_reddit(answer):
    # Use regex to find all citations in the format [number](url)
    pattern = r'\[(\d+)\]\((https?://[^)]+)\)'
    
    def replace_citation(match):
        url = match.group(2)
        # Extract domain from URL
        domain = re.search(r'https?://(?:www\.)?([^/]+)', url)
        if domain:
            domain_name = domain.group(1)
            return f' [[{domain_name}]]({url}) '
        return match.group(0)
    
    formatted_text = re.sub(pattern, replace_citation, answer)
    return formatted_text
def get_latest_news():
    answer = ''
    driver = None
    display = Display(visible=False, size=(800, 600))
    chrome_driver_path = "/usr/bin/chromedriver"
    try:
        for i in range(MAX_RETRIES):
            print('i',i)
            try:
                if platform.machine() == "aarch64" and platform.system() == "Linux":
                    display.start()
                options = uc.ChromeOptions()
                if platform.system() == "Darwin": 
                    options.binary_location = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
                    driver = uc.Chrome(options=options)
                elif platform.system() == "Linux":
                    options.binary_location = "/usr/bin/chromium-browser"
                    chrome_driver_path = "/usr/bin/chromedriver"
                    driver = uc.Chrome(options=options, driver_executable_path=chrome_driver_path)
                else :
                    driver = uc.Chrome()
                driver.get("https://www.perplexity.ai/search?q=What are the latest geopolitical news this week? Make it region wise. ")
                print('driver',driver)

                WebDriverWait(driver, 40).until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Related')]"))
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
                if platform.machine() == "aarch64" and platform.system() == "Linux":
                    display.stop()
                time.sleep(RETRY_DELAY)
                continue  
            finally:
                if driver:
                    driver.quit()
                if platform.machine() == "aarch64" and platform.system() == "Linux":
                    display.stop()

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
        if platform.machine() == "aarch64" and platform.system() == "Linux":
            display.stop()
    return answer
