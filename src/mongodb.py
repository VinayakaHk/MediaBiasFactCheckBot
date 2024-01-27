from pymongo.errors import ConnectionFailure, PyMongoError
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

import os
import sys
import linecache
import time
import praw
import certifi
import ssl
load_dotenv()


MAX_RETRIES = 10
RETRY_DELAY = 10


def store_submission_in_mongo(mongo_db, submission):

    submissions_collection = mongo_db['submissions']
    submissions_collection.insert_one({
        'author': str(submission.author.name),
        'created': str(submission.created),
        'distinguished': str(submission.distinguished),
        'domain': str(submission.domain),
        'submission_id': str(submission.id),
        'is_reddit_media_domain': str(submission.is_reddit_media_domain),
        'is_self': str(submission.is_self),
        'is_video': str(submission.is_video),
        'locked': str(submission.locked),
        'name': str(submission.name),
        'permalink': str(submission.permalink),
        'selftext': str(submission.selftext),
        'spoiler': str(submission.spoiler),
        'stickied': str(submission.stickied),
        'subreddit': str(submission.subreddit),
        'subreddit_id': str(submission.subreddit_id),
        'subreddit_name_prefixed': str(submission.subreddit_name_prefixed),
        'subreddit_subscribers': str(submission.subreddit_subscribers),
        'title': str(submission.title),
        'url': str(submission.url),
    })


def store_comment_in_mongo(mongo_db, comment):
    comments_collection = mongo_db['comments']
    comments_collection.insert_one({
        'author': str(comment.author.name),
        'author_is_blocked': str(comment.author_is_blocked),
        'banned_at_utc': str(comment.banned_at_utc),
        'banned_by': str(comment.banned_by),
        'body': str(comment.body),
        'controversiality': str(comment.controversiality),
        'created_utc': str(comment.created_utc),
        'distinguished': str(comment.distinguished),
        'comment_id': str(comment.id),
        'is_submitter': str(comment.is_submitter),
        'link_author': str(comment.link_author),
        'link_id': str(comment.link_id),
        'link_permalink': str(comment.link_permalink),
        'link_title': str(comment.link_title),
        'link_url': str(comment.link_url),
        'name': str(comment.name),
        'num_comments': str(comment.num_comments),
        'parent_id': str(comment.parent_id),
        'permalink': str(comment.permalink),
        'stickied': str(comment.stickied),
        'subreddit': str(comment.subreddit),
        'subreddit_id': str(comment.subreddit_id),
        'subreddit_name_prefixed': str(comment.subreddit_name_prefixed),
    })


def connect_to_mongo():
    retries = 0
    while retries < MAX_RETRIES:
        try:
            # Create a new client and connect to the server
            client = MongoClient(os.environ.get("MONGODB"))
            db = client.reddit
            # Send a ping to confirm a successful connection
            try:
                client.admin.command('ping')
                print("Pinged your deployment. You successfully connected to MongoDB!")
            except Exception as e:
                print(e)

            return db
        except Exception as e:
            print(e)
            print(
                f"Failed to connect to MongoDB, attempt {retries + 1}/{MAX_RETRIES}. Retrying in {RETRY_DELAY} seconds...")
            retries += 1
            time.sleep(RETRY_DELAY)
    print("Failed to connect to MongoDB after multiple attempts.")
    exit()
