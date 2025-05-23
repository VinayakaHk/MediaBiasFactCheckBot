import time
import threading
from typing import Optional
import praw
from src.config import WHITELIST_LLM, SUBMISSION_STATEMENT_TOO_SHORT, SUBMISSION_STATEMENT_FORMAT_INCORRECT, MIN_SUBMISSION_STATEMENT_LENGTH,REDDIT_USERNAME
from src.mongodb import store_comment_in_mongo, comment_body
from src.llm_automation import llm_detection
from src.reddit_utils import approve_submission
from src.exceptions import print_exception



def remove_and_reply(comment: praw.models.Comment, reply_body: str):
    """
    Remove a comment and reply with a specified message.

    Args:
        comment (praw.models.Comment): The comment to remove and reply to
        reply_body (str): The body of the reply message
    """
    comment.mod.remove()
    comment.mod.lock()
    reply = comment.reply(body=reply_body)
    reply.mod.distinguish()
    reply.mod.lock()



def monitor_comments(subreddit: praw.models.Subreddit, stop_threads: threading.Event):
    """
    Monitor new comments in the specified subreddit.

    Args:
        subreddit (praw.models.Subreddit): The subreddit to monitor
        stop_threads (threading.Event): Event to signal thread stoppage
    """
    while not stop_threads.is_set():
        try:
            for comment in subreddit.stream.comments(skip_existing=True):
                if comment is None:
                    continue
                
                print(f"Comment: {comment}, Author: {comment.author}")
                store_comment_in_mongo(comment)

                handle_comment(comment, subreddit)

                time.sleep(2)
        except praw.exceptions.RedditAPIException as e:
            print(f"API Exception: {e}")
            time.sleep(60)
        except Exception as e:
            print_exception()
            time.sleep(60)

def handle_comment(comment: praw.models.Comment, subreddit: praw.models.Subreddit):
    """
    Handle a new comment based on various conditions.

    Args:
        comment (praw.models.Comment): The comment to handle
        subreddit (praw.models.Subreddit): The subreddit the comment is in
    """
    try : 
        if comment.is_submitter and comment.parent_id == comment.link_id and not comment.submission.approved and str(comment.submission.removed_by).lower() == REDDIT_USERNAME.lower():
            if has_submission_statement(comment):
                print(f'Submission {comment.submission} approved. SS Comment: {comment}')
                approve_submission(comment.submission, comment, comment.submission.is_self)
        # elif not comment.removed and not comment.approved and not comment.spam and not comment.saved and comment.banned_by is None and comment.author not in WHITELIST_LLM:
        #     llm_comment(comment, subreddit.modmail)
    except Exception as e:
        print_exception()

def has_submission_statement(comment: praw.models.Comment) -> bool:
    """
    Check if a comment contains a valid submission statement.

    Args:
        comment (praw.models.Comment): The comment to check

    Returns:
        bool: True if the comment contains a valid submission statement, False otherwise
    """
    try: 
        lower_comment_body = comment.body.lower()
        if lower_comment_body.startswith("submission statement") or lower_comment_body.startswith("ss"):
            if len(comment.body) > MIN_SUBMISSION_STATEMENT_LENGTH:
                return True
            else:
                if not comment.removed:
                    remove_and_reply(comment, SUBMISSION_STATEMENT_TOO_SHORT)
                return False
        else:
            if not comment.removed:
                remove_and_reply(comment, SUBMISSION_STATEMENT_FORMAT_INCORRECT)
            return False
    except Exception as e:
        print_exception()


def llm_comment(comment: praw.models.Comment, mod_mail: praw.models.ModmailConversation):
    """
    Process a comment using llm detection.

    Args:
        comment (praw.models.Comment): The comment to process
        mod_mail (praw.models.ModmailConversation): The modmail conversation to use
    """
    try:
        parent_comment = comment_body(comment.id)
        threading.Thread(target=llm_detection, args=(comment, mod_mail, parent_comment)).start()
    except Exception as e:
        print_exception()
