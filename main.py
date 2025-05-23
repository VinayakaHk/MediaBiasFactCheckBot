import threading
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from src.config import SUBREDDIT
from src.reddit_utils import initialize_reddit
from src.submission_handler import monitor_submission
from src.comment_handler import monitor_comments
from src.exceptions import print_exception

load_dotenv()

def main():
    try:
        reddit = initialize_reddit()
        subreddit = reddit.subreddit(SUBREDDIT)
        stop_threads = threading.Event()

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_submission = executor.submit(monitor_submission, subreddit, stop_threads)
            future_comments = executor.submit(monitor_comments, subreddit, stop_threads)

            if future_submission.exception():
                print(f"Error in monitor_submission: {future_submission.exception()}")
            if future_comments.exception():
                print(f"Error in monitor_comments: {future_comments.exception()}")
    except KeyboardInterrupt:
        print('Monitoring stopped.')
        stop_threads.set()
        future_submission.result()
        future_comments.result()
    except Exception as e:
        print_exception()

if __name__ == '__main__':
    main()