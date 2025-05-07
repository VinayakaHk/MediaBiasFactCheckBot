import time
from typing import Optional
import praw
from src.config import SUBREDDIT
from src.mongodb import store_submission_in_mongo
from src.reddit_utils import send_to_modqueue, approve_submission
from src.exceptions import print_exception
import threading

def monitor_submission(subreddit: praw.models.Subreddit, stop_threads: threading.Event):
    """
    Monitor new submissions in the specified subreddit.

    Args:
        subreddit (praw.models.Subreddit): The subreddit to monitor
        stop_threads (threading.Event): Event to signal thread stoppage
    """
    while not stop_threads.is_set():
        try:
            for submission in subreddit.stream.submissions(skip_existing=True):
                if submission is None:
                    continue
                
                print(f"Submission: {submission}, Approved: {submission.approved}, Removed by: {submission.removed_by}")
                store_submission_in_mongo(submission)

                if submission.author == 'AutoModerator':
                    submission.mod.approve()
                elif not submission.approved and not submission.removed:
                    handle_new_submission(submission)

                time.sleep(2)
        except praw.exceptions.RedditAPIException as e:
            print(f"API Exception: {e}")
            time.sleep(60)
        except Exception as e:
            print_exception()
            time.sleep(60)

def handle_new_submission(submission: praw.models.Submission):
    """
    Handle a new submission by either sending it to the modqueue or approving it.

    Args:
        submission (praw.models.Submission): The submission to handle
    """
    try :
        if not submission.is_self:
            print(f"Submission URL filtered: {submission}")
            send_to_modqueue(submission, False )
        else:
            if len(submission.selftext) > 200:
                approve_submission(submission, None, True)
            else:
                print(f"Self Text filtered: {submission}")
                send_to_modqueue(submission, True)
    except Exception as e:
        print_exception()
# Add more submission-related functions here