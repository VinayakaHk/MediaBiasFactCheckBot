import signal
import threading
import time
from dotenv import load_dotenv
from src.config import SUBREDDIT
from src.reddit_utils import initialize_reddit, approve_submission
from src.submission_handler import monitor_submission
from src.comment_handler import monitor_comments
from src.mongodb import get_stale_awaiting_ss, transition_to_approved
from src.utils import is_valid_submission_statement
from src.exceptions import logger

load_dotenv()

SWEEP_INTERVAL = 120  # seconds between retry sweeps
STALE_THRESHOLD = 300  # consider awaiting_ss stale after 5 minutes


def retry_sweep(reddit, stop_threads: threading.Event):
    """Periodically scan submissions stuck in awaiting_ss for missed SS comments."""
    subreddit = reddit.subreddit(SUBREDDIT)
    while not stop_threads.is_set():
        try:
            stale = get_stale_awaiting_ss(STALE_THRESHOLD)
            for doc in stale:
                if stop_threads.is_set():
                    break
                try:
                    submission = reddit.submission(id=doc['submission_id'])
                    submission._fetch()

                    if submission.approved:
                        transition_to_approved(doc['submission_id'])
                        continue

                    submission.comments.replace_more(limit=0)
                    for comment in submission.comments:
                        if not comment.is_submitter or comment.parent_id != comment.link_id:
                            continue
                        if is_valid_submission_statement(comment.body):
                            if transition_to_approved(doc['submission_id'], str(comment.id)):
                                logger.info(f"Retry sweep: approved {submission} via comment {comment}")
                                approve_submission(submission, comment, submission.is_self)
                            break
                except Exception:
                    logger.exception(f"Retry sweep error for submission {doc['submission_id']}")
        except Exception:
            logger.exception("Retry sweep unexpected error")

        stop_threads.wait(SWEEP_INTERVAL)


def main():
    reddit = initialize_reddit()
    subreddit = reddit.subreddit(SUBREDDIT)
    stop_threads = threading.Event()

    threads = [
        (monitor_submission, (subreddit, stop_threads), "submissions"),
        (monitor_comments, (subreddit, stop_threads), "comments"),
        (retry_sweep, (reddit, stop_threads), "retry_sweep"),
    ]

    for target, args, name in threads:
        t = threading.Thread(target=target, args=args, name=name, daemon=True)
        t.start()

    try:
        signal.pause()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        stop_threads.set()


if __name__ == '__main__':
    main()
