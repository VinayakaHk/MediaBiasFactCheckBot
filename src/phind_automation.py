import traceback
import re
import time
import os
MAX_RETRIES = 3  # Maximum number of retry attempts
RETRY_DELAY = 2  # Delay (in seconds) between each retry attempt


def retry_on_failure(func, *args, **kwargs):
    retries = 0
    while retries < MAX_RETRIES:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            retries += 1
            if retries == MAX_RETRIES:
                raise e
            print(f"Error occurred: {e}. Retrying in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)


def extract_text_from_element(element):
    return element.text.strip()

def phind_detection( comment,mod_mail):
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.keys import Keys
        # Set up Chrome options
        options = webdriver.FirefoxOptions()
        options.add_argument("--start-maximized")  # Optionally adjust window size
        # Initialize the web driver
        driver = webdriver.Firefox(options=options)
        # Navigate to the picYard website
        driver.get("https://www.phind.com/")
        time.sleep(2)  # Asynchronous sleep
        textbox = driver.find_element(By.CSS_SELECTOR, '.searchbox-textarea')
        textbox.send_keys(
            f"You are a moderator who disallows abuse, trolling and personal attacks under Rule 2. Tell me if this comment violates the rule {comment.body}. Your answer must start from True if it violates the rules  or False if it doesnt violate the rules. Give a reason for it",
            Keys.ENTER)

        time.sleep(2)  # Asynchronous sleep
        initial_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//div[@class="fs-5"]'))
        )

        # Keep track of the length of the parent elements containing the dynamic elements
        prev_length = len(driver.find_elements(By.XPATH, '//div[@class="fs-5"]'))

        # Wait and continuously check if new dynamic elements are added
        start_time = time.time()
        while True:
            time.sleep(5)  # Asynchronous sleep  # Wait for 5 seconds before checking again

            # Check the current length of the parent elements
            current_length = len(driver.find_elements(By.XPATH, '//div[@class="fs-5"]'))

            # If the length remains the same after waiting, assume all elements are loaded
            if current_length == prev_length:
                break

            # If the total wait time exceeds 60 seconds, exit the loop to prevent infinite waiting
            if time.time() - start_time > 60:
                print("Timeout occurred while waiting for all elements to load")
                break

            # Update the previous length for the next iteration
            prev_length = current_length

        # Once all elements are loaded, extract text from each dynamic element
        dynamic_elements = driver.find_elements(By.XPATH, '//div[@class="fs-5"]')
        answer = ''
        for elem in dynamic_elements:
            text = extract_text_from_element(elem)
            answer += text
        print('answer : ', answer)

        driver.quit()
        # return answer
        if answer.startswith('True.'):
            reason = answer.split('True.')
            print('reason', reason[1])
            subject_body = f"""Rule breaking comment Removed by AI -"""

            if (comment.parent_id == comment.link_id):
                comment.mod.remove()
                removal_message = f"""Hi u/{comment.author}, Your comment has been removed by our AI based system for the following reason : \n\n {
                reason[1]} \n\n *If you believe it was a mistake, then please [contact our moderators](https://www.reddit.com/message/compose/?to=/r/{os.environ.get('SUBREDDIT')})* """

                reply = comment.mod.send_removal_message(
                    message=removal_message, type='public_as_subreddit')

                reply.mod.lock()
            mod_mail_body = f"""Author: [{comment.author}](https://www.reddit.com/r/{os.environ.get("SUBREDDIT")}/search/?q=author%3A{comment.author}&restrict_sr=1&type=comment&sort=new)\n\ncomment: {
            comment.body}\n\nComment Link : {comment.link_permalink}{comment.id}/?context=3 \n\nBots reason for removal: {reason[1]}"""
            mod_mail.create(
                subject=subject_body,
                body=mod_mail_body,
                recipient=f"""u/{os.environ.get("MODERATOR1")}""")
            comment.save()
        elif answer.startswith('False'): 
            print('Comment Does not violate the rules')
            comment.save()
        else : 
            print('API error')

    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        # Find the line number where the exception occurred
        # Use a regular expression to extract the line number
        line_number_match = re.search(r'File ".*", line (\d+)', tb)
        if line_number_match:
            line_number = line_number_match.group(1)
            print(f"An error occurred on line {line_number}: {e}")
        else:
            print(f"An error occurred: {e}")
            print("Unable to extract line number from traceback.")

        print(f"An error occurred: {e}")
    finally:
        driver.quit()