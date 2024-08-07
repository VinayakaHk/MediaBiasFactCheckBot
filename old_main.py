# from pymongo.errors import ConnectionFailure, PyMongoError
# from pymongo import MongoClient
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import threading
from threading import Thread
import time
import sys
import linecache
import json
import re
import os
import praw
from src.mongodb import connect_to_mongo, store_comment_in_mongo, store_submission_in_mongo, comment_body
from src.llm_automation import llm_detection

load_dotenv()

connect_to_mongo()

stop_threads = threading.Event()

whitelisted_authors_from_llm = list(
    os.environ.get("WHITELIST_LLM").split(" "))

# Initialize PRAW with your credentials
reddit = praw.Reddit(client_id=os.environ.get("CLIENT_ID"),
                     client_secret=os.environ.get("CLIENT_SECRET"),
                     user_agent='A lit af app fam',
                     username=os.environ.get("REDDIT_USERNAME"),
                     password=os.environ.get("PASSWORD"),
                     check_for_async=False)

# Define the subreddit you want to monitor
subreddit_name = os.environ.get('SUBREDDIT')
subreddit = reddit.subreddit(subreddit_name)
mod_mail = subreddit.modmail


def print_exception():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno,
                                                       line.strip(), exc_obj))


def print_mbfc_text(domain, obj):
    text = f"""\n\n**📰 Media Bias fact Check Rating :**  {obj['name']} \n\n\n\n
|Metric|Rating|
|:-|:-|
|Bias Rating|{obj['bias']}|
|Factual Rating| {obj['factual']}|
"""
    credibility = obj.get("credibility", "no credibility rating available")
    if credibility != "no credibility rating available":
        text += f"|Credibility Rating|{obj['credibility']}|\n"

    text += f"""\nThis rating was provided by Media Bias Fact Check. For more information, see {obj['name']}'s review 
[here]({obj['profile']}).
***"""
    return text


def mbfc_political_bias(domain_url):
    try:
        with open('./docs/MBFC_modified.json', 'r') as mbfc_file:
            mbfc_data = json.load(mbfc_file)
        url_index = {entry["url"]: entry for entry in mbfc_data}

        if domain_url in url_index:
            retrieved_data = url_index[domain_url]
            text = print_mbfc_text(retrieved_data['url'], retrieved_data)
            return text
        else:
            print("URL not found in the index")
            return None

    except Exception as e:
        print('Exception ', e)
        print_exception()
        time.sleep(60)


# Function to check if a submission contains a submission statement in its comments
def has_submission_statement(comment):
    lower_comment_body = comment.body.lower()
    if lower_comment_body.startswith(
            "submission statement") or lower_comment_body.startswith("ss"):
        if len(comment.body) > 150:
            return True
        else:
            if not comment.removed:
                comment.mod.remove()
                comment.mod.lock()
                reply = comment.reply(
                    body='Your Submission Statement is not long enough, Please make a lengthier Submission Statement in a '
                         'new comment. Please DO NOT edit your comment and make a new one. Bots cannot re-read your edited '
                         'comment'
                    )
                reply.mod.distinguish()
                reply.mod.lock()

            return False
    else:
        if not comment.removed:
            comment.mod.remove()
            comment.mod.lock()
            reply = comment.reply(
                body='Your Submission Statement should start with the term "SS" or "Submission Statement" (without the " '
                     '").  Please DO NOT edit your comment and make a new one. Bots cannot re-read your edited comment.'
                )
            reply.mod.distinguish()
            reply.mod.lock()
            return False
    return False


# Function to send a submission to the modqueue
def send_to_modqueue(submission):
    try:
        submission.mod.remove()
        message = submission.mod.send_removal_message(
            message=f"""Your submission has been filtered until you comment a Submission Statement.
Please add "Submission Statement" or "SS" (without the " ") while writing a submission Statement
to get your post approved. Make sure its about 1-2 paragraphs long.
\n\nIf you need assistance with writing a submission Statement, please refer https://reddit.com/r/{os.environ.get('SUBREDDIT')}/wiki/submissionstatement/ ."""
        )
        message.mod.lock()
        return message
    except praw.exceptions.RedditAPIException as e:
        print(f"API Exception: {e}")
        time.sleep(60)
    except:
        print_exception()
        time.sleep(60)


def add_prefix_to_paragraphs(input_string):
    formatted_string = re.sub(r'\n+', '\n>\n>', input_string)
    formatted_string = re.sub(r'(?<=\n\n)(?=[^\n])', "> ", formatted_string)
    return formatted_string


def get_reply_text(domains, urls, comment=None):
    try:
        archive_links = f"""\n\n🔗 **Bypass paywalls**:\n\n"""
        for index, url in enumerate(urls):
            archive_links += f"""* [archive.today - {domains[index]}
                ](https://archive.is/submit/?submitid=&url={url}) | """
            archive_links += f"""[Google Webcache - {
            domains[index]}](http://webcache.googleusercontent.com/search?q=cache:{url})\n"""

        formatted_string = add_prefix_to_paragraphs(
            comment.body) if comment else ""

        submission_statement = f"""📣 **[Submission Statement by OP]({comment.permalink})**:\n> {formatted_string}""" if comment else ""

        base_text = f"""{archive_links}\n\n{submission_statement} \n\n**📜 Community Reminder**: Let’s keep our discussions civil, respectful, and on-topic. Abide by the subreddit rules. Rule-violating comments will be removed."""
        domains = list(set(domains))
        for domain in domains:
            if domain:
                additional_text = mbfc_political_bias(domain)
                if additional_text:
                    base_text += "\n\n" + additional_text

        footer = f"""\n\n❓ Questions or concerns? [Contact our moderators](https://www.reddit.com/message/compose/?to=/r/{os.environ.get('SUBREDDIT')})."""

        return base_text + footer
    except Exception as e:
        print('Exception occurred trying to create submission statement: ', e)


def approve_submission_old(submission, comment=None, is_self=True):
    try:
        submission.mod.approve()
        submission.comments.replace_more(limit=None)
        for top_level_comment in submission.comments:
            if (top_level_comment.author == reddit.user.me()):
                top_level_comment.delete()
        if (is_self == False):
            url = str(submission.url)
            domain = re.search('https?://([A-Za-z_0-9.-]+).*', url).group(1)
            domain = [domain]
            url = [url]
            reply_text = get_reply_text(domain, url, comment)
            reply = submission.reply(body=reply_text)
            reply.mod.distinguish(sticky=True)
            reply.mod.lock()
        else:
            full_text = submission.selftext
            url_pattern = re.compile(r'(https?://[^\s]+)')
            domain_pattern = re.compile(r'https?://([a-zA-Z0-9.-]+)')
            urls = url_pattern.findall(full_text)
            domains = domain_pattern.findall(full_text)
            if (domains == []):
                url = str(submission.url)
                domain = re.search(
                    'https?://([A-Za-z_0-9.-]+).*', url).group(1)
                domain = [domain]
                url = [url]
                reply_text = get_reply_text(domain, url, comment)
                reply = submission.reply(body=reply_text)
                reply.mod.distinguish(sticky=True)
                reply.mod.lock()
            else:
                reply_text = get_reply_text(domains, urls, comment)

                reply = submission.reply(body=reply_text)
                reply.mod.distinguish(sticky=True)
                reply.mod.lock()
    except praw.exceptions.RedditAPIException as e:
        print(f"API Exception: {e}")
        time.sleep(60)
    except:
        print_exception()
        time.sleep(60)


def approve_submission(submission, comment=None, is_self=True):
    try:
        submission.mod.approve()
        submission.comments.replace_more(limit=None)
        for top_level_comment in submission.comments:
            if top_level_comment.author == reddit.user.me():
                top_level_comment.delete()
        if not is_self:
            url = str(submission.url)
            domain = re.search('https?://([A-Za-z_0-9.-]+).*', url).group(1)
            domain = [domain]
            url = [url]
            reply_text = get_reply_text(domain, url, comment)
            reply = submission.reply(body=reply_text)
            reply.mod.distinguish(sticky=True)
            reply.mod.lock()
        else:
            urls = []
            domains = []
            full_text = submission.selftext
            # url_pattern = re.compile(r'\[?(https?://[^\s\]]+)')
            # domain_pattern = re.compile(r'https?://([a-zA-Z0-9.-]+)')
            url_pattern = re.compile(r'(https?://[^\]\s)]+)')
            domain_pattern = re.compile(r'https?://([a-zA-Z0-9.-]+)')

            url_matches = url_pattern.findall(full_text)
            domain_matches = domain_pattern.findall(full_text)
            if (domain_matches == []):
                url = str(submission.url)
                domain = re.search(
                    'https?://([A-Za-z_0-9.-]+).*', url).group(1)
                domain = [domain]
                url = [url]
                reply_text = get_reply_text(domain, url, comment)
                reply = submission.reply(body=reply_text)
                reply.mod.distinguish(sticky=True)
                reply.mod.lock()
            else:
                # Extract URLs and domains from the selftext
                for url, domain in zip(url_matches, domain_matches):
                    # Check if the URL is already in the list
                    if url not in urls:
                        urls.append(url)
                        domains.append(domain)
                # Generate reply text using the extracted domains and URLs
                reply_text = get_reply_text(domains, urls, comment)
                reply = submission.reply(body=reply_text)
                reply.mod.distinguish(sticky=True)
                reply.mod.lock()

    except praw.exceptions.RedditAPIException as e:
        print(f"API Exception: {e}")
        time.sleep(60)
    except Exception as e:
        print(f"Exception: {e}")
        time.sleep(60)


def llm_comment(comment):
    try:
        global mod_mail
        parent_comment = comment_body(comment.id)
        Thread(target=llm_detection, args=(comment, mod_mail, parent_comment,)).start()
        # llm_detection(comment, mod_mail,parent_comment)
    except Exception as e:
        print_exception()


def monitor_submission():
    while True:
        try:
            while not stop_threads.is_set():
                print('monitor_submission:')
                # skip_existing=True
                for submission in subreddit.stream.submissions():
                    try:
                        if (submission != None):
                            print("Submission : ", submission, "Approved : ", submission.approved,
                                  submission.removed_by)
                            store_submission_in_mongo(submission)
                            if (submission.author == 'AutoModerator'):
                                submission.mod.approve()
                            elif submission != None and submission.approved == False and submission.removed == False:
                                if not submission.is_self:

                                    print("Submission URL filtered: ", submission)

                                    message = send_to_modqueue(submission)
                                else:
                                    if len(submission.selftext) > 200:
                                        approve_submission(submission, None, True)

                                    else:
                                        print("Self Text filtered : ", submission)
                                        message = send_to_modqueue(submission)
                        time.sleep(2)
                    except Exception as e:
                        print_exception()
                        time.sleep(60)
                pass


        except KeyboardInterrupt:
            print("monitor_submission interrupted.")
        except praw.exceptions.RedditAPIException as e:
            print(f"API Exception: {e}")
            time.sleep(60)
        except:
            print_exception()
            time.sleep(60)


def monitor_comments():
    while True:
        try:
            while not stop_threads.is_set():
                print('monitor_comments:')
                # skip_existing=True
                for comment in subreddit.stream.comments():
                    try:
                        if comment is not None:
                            print("comment: ", comment,
                                  "author : ", comment.author)
                            store_comment_in_mongo(comment)

                            if comment.author == "empleadoEstatalBot":
                                comment.mod.approve()
                            if comment.is_submitter and comment.parent_id == comment.link_id and comment.submission.approved == False and comment.submission.removed_by == reddit.user.me(
                            ):
                                if has_submission_statement(comment):
                                    print('Submission ', comment.submission,
                                          'approved. SS Comment : ', comment)
                                    approve_submission(
                                        comment.submission, comment, bool(comment.submission.is_self))
                            elif comment.removed == False and comment.approved == False and comment.spam == False and comment.saved == False and comment.banned_by == None and (
                                    comment.author not in whitelisted_authors_from_llm):
                                llm_comment(comment)
                        time.sleep(2)
                    except Exception as e:
                        print_exception()
                        time.sleep(60)
                pass


        except KeyboardInterrupt:
            print("monitor_submission interrupted.")
        except praw.exceptions.RedditAPIException as e:
            print(f"API Exception: {e}")
            time.sleep(60)
        except:
            print_exception()
            time.sleep(60)


def main():
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_submission = executor.submit(monitor_submission)
            future_comments = executor.submit(monitor_comments)
        if future_submission.exception():
            print(f"""Error in monitor_submission{
            future_submission.exception()}""")
        if future_comments.exception():
            print(f"""Error in monitor_comments: {
            future_comments.exception()}""")
    except KeyboardInterrupt:
        print('Monitoring stopped.')
        stop_threads.set()
        # Wait for the threads to finish
        future_submission.result()
        future_comments.result()
        exit()
    except Exception as e:
        print("Error ", e)
        time.sleep(60)
        main()


if __name__ == '__main__':
    main()
