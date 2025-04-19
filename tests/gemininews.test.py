import time
import urllib.parse
import platform

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
#import options 
from selenium.webdriver.chrome.options import Options
from markdownify import markdownify as md

options = Options()
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
from pyvirtualdisplay import Display


MAX_RETRIES = 5
RETRY_DELAY = 5  






def format_for_reddit(answers):
    markdown_text = ""
    current_section = ""
    
    for answer in answers:
        # Skip span elements that contain only numbers
        if answer['tag'] == 'span' and (answer['text'].strip().isdigit() or 
            answer['text'].strip().endswith('.') and answer['text'].strip()[:-1].isdigit()):
            continue
            
        # Handle strong tags as headers
        if answer['tag'] == 'strong':
            markdown_text += f"\n{answer['text']}\n\n"
            current_section = answer['text']
            
        # Handle paragraph tags
        elif answer['tag'] == 'p' and answer['text'] and not answer['text'].strip() == current_section:
            markdown_text += f"{answer['text']}\n\n"
            
        # Handle list items
        elif answer['tag'] == 'li':
            markdown_text += f"* {answer['text']}\n"
            
        # Handle links
        elif answer['tag'] == 'a' and answer['href']:
            markdown_text += f"[Source]({answer['href']}) "

    return markdown_text.strip()

def main_function():
    answers = []
    driver = None
    display = Display(visible=False, size=(800, 600))

    try:
        for i in range(MAX_RETRIES):
            print('i',i)
            try:
                if platform.machine() == "aarch64" and platform.system() == "Linux":
                    display.start()

                driver = webdriver.Chrome(options=options)

                query = f"give me the latest geopolitical news in this week"
                encoded_url = urllib.parse.quote(query)
                driver.get(f"https://gemini.google.com/app")
                time.sleep(10)
                print(driver.title)

                main_page = WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, 'markdown'))
                )
                print(main_page)
                if main_page:
                    # find text-input-field_textarea-wrapper
                    input_field = driver.find_element(By.CLASS_NAME,'text-input-field_textarea-wrapper')
                    input_field.send_keys(query)
                    input_field.submit()
                    time.sleep(10)
                dynamic_elements = WebDriverWait(driver, 40).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, 'markdown'))
                )
                if dynamic_elements:
                    # Extract text and HTML from each element
                    for element in dynamic_elements:
                        html_content = element.get_attribute('innerHTML')
                        print(html_content)
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

        if len(answers) > 0:
            format_for_reddit(answers)
            print('Formatted Reddit Post:')
            # print(formatted_text)
        else:
            print('API error', answers)

    except Exception as e:
        print(e)
    finally:
        if driver:
            driver.quit()
        if platform.machine() == "aarch64" and platform.system() == "Linux":
            display.stop()
    return answers

if __name__ == '__main__':
    main_function()


