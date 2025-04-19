from datetime import datetime

from src.reddit_utils import initialize_reddit
from src.config import SUBREDDIT
from src.get_latest_news import get_latest_news

def create_weekly_discussion():
    reddit = initialize_reddit()
    subreddit = reddit.subreddit(SUBREDDIT)


    # Create post title with current date
    current_date = datetime.now().strftime("%d %B, %Y")
    post_title = f"Weekly Discussion Thread - {current_date}"

    # Post content
    post_body = """
Welcome to this week's discussion thread! 

This thread is dedicated to exploring and discussing geopolitics . We will cover a wide range of topics, including current events, global trends, and potential developments.
Please feel free to participate by sharing your own insights, analysis, or questions related to the geopolitical news.

Here are some trending news this week: 
"""
    # Get latest news
    latest_news = get_latest_news()
    if latest_news:
        post_body += f"\n\n{latest_news}"

        post_body += "\n\n---\n\n"
        post_body += "Please feel free to share your thoughts, questions, or any other relevant discussions on this topic."
        post_body += "\n\n---\n\n"
        post_body += "I hope you have a great week!"
        new_post = subreddit.submit(
            title=post_title,
            selftext=post_body,
            send_replies=False
        )
        new_post.mod.sticky(state=True, bottom=False)
        return new_post.url
    else:
        print("No news found.")
        return None
post_url = create_weekly_discussion()
print(f"Weekly discussion post created and pinned: {post_url}")