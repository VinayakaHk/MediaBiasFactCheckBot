import praw
import os
from dotenv import load_dotenv
load_dotenv()

# Initialize PRAW with your script credentials
reddit = praw.Reddit(client_id=os.environ.get("CLIENT_ID"),
                     client_secret=os.environ.get("CLIENT_SECRET"),
                     user_agent='A lit af app fam',
                     username=os.environ.get("REDDIT_USERNAME"),
                     password=os.environ.get("PASSWORD"),
                     check_for_async=False)


# Define the subreddit you're working with
subreddit_name = os.environ.get('SUBREDDIT')
subreddit = reddit.subreddit(subreddit_name)

# Fetch the list of flairs
flairs = list(subreddit.flair(limit=None))

# Loop through each flair
for flair in flairs:
    user = flair['user'].name
    flair_text = flair['flair_text']
    # Replace with the new flair text you want to set
    new_flair_text = ' '

    # Edit the flair
    subreddit.flair.set(user, new_flair_text)

    print(f"Updated flair for {user} to {new_flair_text}")
