import time
import threading
import praw
from src.config import (
    SUBMISSION_STATEMENT_TOO_SHORT,
    SUBMISSION_STATEMENT_FORMAT_INCORRECT
)
from src.mongodb import (
    store_comment_in_mongo, comment_body,
    get_submission_state, transition_to_approved,
    STATE_AWAITING_SS, STATE_APPROVED
)
from src.llm_automation import llm_detection
from src.reddit_utils import approve_submission
from src.exceptions import logger
from src.utils import exponential_backoff, is_valid_submission_statement


def remove_and_reply(comment: praw.models.Comment, reply_body: str):
    comment.mod.remove()
    comment.mod.lock()
    reply = comment.reply(body=reply_body)
    reply.mod.distinguish()
    reply.mod.lock()


def monitor_comments(subreddit: praw.models.Subreddit, stop_threads: threading.Event):
    attempt = 0
    while not stop_threads.is_set():
        try:
            for comment in subreddit.stream.comments(skip_existing=True):
                if comment is None:
                    continue
                attempt = 0  # reset on success

                logger.info(f"Comment: {comment}, Author: {comment.author}")
                store_comment_in_mongo(comment)
                handle_comment(comment)
                time.sleep(2)
        except praw.exceptions.RedditAPIException:
            logger.exception("Reddit API error in comment monitor")
            exponential_backoff(attempt)
            attempt += 1
        except Exception:
            logger.exception("Unexpected error in comment monitor")
            exponential_backoff(attempt)
            attempt += 1


def handle_comment(comment: praw.models.Comment):
    try:
        if not (comment.is_submitter and comment.parent_id == comment.link_id):
            return

        submission = comment.submission
        submission_id = str(submission.id)
        state_doc = get_submission_state(submission_id)

        # If no state doc yet, submission stream hasn't processed it — skip for now,
        # the submission handler will scan existing comments when it catches up.
        if not state_doc:
            return

        if state_doc['state'] == STATE_APPROVED:
            return

        if state_doc['state'] != STATE_AWAITING_SS:
            return

        if has_submission_statement(comment):
            if transition_to_approved(submission_id, str(comment.id)):
                logger.info(f'Submission {submission} approved. SS Comment: {comment}')
                approve_submission(submission, comment, submission.is_self)
            # else: another thread already approved it, nothing to do
    except Exception:
        logger.exception("Error handling comment")


def has_submission_statement(comment: praw.models.Comment) -> bool:
    try:
        if is_valid_submission_statement(comment.body):
            return True

        lower_body = comment.body.lower()
        starts_correct = lower_body.startswith("submission statement") or lower_body.startswith("ss")
        if not comment.removed:
            if starts_correct:
                remove_and_reply(comment, SUBMISSION_STATEMENT_TOO_SHORT)
            else:
                remove_and_reply(comment, SUBMISSION_STATEMENT_FORMAT_INCORRECT)
        return False
    except Exception:
        logger.exception("Error checking submission statement")
        return False


def llm_comment(comment: praw.models.Comment, mod_mail: praw.models.ModmailConversation):
    try:
        parent_comment = comment_body(comment.id)
        threading.Thread(target=llm_detection, args=(comment, mod_mail, parent_comment)).start()
    except Exception:
        logger.exception("Error starting LLM detection thread")
