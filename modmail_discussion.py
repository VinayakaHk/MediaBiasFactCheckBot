from src.config import SUBREDDIT, CONVERSATION_ID
from src.reddit_utils import initialize_reddit
from src.modmail_handler import extract_moderator_links 
reddit = initialize_reddit()
urls = extract_moderator_links(reddit=reddit,conversation_id=CONVERSATION_ID, subreddit=SUBREDDIT)
print("Links from human moderators:")
if len(urls) == 0:
    print("No links found.")
else:    
    print(f"- {urls}")
