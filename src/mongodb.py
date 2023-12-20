from pymongo.errors import ConnectionFailure, PyMongoError
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os
import sys
import linecache
import time
import praw
load_dotenv()


MAX_RETRIES = 10
RETRY_DELAY = 10


# def praw_integration(client):
#     db = client['reddit_clone']
#     comments = db['comments']
#     submission = db['submissions']
#     reddit = praw.Reddit(client_id=os.environ.get("CLIENT_ID"),
#                          client_secret=os.environ.get("CLIENT_SECRET"),
#                          user_agent='A lit af app fam',
#                          username=os.environ.get("REDDIT_USERNAME"),
#                          password=os.environ.get("PASSWORD"),
#                          check_for_async=False)

#     # Define the subreddit you want to monitor
#     subreddit_name = os.environ.get('SUBREDDIT')
#     subreddit = reddit.subreddit(subreddit_name)
#     for submission in subreddit.hot(limit=10):
#         submission.comments.replace_more(limit=None)
#         for comment in submission.comments.list():
#             comments.insert_one(comment)


def connect_to_mongo():
    retries = 0
    while retries < MAX_RETRIES:
        try:
            # Create a new client and connect to the server
            client = MongoClient(os.environ.get("MONGODB"),
                                 server_api=ServerApi('1'))
            # Send a ping to confirm a successful connection
            try:
                client.admin.command('ping')
                print("Pinged your deployment. You successfully connected to MongoDB!")
                praw_integration(client)
            except Exception as e:
                print(e)

            return True
        except ConnectionFailure:
            print(
                f"Failed to connect to MongoDB, attempt {retries + 1}/{MAX_RETRIES}. Retrying in {RETRY_DELAY} seconds...")
            retries += 1
            time.sleep(RETRY_DELAY)
    print("Failed to connect to MongoDB after multiple attempts.")
    exit()


pending_submissions = connect_to_mongo()
