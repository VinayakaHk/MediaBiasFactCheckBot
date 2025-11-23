import os 
from datetime import datetime

from src.reddit_utils import initialize_reddit
from src.config import SUBREDDIT
from src.get_latest_news import get_latest_news

def post_with_summaries():
    reddit = initialize_reddit()
    subreddit = reddit.subreddit(SUBREDDIT)
    with open("summaries.json", "r") as f:
        summaries = f.read()
    # Create post title with current date
    current_date = datetime.now().strftime("%d %B, %Y")
    post_title = f"Weekly Discussion Thread - {current_date}"
    
    # Post content
    post_url = summaries[0]["url"]
    new_post = subreddit.submit(
        title=post_title,
        selftext=post_body,
        send_replies=False
    )
    return new_post.url