import time
import urllib.parse
import platform

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException

from pyvirtualdisplay import Display



MAX_RETRIES = 3  
RETRY_DELAY = 2  

def element_strip(elem):
    return elem.text.strip()

def llm_detection (comment):
    """
    A function that performs llm detection using the provided comment, mod_mail, and parent_comment.
    It checks for rule violations in the comment and takes appropriate actions based on the result.
    """

    answer = ''
    driver = None
    display = Display(visible=0, size=(800, 600))

    try:
        for i in range(MAX_RETRIES):
            try:
                if platform.machine() == "aarch64" and platform.system() == "Linux":
                    display.start()

                driver = webdriver.Chrome()
                query = f"for context, '' is the parent comment. Donot judge this. You are a moderator who disallows verbal abuse under Rule 2. Criticism is fair and allowed. Tell me if this comment starting and ending with violates the rule \n\n ```{comment}```.\n\n Your answer must start from either  (False. if it doesn't violate the rules )  or (True. if it does violate the rules) .  Give a short reason in under 80 characters"
                encoded_url = urllib.parse.quote(query)
                driver.get(f"https://www.perplexity.ai/search?q={encoded_url}")
                time.sleep(7)
                print(driver.title)

                dynamic_elements = WebDriverWait(driver, 30).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, 'prose'))
                )
                if dynamic_elements:
                    answer = ''.join([element_strip(elem) for elem in dynamic_elements])
                break  

            except (WebDriverException, TimeoutException) as e:
                print(f"Error encountered: {str(e)}")
                time.sleep(RETRY_DELAY)
                if driver:
                    driver.quit()
                if platform.machine() == "aarch64" and platform.system() == "Linux":
                    display.stop()
                continue  
            finally:
                if driver:
                    driver.quit()
                if platform.machine() == "aarch64" and platform.system() == "Linux":
                    display.stop()
        if answer.startswith('True.') and not any(substring in answer for substring in ['does not', 'without', 'respectful']):
            reason = answer.split('True.')
            if len(reason) > 100:
                reason = reason[:100]
            print(reason[1])
           
        elif answer.startswith('False.'):
            reason = answer.split('False.')
            if len(reason) > 100:
                reason = reason[:100]
            print(reason[1])
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


if __name__ == '__main__':
    llm_detection("They should get their own life together first lol.")

