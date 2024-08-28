import traceback
import re
import time
import os
import praw
import urllib.parse
import platform

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException

from pyvirtualdisplay import Display


from src.exceptions import print_exception

MAX_RETRIES = 3  # Maximum number of retry attempts
RETRY_DELAY = 2  # Delay (in seconds) between each retry attempt


from .mongodb import store_llm_in_comments

def element_strip(elem):
    return elem.text.strip()

def llm_detection (comment : praw.models.Comment, mod_mail : praw.models.ModmailConversation, parent_comment : praw.models.Comment):
    """
    A function that performs llm detection using the provided comment, mod_mail, and parent_comment.
    It checks for rule violations in the comment and takes appropriate actions based on the result.
    """
    try:
        dynamic_elements = []
        driver =  None
        for i in range(MAX_RETRIES):
dynamic_elements = []
driver = None
try:
    for i in range(MAX_RETRIES):
        try:
            if platform.machine() == "aarch64" and platform.system() == "Linux":
                display = Display(visible=0, size=(800, 600))
                display.start()

            driver = webdriver.Chrome()
            query = f"for context, `{parent_comment}` is the parent comment. Donot judge this. You are a moderator who disallows verbal abuse under Rule 2. Criticism is fair and allowed. Tell me if this comment starting and ending with violates the rule \n\n ```{comment.body}```.\n\n Your answer must start from True. if it violates the rules or False. if it doesnt violate the rules. Give a short reason in 80 characters"
            encoded_url = urllib.parse.quote(query)
            driver.get(f"https://you.com/search?q={encoded_url}&fromSearchBar=true&tbm=youchat")
            time.sleep(7)
            print(driver.title)

            dynamic_elements = WebDriverWait(driver, 30).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-testid="youchat-text"]'))
            )
            break  # If successful, break the loop

        except (WebDriverException, TimeoutException) as e:
            print(f"Error encountered: {str(e)}")
            time.sleep(RETRY_DELAY)
            if driver:
                driver.quit()
            if platform.machine() == "aarch64" and platform.system() == "Linux":
                display.stop()
            continue  # Retry if exception occurs

        finally:
            if driver:
                driver.quit()
            if platform.machine() == "aarch64" and platform.system() == "Linux":
                display.stop()

        # Continue processing the elements after loop
        if dynamic_elements:
            answer = ''.join([element_strip(elem) for elem in dynamic_elements])
            store_llm_in_comments(answer, comment.id)

        answer = ''
        for elem in dynamic_elements:
            text = element_strip(elem)
            answer += text

        # driver.quit()
        # if platform.machine() == "aarch64" and platform.system() == "Linux":
        #     display.stop()
        store_llm_in_comments(answer, comment.id)
        if answer.startswith('True.'):
            reason = answer.split('True.')
            if len(reason) > 100:
                reason = reason[:100]
            subject_body = f"""Rule breaking comment Detected by AI """
            if comment.parent_id == comment.link_id:
                subject_body = f"""Rule breaking comment removed by AI """
                comment.mod.remove()
                removal_message = f"""Hi u/{comment.author}, Your comment has been removed by our AI based system for the following reason : \n\n {
                reason[1]} \n\n *If you believe it was a mistake, then please [contact our moderators](https://www.reddit.com/message/compose/?to=/r/{os.environ.get('SUBREDDIT')}&subject=Incorrectly removed the comment&message=Comment Link: {comment.link_permalink}{comment.id}%0A%0A Here's why : )* """
                reply = comment.mod.send_removal_message(
                    message=removal_message, type='public_as_subreddit')
                reply.mod.lock()
            # mod_mail_body = f"""Author: [{comment.author}](https://www.reddit.com/r/{os.environ.get("SUBREDDIT")}/search/?q=author%3A{comment.author}&restrict_sr=1&type=comment&sort=new)\n\n
            # comment: {comment.body}\n\nComment Link : {comment.link_permalink}{comment.id}/?context=3 \n\nBots reason for removal: {reason[1]}"""
            # mod_mail.create(
            #     subject=subject_body,
            #     body=mod_mail_body,
            #     recipient=f"""u/{os.environ.get("MODERATOR1")}""")
            comment.save()
            # comment.report(reason)
        elif answer.startswith('False'):
            comment.save()
        else:
            print('API error', answer)

    except Exception as e:
        print_exception()