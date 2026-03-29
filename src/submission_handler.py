import time
import threading
import praw
from src.config import MIN_SUBMISSION_STATEMENT_LENGTH
from src.mongodb import (
    store_submission_in_mongo, init_submission_state,
    transition_to_awaiting_ss, transition_to_approved, STATE_APPROVED
)
from src.reddit_utils import send_to_modqueue, approve_submission
from src.exceptions import logger


def monitor_submission(subreddit: praw.models.Subreddit, stop_threads: threading.Event):
    while not stop_threads.is_set():
        try:
            for submission in subreddit.stream.submissions(skip_existing=True):
                if submission is None:
                    continue

                logger.info(f"Submission: {submission}, Approved: {submission.approved}, Removed by: {submission.removed_by}")
                store_submission_in_mongo(submission)

                if submission.author == 'AutoModerator':
                    submission.mod.approve()
                elif not submission.approved and not submission.removed:
                    handle_new_submission(submission)

                time.sleep(2)
        except praw.exceptions.RedditAPIException:
            logger.exception("Reddit API error in submission monitor")
            time.sleep(60)
        except Exception:
            logger.exception("Unexpected error in submission monitor")
            time.sleep(60)


def handle_new_submission(submission: praw.models.Submission):
    try:
        state_doc = init_submission_state(str(submission.id))
        if not state_doc or state_doc['state'] == STATE_APPROVED:
            return

        if submission.is_self and len(submission.selftext) > 200:
            if transition_to_approved(str(submission.id)):
                approve_submission(submission, None, True)
            return

        # Needs an SS — remove and transition to awaiting_ss
        is_self = submission.is_self
        send_to_modqueue(submission, is_self)
        transition_to_awaiting_ss(str(submission.id))

        # Scan existing comments in case SS arrived before we processed the submission
        ss_comment = scan_existing_comments_for_ss(submission)
        if ss_comment:
            if transition_to_approved(str(submission.id), str(ss_comment.id)):
                logger.info(f"Submission {submission} approved from existing SS comment {ss_comment}")
                approve_submission(submission, ss_comment, is_self)
    except Exception:
        logger.exception("Error handling new submission")


def scan_existing_comments_for_ss(submission: praw.models.Submission):
    """Check if any existing top-level comment by OP is a valid SS."""
    try:
        submission.comments.replace_more(limit=0)
        for comment in submission.comments:
            if not comment.is_submitter:
                continue
            if comment.parent_id != comment.link_id:
                continue
            lower_body = comment.body.lower()
            if (lower_body.startswith("submission statement") or lower_body.startswith("ss")) \
                    and len(comment.body) > MIN_SUBMISSION_STATEMENT_LENGTH:
                return comment
        return None
    except Exception:
        logger.exception("Error scanning existing comments for SS")
        return None
