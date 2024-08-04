import os
from dotenv import load_dotenv

load_dotenv()

# Reddit API credentials
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
USER_AGENT = 'A lit af app fam'
REDDIT_USERNAME = os.environ.get("REDDIT_USERNAME")
PASSWORD = os.environ.get("PASSWORD")

# Subreddit configuration
SUBREDDIT = os.environ.get('SUBREDDIT')

# Whitelisted authors
WHITELIST_GEMINI = list(os.environ.get("WHITELIST_GEMINI", "").split(" "))

# Submission statement requirements
MIN_SUBMISSION_STATEMENT_LENGTH = 150

# Error messages
SUBMISSION_STATEMENT_TOO_SHORT = """Your Submission Statement is not long enough. Please make a lengthier Submission Statement in a new comment. Please DO NOT edit your comment and make a new one. Bots cannot re-read your edited comment."""

SUBMISSION_STATEMENT_FORMAT_INCORRECT = """Your Submission Statement should start with the term "SS" or "Submission Statement" (without the quotes). Please DO NOT edit your comment and make a new one. Bots cannot re-read your edited comment."""

# Other configuration settings
MBFC_JSON_PATH = './docs/MBFC_modified.json'

# Add more configuration variables as needed