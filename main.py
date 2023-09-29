import praw
import time
import multiprocessing
from dotenv import load_dotenv
import os
import re
import json
import linecache
import sys
from keep_alive import keep_alive

keep_alive()
load_dotenv()

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
  text = f"""\n\n**📰 Media Bias fact Check Rating :**  \n\n\n\n
|Metric|Rating|
|:-|:-|
|Bias Rating|{obj['bias']}|
|Factual Rating| {obj['factual']}|
"""
  credibility = obj.get("credibility", "no credibility rating available")
  if credibility != "no credibility rating available":
    text += f"|Credibility Rating|{obj['credibility']}|\n"

  text += f"""\nThis rating was provided by Media Bias Fact Check. For more information, see {obj['name']}'s review [here]({obj['profile']})."""
  return text


def mbfc_political_bias(domain_url):
  try:
    if not hasattr(mbfc_political_bias, "data"):
      with open('MBFC.json', 'r') as mbfc_file:
        mbfc_political_bias.data = json.load(mbfc_file)

    for i in mbfc_political_bias.data:
      if not i['url'] == "no url available":
        url = i['url']
        domain = re.search('https?://([A-Za-z_0-9.-]+).*', url).group(1)
        if domain == domain_url:
          text = print_mbfc_text(domain, i)
          return text
    return None
  except:
    PrintException()


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
            'Your Submission Statement is not long enough, Please make a lengthier Submission Statement in a new comment. Please donot edit your comment and make a new one. Bots cannot re-read your edited comment'
        )
        reply.mod.distinguish()
        reply.mod.lock()

      return False
  else:
    if not comment.removed:
      comment.mod.remove()
      comment.mod.lock()
      reply = comment.reply(
          'Your Submission Statement should start with the term "SS" or "Submission Statement". Please donot edit your comment and make a new one. Bots cannot re-read your edited comment.'
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
        message=
        'Your submission has been filtered until you enter a Submission Statement. Please add "Submission Statement" or "SS" while writing a submission Statement to get your post approved. Make sure its about 3-5 paragraphs long. \n\nIf you need assistance with writing a submission Statement, please refer https://reddit.com/r/geopoliticsIndia/wiki/submissionstatement/ for more information.'
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
  # Use regular expression to match multiple consecutive newline characters
  # and replace them with just two newline characters
  formatted_string = re.sub(r'\n+', '\n\n', input_string)

  # Add "> " to the start of each paragraph
  formatted_string = re.sub(r'(?<=\n\n)(?=[^\n])', "> ", formatted_string)

  return formatted_string


def get_reply_text(domain, url, comment):
  archive_links = f"""
🔗 **Archive**:
* [archive.today](https://archive.is/submit/?submitid=&url={url}) 
* [archive.today for Reddit App users](https://archive.is/{url})
* [WayBack Machine](https://web.archive.org/web/{url})
* [Google Webcache](http://webcache.googleusercontent.com/search?q=cache:{url})
"""
  formatted_string = add_prefix_to_paragraphs(comment.body)

  submission_statement = f"""
📣 **[Submission Statement from OP]({comment.permalink})**:
> {formatted_string}
""" if comment else ""

  base_text = f"""
---
**Post Approved**: Your submission has been approved!
{archive_links}
{submission_statement}
---

📜 **Community Reminder**: Let’s keep our discussions civil, respectful, and on-topic. Abide by the subreddit rules. Rule-violating comments may be removed.
"""

  if domain:
    additional_text = mbfc_political_bias(domain)
    if additional_text:
      base_text += "\n\n" + additional_text

  footer = """\n
❓ Questions or concerns? [Contact our moderators](https://www.reddit.com/message/compose/?to=/r/GeopoliticsIndia).
"""

  return base_text + footer


def edit_geoind_comment(submission, comment):
  try:
    submission.comments.replace_more(limit=None)
    print("comment from edit_geoind_comment : ", comment)
    # Delete previous comments made by the bot
    for top_level_comment in submission.comments:
      if (top_level_comment.author == reddit.user.me()):
        top_level_comment.delete()

    url = str(submission.url)
    domain = re.search('https?://([A-Za-z_0-9.-]+).*', url).group(1)

    reply_text = get_reply_text(domain, url, comment)
    reply = submission.reply(reply_text)
    reply.mod.distinguish(sticky=True)
    reply.mod.lock()

  except praw.exceptions.RedditAPIException as e:
    print(f"API Exception: {e}")
    time.sleep(60)
  except Exception as e:
    # You'll need to define the 'PrintException' function elsewhere, or replace with 'print'
    print(f"Exception: {e}")
    time.sleep(60)


# Function to approve a submission if it has a submission statement in its comments


def approve_submission(submission, comment=None):
  try:
    f = open('removed.txt', 'a')
    f.write(str(submission.id) + '\n')
    f.close()

    submission.mod.approve()
    edit_geoind_comment(submission, comment)
  except praw.exceptions.RedditAPIException as e:
    print(f"API Exception: {e}")
    time.sleep(60)
  except:
    PrintException()
    time.sleep(60)


# Function to monitor a single submission and wait for the author to add a submission statement
def monitor_submission():
  while True:
    try:
      print('monitor_submission:')
      f = open('removed.txt', 'r')
      IDs = f.readlines()
      for submission in subreddit.stream.submissions():
        print("Submission : ", submission, "Approved : ", submission.approved,
              submission.removed_by)
        if submission != None and str(
            submission.id
        ) not in IDs and submission.approved == False and submission.removed == False:
          if not submission.is_self:
            print("Submission filtered : ", submission)
            f.close()
            message = send_to_modqueue(submission)
          else:
            if len(submission.selftext) > 200:
              approve_submission(submission)
              f.close()
            else:
              print("Self Text filtered : ", submission)
              f.close()
              message = send_to_modqueue(submission)
        time.sleep(0.5)
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
        if (comment != None):
          print("comment: ", comment)
          if comment.is_submitter and comment.parent_id == (
              't3_' + comment.submission.id
          ) and comment.submission.approved == False and comment.submission.removed_by == reddit.user.me(
          ):
            if has_submission_statement(comment):
              print('Submission ', comment.submission,
                    'approved. SS Comment : ', comment)
              approve_submission(comment.submission, comment)

    except praw.exceptions.RedditAPIException as e:
      print(f"API Exception: {e}")
      time.sleep(60)
    except:
      PrintException()
      time.sleep(60)


# Start monitoring new submissions
if __name__ == '__main__':
  try:
    process_submission = multiprocessing.Process(target=monitor_submission)
    process_submission.start()
    process_comments = multiprocessing.Process(target=monitor_comments)
    process_comments.start()
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
