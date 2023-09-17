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
reddit = praw.Reddit(client_id=os.getenv("CLIENT_ID"),
                     client_secret=os.getenv("CLIENT_SECRET"),
                     user_agent='A lit af app fam',
                     username=os.getenv("REDDIT_USERNAME"),
                     password=os.getenv("PASSWORD"),
                     check_for_async=False)

# Define the subreddit you want to monitor
subreddit_name = os.getenv("SUBREDDIT")
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
  text = f"""\n\n\n\n
|Metric|Rating|
|:-|:-|
|Bias Rating|{obj['bias']}|
|Factual Rating| {obj['factual']}|
"""
  credibility = obj.get("credibility", "no credibility rating available")
  if credibility != "no credibility rating available":
    text += f"|Credibility Rating|{obj['credibility']}|\n"

  text += f"""\nThis rating was provided by Media Bias Fact Check. For more information, see {obj['name']}'s review [here]({obj['profile']}). \n\n*I am a bot, and this action was performed automatically. Please [contact the moderators of this subreddit](https://www.reddit.com/message/compose/?to=/r/GeopoliticsIndia) if you have any questions or concerns.*
"""
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
      comment.mod.remove()
      comment.mod.lock()
      reply = comment.reply(
        'Your Submission Statement is not long enough, Please make a lengthier Submission Statement in a new comment. Please donot edit your comment and make a new one. Bots cannot re-read your edited comment'
      )
      reply.mod.distinguish()
      reply.mod.lock()

      return False
  else:
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
  except praw.exceptions.APIException as e:
    print(f"API Exception: {e}")
  except:
    PrintException()
    time.sleep(60)


def edit_geoind_comment(submission):
  try:
    comments = submission.comments
    comments.replace_more(limit=None)
    for top_level_comment in comments:
      if (top_level_comment.author == reddit.user.me()):
        top_level_comment.delete()
        url = submission.url
        url = str(url)
        domain = re.search('https?://([A-Za-z_0-9.-]+).*', url).group(1)
        text = mbfc_political_bias(domain)
        if text is not None:
          reply_text = f"""Archive URL : [archive.is](https://archive.is/submit/?submitid=&url={url}) | [archive.org](https://web.archive.org/web/{url})\n\nThis is an automated message to inform you that your post has been approved by the r/geopoliticsIndia bot. We believe it contributes to the insightful and respectful discussions we strive to foster in this community.

As always, we kindly remind all commenters to adhere to the subreddit rules. Let’s ensure our discussions remain civil, respectful, and focused on the topic at hand. Any comments that violate these rules may be removed by the bot.
""" + text
        else:
          reply_text = f"""Archive URL : [archive.is](https://archive.is/submit/?submitid=&url={url}) | [archive.org](https://web.archive.org/web/{url})\n\nThis is an automated message to inform you that your post has been approved by the r/geopoliticsIndia bot. We believe it contributes to the insightful and respectful discussions we strive to foster in this community.

As always, we kindly remind all commenters to adhere to the subreddit rules. Let’s ensure our discussions remain civil, respectful, and focused on the topic at hand. Any comments that violate these rules may be removed by the bot."""
        reply = submission.reply(reply_text)
        reply.mod.distinguish(sticky=True)
        reply.mod.lock()
        time.sleep(10)
  except praw.exceptions.APIException as e:
    print(f"API Exception: {e}")
  except:
    PrintException()
    time.sleep(60)


# Function to approve a submission if it has a submission statement in its comments
def approve_submission(submission):
  try:
    f = open('approved.txt', 'a')
    f.write(str(submission.id) + '\n')
    f.close()

    submission.mod.approve()
    edit_geoind_comment(submission)
  except praw.exceptions.APIException as e:
    print(f"API Exception: {e}")
  except:
    PrintException()
    time.sleep(60)


# Function to monitor a single submission and wait for the author to add a submission statement
def monitor_submission():
  while True:
    try:
      print('monitor_submission:')
      f = open('approved.txt', 'r')
      IDs = f.readlines()
      for submission in subreddit.stream.submissions():
        print("Submission : ", submission, "Approved : ", submission.approved,
              submission.removed_by)
        if submission != None and str(
            submission.id
        ) not in IDs and submission.approved == False and submission.removed == False:
          print("Submission : ", submission)
          f.close()
          message = send_to_modqueue(submission)
        time.sleep(2)
    except praw.exceptions.APIException as e:
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
              approve_submission(comment.submission)
        time.sleep(2)
    except praw.exceptions.APIException as e:
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
