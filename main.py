# from pymongo.errors import ConnectionFailure, PyMongoError
# from pymongo import MongoClient
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

import time
import sys
import linecache
import json
import re
import os
import praw
# import pprint
from src.mongodb import connect_to_mongo, store_comment_in_mongo, store_submission_in_mongo, comment_body
from src.gemini import gemini_detection
load_dotenv()

connect_to_mongo()

whitelisted_authors_from_Gemini = list(
    os.environ.get("WHITELIST_GEMINI").split(" "))

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
print('subreddit ', subreddit)
mod_mail = subreddit.modmail


def PrintException():
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

    text += f"""\nThis rating was provided by Media Bias Fact Check. For more information, see {
        obj['name']}'s review [here]({obj['profile']}).
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
        PrintException()
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
                    'Your Submission Statement is not long enough, Please make a lengthier Submission Statement in a new comment. Please DO NOT edit your comment and make a new one. Bots cannot re-read your edited comment'
                )
                reply.mod.distinguish()
                reply.mod.lock()

            return False
    else:
        if not comment.removed:
            comment.mod.remove()
            comment.mod.lock()
            reply = comment.reply(
                'Your Submission Statement should start with the term "SS" or "Submission Statement" (without the " ").  Please DO NOT edit your comment and make a new one. Bots cannot re-read your edited comment.'
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
to get your post approved. Make sure its about 2-3 paragraphs long.
\n\nIf you need assistance with writing a submission Statement, please refer https://reddit.com/r/{
                os.environ.get('SUBREDDIT')}/wiki/submissionstatement/ ."""
        )
        message.mod.lock()
        return message
    except praw.exceptions.RedditAPIException as e:
        print(f"API Exception: {e}")
        time.sleep(60)
    except:
        PrintException()
        time.sleep(60)


def add_prefix_to_paragraphs(input_string):
    formatted_string = re.sub(r'\n+', '\n>\n>', input_string)
    formatted_string = re.sub(r'(?<=\n\n)(?=[^\n])', "> ", formatted_string)
    return formatted_string


def get_reply_text(domains, urls, comment=None):
    archive_links = f"""
🔗 **Archive**:
---
"""

    for index, url in enumerate(urls):
        archive_links += f"""* [archive.today - {domains[index]}
            ](https://archive.is/submit/?submitid=&url={url}) | """
        archive_links += f"""[Google Webcache - {
            domains[index]}](http://webcache.googleusercontent.com/search?q=cache:{url})\n"""

    formatted_string = add_prefix_to_paragraphs(
        comment.body) if comment else ""

    submission_statement = f"""
📣 **[Submission Statement from OP]({comment.permalink})**:
> {formatted_string}
""" if comment else ""

    base_text = f"""
---
**Post Approved**: Your submission has been approved!
{archive_links}
{submission_statement}
***
📜 Community Reminder: Let’s keep our discussions civil, respectful, and on-topic. Abide by the subreddit rules. Rule-violating comments may be removed.
***
"""

    for domain in domains:
        if domain:
            additional_text = mbfc_political_bias(domain)
            if additional_text:
                base_text += "\n\n" + additional_text

    footer = f"""
❓ Questions or concerns? [Contact our moderators](https://www.reddit.com/message/compose/?to=/r/{os.environ.get('SUBREDDIT')}).
"""

    return base_text + footer


# Function to approve a submission if it has a submission statement in its comments
def approve_submission(submission, comment=None, is_self=True):
    try:
        submission.mod.approve()
        submission.comments.replace_more(limit=None)
        print("comment from edit_geoind_comment : ", comment)
        # Delete previous comments made by the bot
        for top_level_comment in submission.comments:
            if (top_level_comment.author == reddit.user.me()):
                top_level_comment.delete()
        if (is_self == False):
            url = str(submission.url)
            domain = re.search('https?://([A-Za-z_0-9.-]+).*', url).group(1)
            domain = [domain]
            url = [url]
            reply_text = get_reply_text(domain, url, comment)
            reply = submission.reply(reply_text)
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
                reply = submission.reply(reply_text)
                reply.mod.distinguish(sticky=True)
                reply.mod.lock()
            else:
                reply_text = get_reply_text(domains, urls, comment)

                reply = submission.reply(reply_text)
                reply.mod.distinguish(sticky=True)
                reply.mod.lock()
    except praw.exceptions.RedditAPIException as e:
        print(f"API Exception: {e}")
        time.sleep(60)
    except:
        PrintException()
        time.sleep(60)


def gemini_comment(comment):
    try:
        global mod_mail
        parent_comment = comment_body(comment.id)
        gemini_result = gemini_detection(
            comment.body, parent_comment, comment.link_title)
        if int(gemini_result['answer']) > 90:
            if (comment.parent_id == comment.link_id):
                comment.mod.remove()
                removal_message = f"""Hi u/{comment.author}, Your comment has been removed by our AI based system for the following reason : \n\n {
                    gemini_result['reason']} \n\n *If you believe it was a mistake, then please [contact our moderators](https://www.reddit.com/message/compose/?to=/r/{os.environ.get('SUBREDDIT')})* """

                reply = comment.mod.send_removal_message(
                    message=removal_message, type='public_as_subreddit')

                reply.mod.lock()
            mod_mail_body = f"""Author: [{comment.author}](https://www.reddit.com/r/{os.environ.get("SUBREDDIT")}/search/?q=author%3A{comment.author}&restrict_sr=1&type=comment&sort=new)\n\ncomment: {
                comment.body}\n\nComment Link : {comment.link_permalink}{comment.id}/?context=3 \n\nBots reason for removal: {gemini_result['reason']}"""
            mod_mail.create(
                subject=f"""Rule breaking comment by Gemini - {
                    gemini_result['answer']}%""",
                body=mod_mail_body,
                recipient=f"""u/{os.environ.get("MODERATOR1")}""")
            comment.save()
    except Exception as e:
        PrintException()
        time.sleep(60)


def monitor_submission():
    while True:
        try:
            print('monitor_submission:')

            for submission in subreddit.stream.submissions():
                if (submission != None):
                    print("Submission : ", submission, "Approved : ", submission.approved,
                          submission.removed_by)
                    store_submission_in_mongo(submission)
                    if(submission.author == 'AutoModerator'):
                        submission.mod.approve()
                    else if submission != None and submission.approved == False and submission.removed == False :
                        if not submission.is_self:
                            print("Submission filtered : ", submission)

                            message = send_to_modqueue(submission)
                        else:
                            if len(submission.selftext) > 200:
                                approve_submission(submission, None, True)

                            else:
                                print("Self Text filtered : ", submission)
                                message = send_to_modqueue(submission)
                time.sleep(2)
        except praw.exceptions.RedditAPIException as e:
            print(f"API Exception: {e}")
            time.sleep(60)
        except:
            PrintException()
            time.sleep(60)


def monitor_comments():
    while True:
        try:
            print('monitor_comments:')
            for comment in subreddit.stream.comments():
                try:
                    if (comment != None):
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
                                    comment.submission,  comment, False)
                        if comment.removed == False and comment.approved == False and comment.spam == False and comment.saved == False and comment.banned_by == None and (comment.author not in whitelisted_authors_from_Gemini) and (len(comment.body) <= 1000):
                            gemini_comment(comment)
                    time.sleep(2)
                except Exception as e:
                    PrintException()
                    time.sleep(60)
        except praw.exceptions.RedditAPIException as e:
            print(f"API Exception: {e}")
            time.sleep(60)
        except:
            PrintException()
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
        exit()
    except:
        print("Error ")
        process_submission.terminate()
        process_comments.terminate()
        time.sleep(60)
        process_submission.start()
        process_comments.start()


if __name__ == '__main__':
    main()
