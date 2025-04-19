
import time
import platform
import re 

from selenium.webdriver.chrome.options import Options


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

def format_for_reddit(answer ):
    formatted_text = ""
    formatted_text = re.sub(r'\[.*?\]', '', answer)
    formatted_text = re.sub(r'\(.*?\)', '', formatted_text)
    
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
                options = Options()
                if platform.system() == "Darwin": 
                    options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
                elif platform.system() == "Linux":
                    options.binary_location = "/usr/bin/chromium"
                    chrome_driver_path = "/usr/bin/chromedriver"
                
                driver = uc.Chrome(driver_executable_path=chrome_driver_path, options=options)
                
                driver.get("https://www.perplexity.ai/search?q=give me the latest geopolitical news in this week and dont give an introduction")
                print('driver',driver)

                time.sleep(30)

                dynamic_elements = WebDriverWait(driver, 40).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, 'prose'))
                )
                if dynamic_elements:
                    # Extract text and HTML from each element
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

